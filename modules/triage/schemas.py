"""Pydantic schemas for triage - MUST be validated for all agent outputs."""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from enum import Enum

from pydantic import BaseModel, Field


# ========================
# Enums
# ========================

class TriageStatus(str, Enum):
    """Triage thread status."""
    INTERVIEWING = "INTERVIEWING"
    EMERGENCY = "EMERGENCY"
    CODING = "CODING"
    SCRIBING = "SCRIBING"
    DONE = "DONE"


class DispositionLevel(str, Enum):
    """Risk disposition levels."""
    EMERGENT = "EMERGENT"
    URGENT = "URGENT"
    LESS_URGENT = "LESS_URGENT"
    NON_URGENT = "NON_URGENT"


# ========================
# Agent Output Schemas (MUST be validated)
# ========================

class InterviewerOutput(BaseModel):
    """Interviewer agent structured output."""
    
    assistant_message: str = Field(
        ..., description="The message to display to the patient"
    )
    captured_updates: Dict[str, Any] = Field(
        default_factory=dict,
        description="Updates to intake data captured from this exchange"
    )
    missing_fields: List[str] = Field(
        default_factory=list,
        description="Fields still needed to complete the interview"
    )
    is_done: bool = Field(
        default=False,
        description="Whether the interview is complete"
    )
    done_reason: Optional[str] = Field(
        None,
        description="Reason interview is complete (if is_done=True)"
    )


class RedFlag(BaseModel):
    """Red flag indicator for risk assessment."""
    
    rule_id: str = Field(..., description="Unique identifier for the rule")
    label: str = Field(..., description="Human-readable label")
    matched_text: str = Field(..., description="Text that triggered this flag")
    severity: str = Field(..., description="Severity level: CRITICAL, HIGH, MEDIUM")


class RiskAssessmentOutput(BaseModel):
    """Risk Assessor agent structured output."""
    
    emergency: bool = Field(
        default=False,
        description="Whether this is an emergency requiring immediate action"
    )
    red_flags: List[RedFlag] = Field(
        default_factory=list,
        description="List of detected red flags"
    )
    disposition: DispositionLevel = Field(
        default=DispositionLevel.NON_URGENT,
        description="Recommended disposition level"
    )
    ui_interrupt: bool = Field(
        default=False,
        description="Whether to interrupt the UI immediately"
    )
    recommended_action_template_id: Optional[str] = Field(
        None,
        description="ID of recommended action template"
    )


class ICD10Code(BaseModel):
    """Single ICD-10 code with evidence."""
    
    icd10: str = Field(..., description="ICD-10 code (e.g., 'J06.9')")
    description: str = Field(..., description="Code description")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score 0-1")
    evidence_snippets: List[str] = Field(
        default_factory=list,
        description="Text snippets supporting this code"
    )
    source_ids: List[str] = Field(
        default_factory=list,
        description="IDs of source documents used"
    )


class ICD10CodingOutput(BaseModel):
    """Medical Coder agent structured output."""
    
    codes: List[ICD10Code] = Field(
        default_factory=list,
        description="List of ICD-10 codes with evidence"
    )


class SOAPSection(BaseModel):
    """Generic SOAP section data."""
    content: Dict[str, Any] = Field(default_factory=dict)


class SOAPNoteOutput(BaseModel):
    """Scribe agent structured SOAP note output."""
    
    subjective: Dict[str, Any] = Field(
        default_factory=dict,
        description="Subjective section: chief complaint, HPI, ROS"
    )
    objective: Dict[str, Any] = Field(
        default_factory=dict,
        description="Objective section: vitals, physical exam findings"
    )
    assessment: Dict[str, Any] = Field(
        default_factory=dict,
        description="Assessment: diagnoses, ICD-10 codes, differential"
    )
    plan: Dict[str, Any] = Field(
        default_factory=dict,
        description="Plan: treatment, medications, follow-up"
    )
    ehr_format_version: str = Field(
        default="1.0",
        description="EHR format version for compatibility"
    )


# ========================
# UI Response Schema
# ========================

class EmergencyBanner(BaseModel):
    """Emergency banner for UI display."""
    
    title: str = Field(default="Emergency Detected")
    message: str = Field(..., description="Emergency message")
    severity: str = Field(default="CRITICAL")
    actions: List[str] = Field(default_factory=list)


class UIResponse(BaseModel):
    """Unified response returned from chat endpoint to UI."""
    
    assistant_message: str = Field(
        ..., description="Message to display to user"
    )
    status: TriageStatus = Field(
        ..., description="Current triage status"
    )
    progress_missing_fields: List[str] = Field(
        default_factory=list,
        description="Fields still needed"
    )
    emergency_banner: Optional[EmergencyBanner] = Field(
        None, description="Emergency banner if status=EMERGENCY"
    )
    artifacts: Optional[Dict[str, Any]] = Field(
        None, description="Available artifacts (ICD-10, SOAP, risk)"
    )


# ========================
# Request Schemas
# ========================

class ThreadCreateRequest(BaseModel):
    """Create triage thread request."""
    
    patient_id: str = Field(..., description="Patient ID")
    chief_complaint: Optional[str] = Field(
        None, description="Initial chief complaint"
    )


class MessageRequest(BaseModel):
    """Send message to triage thread."""
    
    content: str = Field(..., min_length=1, description="Message content")


# ========================
# Response Schemas
# ========================

class ThreadResponse(BaseModel):
    """Triage thread response."""
    
    id: str
    user_id: str
    patient_id: str
    status: str
    chief_complaint: Optional[str] = None
    intake_data: Optional[Dict[str, Any]] = None
    missing_fields: Optional[List[str]] = None
    completion_reason: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ThreadListResponse(BaseModel):
    """Thread list response."""
    
    success: bool = True
    data: List[ThreadResponse]
    pagination: Optional[Dict[str, Any]] = None


class ThreadDetailResponse(BaseModel):
    """Single thread response."""
    
    success: bool = True
    data: ThreadResponse


class MessageResponse(BaseModel):
    """Message response."""
    
    id: str
    thread_id: str
    role: str
    content: str
    agent_name: Optional[str] = None
    created_at: Optional[datetime] = None


class ChatResponse(BaseModel):
    """Chat endpoint response wrapping UIResponse."""
    
    success: bool = True
    data: UIResponse


class ArtifactsResponse(BaseModel):
    """Artifacts response."""
    
    success: bool = True
    data: Dict[str, Any]

