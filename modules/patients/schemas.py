"""Pydantic schemas for patients."""

from datetime import datetime, date
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, EmailStr


# ========================
# Request Schemas
# ========================

class PatientCreateRequest(BaseModel):
    """Create patient request."""
    
    first_name: str = Field(..., min_length=1, max_length=255)
    last_name: str = Field(..., min_length=1, max_length=255)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    medical_history: Optional[Dict[str, Any]] = Field(default_factory=dict)
    allergies: Optional[List[str]] = Field(default_factory=list)
    medications: Optional[List[str]] = Field(default_factory=list)
    emergency_contact: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PatientUpdateRequest(BaseModel):
    """Update patient request."""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, min_length=1, max_length=255)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    medical_history: Optional[Dict[str, Any]] = None
    allergies: Optional[List[str]] = None
    medications: Optional[List[str]] = None
    emergency_contact: Optional[Dict[str, Any]] = None


# ========================
# Response Schemas
# ========================

class PatientResponse(BaseModel):
    """Patient response."""
    
    id: str
    user_id: str
    first_name: str
    last_name: str
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    medical_history: Optional[Dict[str, Any]] = None
    allergies: Optional[List[str]] = None
    medications: Optional[List[str]] = None
    emergency_contact: Optional[Dict[str, Any]] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PatientListResponse(BaseModel):
    """Patient list response."""
    
    success: bool = True
    data: List[PatientResponse]
    pagination: Optional[Dict[str, Any]] = None


class PatientDetailResponse(BaseModel):
    """Single patient response."""
    
    success: bool = True
    data: PatientResponse

