"""Pydantic schemas for dashboard."""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class DashboardStats(BaseModel):
    """Dashboard statistics."""
    
    total_patients: int = Field(default=0)
    active_threads: int = Field(default=0)
    emergencies_today: int = Field(default=0)
    completed_today: int = Field(default=0)
    completed_this_week: int = Field(default=0)


class PatientSummary(BaseModel):
    """Patient summary for dashboard list."""
    
    id: str
    first_name: str
    last_name: str
    last_triage_status: Optional[str] = None
    last_activity_at: Optional[datetime] = None
    active_threads_count: int = 0


class DashboardSummaryResponse(BaseModel):
    """Dashboard summary response."""
    
    success: bool = True
    data: DashboardStats


class DashboardPatientsResponse(BaseModel):
    """Dashboard patients list response."""
    
    success: bool = True
    data: List[PatientSummary]
    pagination: Optional[Dict[str, Any]] = None

