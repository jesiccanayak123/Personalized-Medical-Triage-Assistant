"""LangGraph state definition for triage workflow."""

from typing import TypedDict, Optional, List, Dict, Any, Annotated
from enum import Enum

from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage

from modules.triage.schemas import (
    TriageStatus,
    InterviewerOutput,
    RiskAssessmentOutput,
    ICD10CodingOutput,
    SOAPNoteOutput,
)


class TriageState(TypedDict):
    """State for the triage LangGraph workflow.
    
    This is the short-term memory that persists across turns.
    """
    
    # Thread identifiers
    thread_id: str
    user_id: str
    patient_id: str
    
    # Messages (using LangGraph's message reducer)
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Structured interview data
    intake_data: Dict[str, Any]
    
    # Current workflow status
    status: str  # TriageStatus value
    
    # Agent outputs (validated Pydantic models)
    interviewer_output: Optional[InterviewerOutput]
    risk_output: Optional[RiskAssessmentOutput]
    icd10_output: Optional[ICD10CodingOutput]
    soap_output: Optional[SOAPNoteOutput]
    
    # Progress tracking
    missing_fields: List[str]
    completion_reason: Optional[str]
    
    # Control flags
    should_interrupt: bool  # Emergency interrupt flag


def create_initial_state(
    thread_id: str,
    user_id: str,
    patient_id: str,
    intake_data: Optional[Dict[str, Any]] = None,
) -> TriageState:
    """Create initial state for a new triage session.
    
    Args:
        thread_id: Thread ID
        user_id: User ID
        patient_id: Patient ID
        intake_data: Optional existing intake data
        
    Returns:
        Initial TriageState
    """
    return TriageState(
        thread_id=thread_id,
        user_id=user_id,
        patient_id=patient_id,
        messages=[],
        intake_data=intake_data or {},
        status=TriageStatus.INTERVIEWING.value,
        interviewer_output=None,
        risk_output=None,
        icd10_output=None,
        soap_output=None,
        missing_fields=[
            "symptoms",
            "duration",
            "severity",
            "location",
            "associated_symptoms",
        ],
        completion_reason=None,
        should_interrupt=False,
    )

