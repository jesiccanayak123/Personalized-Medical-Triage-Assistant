"""Dashboard API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query

from modules.dashboard.schemas import (
    DashboardSummaryResponse,
    DashboardPatientsResponse,
)
from modules.dashboard.service import DashboardService
from database.dao import PatientsDao, TriageThreadsDao
from app.dependencies import (
    get_patients_dao,
    get_triage_threads_dao,
    get_current_user,
)
from global_utils.exceptions import AppException


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_dashboard_service(
    patients_dao: PatientsDao = Depends(get_patients_dao),
    threads_dao: TriageThreadsDao = Depends(get_triage_threads_dao),
) -> DashboardService:
    """Get DashboardService instance."""
    return DashboardService(
        patients_dao=patients_dao,
        threads_dao=threads_dao,
    )


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_summary(
    current_user: dict = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
):
    """Get dashboard summary statistics.
    
    Returns counts for patients, active threads, emergencies, etc.
    """
    try:
        return await service.get_summary(user_id=current_user["id"])
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/patients", response_model=DashboardPatientsResponse)
async def get_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
):
    """Get patients list with last triage status.
    
    Returns patients with their most recent triage status and activity.
    """
    try:
        return await service.get_patients_with_status(
            user_id=current_user["id"],
            skip=skip,
            limit=limit,
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

