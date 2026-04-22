"""Interviewer agent node - patient-facing agent."""

import json
from typing import Dict, Any

from langchain_core.messages import HumanMessage, AIMessage

from agents.state import TriageState
from agents.prompts import INTERVIEWER_SYSTEM_PROMPT
from modules.triage.schemas import InterviewerOutput
from integrations.openai.client import OpenAIClient
from config.logging import logger


async def interviewer_node(state: TriageState) -> Dict[str, Any]:
    """Interviewer agent - conducts patient interview.
    
    This is the only agent that produces patient-visible output.
    Uses reflective listening and asks ONE question at a time.
    
    Args:
        state: Current triage state
        
    Returns:
        Updated state with interviewer_output
    """
    client = OpenAIClient()
    
    # Build conversation context
    conversation_text = ""
    for msg in state["messages"]:
        role = "Patient" if isinstance(msg, HumanMessage) else "Assistant"
        conversation_text += f"{role}: {msg.content}\n"
    
    # Format system prompt with current data
    system_prompt = INTERVIEWER_SYSTEM_PROMPT.format(
        intake_data=json.dumps(state["intake_data"], indent=2),
        missing_fields=", ".join(state["missing_fields"]),
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Conversation so far:\n{conversation_text}\n\nGenerate the next response and update captured data."},
    ]
    
    try:
        # Get structured output from OpenAI
        output = await client.structured_output(
            messages=messages,
            response_model=InterviewerOutput,
            temperature=0.7,
        )
        
        # Update missing fields based on captured data
        captured_fields = set(output.captured_updates.keys())
        remaining_missing = [f for f in state["missing_fields"] if f not in captured_fields]
        
        # Determine if interview is complete
        # Require at least: symptoms, duration, severity
        required_fields = {"symptoms", "duration", "severity"}
        captured_so_far = set(state["intake_data"].keys()) | captured_fields
        has_required = required_fields.issubset(captured_so_far)
        
        if has_required and not output.is_done:
            # Check if we should auto-complete
            if len(remaining_missing) <= 1:
                output.is_done = True
                output.done_reason = "Sufficient information collected"
                # Update message to be a closing statement, not a question
                output.assistant_message = (
                    "Thank you for providing all this information. I now have what I need to "
                    "complete your triage assessment. Please wait while we process this for "
                    "further assistance."
                )
        
        output.missing_fields = remaining_missing
        
        # Merge captured updates into intake_data for downstream agents
        updated_intake = dict(state["intake_data"])
        updated_intake.update(output.captured_updates)
        
        logger.info(
            "Interviewer completed",
            is_done=output.is_done,
            captured_fields=list(captured_fields),
            missing_fields=remaining_missing,
        )
        
        return {
            "interviewer_output": output,
            "intake_data": updated_intake,  # Update state with captured data
            "missing_fields": remaining_missing,
        }
        
    except Exception as e:
        logger.error(f"Interviewer error: {e}")
        
        # Return fallback response
        return {
            "interviewer_output": InterviewerOutput(
                assistant_message="I understand. Can you tell me more about your symptoms?",
                captured_updates={},
                missing_fields=state["missing_fields"],
                is_done=False,
            ),
            "missing_fields": state["missing_fields"],
        }

