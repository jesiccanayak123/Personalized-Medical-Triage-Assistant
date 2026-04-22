"""Patients API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from modules.patients.schemas import (
    PatientCreateRequest,
    PatientUpdateRequest,
    PatientListResponse,
    PatientDetailResponse,
)
from modules.patients.service import PatientsService
from database.dao.patients import PatientsDao
from app.dependencies import get_patients_dao, get_current_user
from global_utils.exceptions import AppException


router = APIRouter(prefix="/patients", tags=["Patients"])


def get_patients_service(
    patients_dao: PatientsDao = Depends(get_patients_dao),
) -> PatientsService:
    """Get PatientsService instance."""
    return PatientsService(patients_dao=patients_dao)


@router.post("", response_model=PatientDetailResponse, status_code=201)
async def create_patient(
    payload: PatientCreateRequest,
    current_user: dict = Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    """Create a new patient.
    
    Creates a patient record associated with the current user.
    """
    try:
        return await service.create_patient(
            user_id=current_user["id"],
            patient_data=payload.model_dump(exclude_unset=True),
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("", response_model=PatientListResponse)
async def list_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    """List patients for the current user.
    
    Returns a paginated list of patients.
    """
    try:
        return await service.list_patients(
            user_id=current_user["id"],
            skip=skip,
            limit=limit,
            search=search,
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{patient_id}", response_model=PatientDetailResponse)
async def get_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    """Get a patient by ID.
    
    Returns the patient details if owned by the current user.
    """
    try:
        return await service.get_patient(
            patient_id=patient_id,
            user_id=current_user["id"],
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/{patient_id}", response_model=PatientDetailResponse)
async def update_patient(
    patient_id: str,
    payload: PatientUpdateRequest,
    current_user: dict = Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    """Update a patient.
    
    Updates the patient record if owned by the current user.
    """
    try:
        return await service.update_patient(
            patient_id=patient_id,
            user_id=current_user["id"],
            update_data=payload.model_dump(exclude_unset=True),
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    service: PatientsService = Depends(get_patients_service),
):
    """Delete a patient (soft delete).
    
    Marks the patient as inactive if owned by the current user.
    """
    try:
        return await service.delete_patient(
            patient_id=patient_id,
            user_id=current_user["id"],
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

