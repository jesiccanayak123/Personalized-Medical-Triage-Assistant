"""Risk Assessor agent node - runs in parallel to detect emergencies."""

import json
from typing import Dict, Any

from langchain_core.messages import HumanMessage

from agents.state import TriageState
from agents.prompts import RISK_ASSESSOR_SYSTEM_PROMPT
from agents.rules_engine import rules_engine
from modules.triage.schemas import RiskAssessmentOutput, TriageStatus
from integrations.openai.client import OpenAIClient
from config.logging import logger


async def risk_assessor_node(state: TriageState) -> Dict[str, Any]:
    """Risk Assessor agent - detects emergency conditions.
    
    Runs BOTH:
    1. Deterministic rules engine (fast, reliable)
    2. LLM-based assessment (for nuanced cases)
    
    Args:
        state: Current triage state
        
    Returns:
        Updated state with risk_output and potential status change
    """
    # Build text from conversation
    conversation_text = ""
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            conversation_text += f"{msg.content}\n"
    
    # 1. Run deterministic rules engine FIRST
    rules_result = rules_engine.evaluate(conversation_text)
    
    # If rules engine detects CRITICAL emergency, use that immediately
    if rules_result.emergency:
        logger.warning(
            "Emergency detected by rules engine",
            red_flags=[rf.model_dump() for rf in rules_result.red_flags],
        )
        
        return {
            "risk_output": rules_result,
            "status": TriageStatus.EMERGENCY.value,
            "should_interrupt": True,
        }
    
    # 2. For non-emergency cases, optionally use LLM for more nuanced assessment
    # (Skip LLM if rules engine found nothing and conversation is short)
    if len(conversation_text) < 100 and not rules_result.red_flags:
        return {
            "risk_output": rules_result,
            "should_interrupt": False,
        }
    
    # Run LLM-based assessment
    try:
        client = OpenAIClient()
        
        system_prompt = RISK_ASSESSOR_SYSTEM_PROMPT.format(
            symptoms_text=conversation_text,
            intake_data=json.dumps(state["intake_data"], indent=2),
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Assess the risk level and identify any red flags."},
        ]
        
        llm_result = await client.structured_output(
            messages=messages,
            response_model=RiskAssessmentOutput,
            temperature=0.2,  # Low temperature for consistent risk assessment
        )
        
        # Merge rules and LLM results (rules take precedence for emergencies)
        if llm_result.emergency and not rules_result.emergency:
            logger.warning(
                "Emergency detected by LLM (not by rules)",
                llm_flags=[rf.model_dump() for rf in llm_result.red_flags],
            )
        
        # Combine red flags
        all_flags = rules_result.red_flags + [
            rf for rf in llm_result.red_flags 
            if rf.rule_id not in {rf.rule_id for rf in rules_result.red_flags}
        ]
        
        # Use the more severe assessment
        final_emergency = rules_result.emergency or llm_result.emergency
        final_disposition = (
            rules_result.disposition 
            if rules_result.emergency 
            else llm_result.disposition
        )
        
        final_result = RiskAssessmentOutput(
            emergency=final_emergency,
            red_flags=all_flags,
            disposition=final_disposition,
            ui_interrupt=final_emergency,
            recommended_action_template_id=(
                rules_result.recommended_action_template_id 
                or llm_result.recommended_action_template_id
            ),
        )
        
        new_status = (
            TriageStatus.EMERGENCY.value 
            if final_emergency 
            else state["status"]
        )
        
        return {
            "risk_output": final_result,
            "status": new_status,
            "should_interrupt": final_emergency,
        }
        
    except Exception as e:
        logger.error(f"Risk Assessor LLM error: {e}")
        
        # Fall back to rules-only result
        return {
            "risk_output": rules_result,
            "should_interrupt": rules_result.emergency,
        }

