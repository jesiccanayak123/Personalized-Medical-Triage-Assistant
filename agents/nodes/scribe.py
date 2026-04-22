"""Scribe agent node - generates SOAP notes."""

import json
from typing import Dict, Any

from agents.state import TriageState
from agents.prompts import SCRIBE_SYSTEM_PROMPT
from modules.triage.schemas import SOAPNoteOutput, TriageStatus
from integrations.openai.client import OpenAIClient
from config.logging import logger


async def scribe_node(state: TriageState) -> Dict[str, Any]:
    """Scribe agent - generates structured SOAP notes for EHR.
    
    Runs after Medical Coder completes.
    
    Args:
        state: Current triage state
        
    Returns:
        Updated state with soap_output and DONE status
    """
    client = OpenAIClient()
    
    # Format ICD-10 codes
    icd10_codes = "None assigned"
    if state.get("icd10_output") and state["icd10_output"].codes:
        codes = state["icd10_output"].codes
        icd10_codes = "\n".join([
            f"- {c.icd10}: {c.description} (confidence: {c.confidence:.2f})"
            for c in codes
        ])
    
    # Format risk assessment
    risk_assessment = "No significant risk factors"
    if state.get("risk_output"):
        risk = state["risk_output"]
        if risk.red_flags:
            flags = ", ".join([f.label for f in risk.red_flags])
            risk_assessment = f"Red flags: {flags}. Disposition: {risk.disposition.value}"
        else:
            risk_assessment = f"Disposition: {risk.disposition.value}"
    
    system_prompt = SCRIBE_SYSTEM_PROMPT.format(
        intake_data=json.dumps(state["intake_data"], indent=2),
        icd10_codes=icd10_codes,
        risk_assessment=risk_assessment,
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Generate the SOAP note."},
    ]
    
    try:
        output = await client.structured_output(
            messages=messages,
            response_model=SOAPNoteOutput,
            temperature=0.3,
        )
        
        logger.info("SOAP note generated")
        
        return {
            "soap_output": output,
            "status": TriageStatus.DONE.value,
            "completion_reason": "SOAP note completed",
        }
        
    except Exception as e:
        logger.error(f"Scribe error: {e}")
        
        # Generate basic SOAP note
        intake = state["intake_data"]
        
        return {
            "soap_output": SOAPNoteOutput(
                subjective={
                    "chief_complaint": intake.get("symptoms", "Not specified"),
                    "hpi": {
                        "duration": intake.get("duration", "Not specified"),
                        "severity": intake.get("severity", "Not specified"),
                        "location": intake.get("location", "Not specified"),
                    },
                },
                objective={
                    "vitals": "Not available",
                    "exam": "Telehealth encounter - no physical exam",
                },
                assessment={
                    "diagnosis": "Pending physician review",
                    "icd10_codes": [],
                },
                plan={
                    "treatment": "Pending physician review",
                    "follow_up": "As needed",
                },
                ehr_format_version="1.0",
            ),
            "status": TriageStatus.DONE.value,
            "completion_reason": "SOAP note completed (fallback)",
        }

