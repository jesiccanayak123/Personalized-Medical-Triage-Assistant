"""Triage API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from modules.triage.schemas import (
    ThreadCreateRequest,
    MessageRequest,
    ThreadListResponse,
    ThreadDetailResponse,
    ChatResponse,
    ArtifactsResponse,
)
from modules.triage.service import TriageService
from database.dao import (
    TriageThreadsDao,
    MessagesDao,
    ArtifactsDao,
    PatientsDao,
)
from app.dependencies import (
    get_triage_threads_dao,
    get_messages_dao,
    get_artifacts_dao,
    get_patients_dao,
    get_current_user,
)
from global_utils.exceptions import AppException
from agents.graph import get_triage_graph
from config.settings import settings


router = APIRouter(prefix="/triage", tags=["Triage"])


def get_triage_service(
    threads_dao: TriageThreadsDao = Depends(get_triage_threads_dao),
    messages_dao: MessagesDao = Depends(get_messages_dao),
    artifacts_dao: ArtifactsDao = Depends(get_artifacts_dao),
    patients_dao: PatientsDao = Depends(get_patients_dao),
) -> TriageService:
    """Get TriageService instance with LangGraph runner."""
    # Only enable LangGraph if OpenAI key is configured
    graph_runner = None
    if settings.openai_api_key and settings.openai_api_key != "":
        graph_runner = get_triage_graph()
    
    return TriageService(
        threads_dao=threads_dao,
        messages_dao=messages_dao,
        artifacts_dao=artifacts_dao,
        patients_dao=patients_dao,
        graph_runner=graph_runner,
    )


@router.post("/threads", response_model=ThreadDetailResponse, status_code=201)
async def create_thread(
    payload: ThreadCreateRequest,
    current_user: dict = Depends(get_current_user),
    service: TriageService = Depends(get_triage_service),
):
    """Create a new triage thread.
    
    Creates a triage session for a patient.
    """
    try:
        return await service.create_thread(
            user_id=current_user["id"],
            patient_id=payload.patient_id,
            chief_complaint=payload.chief_complaint,
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/threads", response_model=ThreadListResponse)
async def list_threads(
    patient_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    service: TriageService = Depends(get_triage_service),
):
    """List triage threads.
    
    Returns threads filtered by patient_id or status.
    """
    try:
        return await service.list_threads(
            user_id=current_user["id"],
            patient_id=patient_id,
            status=status,
            skip=skip,
            limit=limit,
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/threads/{thread_id}", response_model=ThreadDetailResponse)
async def get_thread(
    thread_id: str,
    current_user: dict = Depends(get_current_user),
    service: TriageService = Depends(get_triage_service),
):
    """Get a triage thread by ID."""
    try:
        return await service.get_thread(
            thread_id=thread_id,
            user_id=current_user["id"],
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/threads/{thread_id}/messages", response_model=ChatResponse)
async def send_message(
    thread_id: str,
    payload: MessageRequest,
    current_user: dict = Depends(get_current_user),
    service: TriageService = Depends(get_triage_service),
):
    """Send a message to a triage thread.
    
    Runs the LangGraph workflow and returns the UI response.
    """
    try:
        return await service.send_message(
            thread_id=thread_id,
            user_id=current_user["id"],
            content=payload.content,
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/threads/{thread_id}/artifacts", response_model=ArtifactsResponse)
async def get_artifacts(
    thread_id: str,
    current_user: dict = Depends(get_current_user),
    service: TriageService = Depends(get_triage_service),
):
    """Get all artifacts for a triage thread.
    
    Returns risk assessment, ICD-10 codes, and SOAP notes.
    """
    try:
        return await service.get_artifacts(
            thread_id=thread_id,
            user_id=current_user["id"],
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/threads/{thread_id}/messages")
async def get_messages(
    thread_id: str,
    current_user: dict = Depends(get_current_user),
    service: TriageService = Depends(get_triage_service),
):
    """Get all messages for a triage thread."""
    try:
        return await service.get_messages(
            thread_id=thread_id,
            user_id=current_user["id"],
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

