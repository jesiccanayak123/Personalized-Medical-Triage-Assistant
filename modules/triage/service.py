"""Triage service - orchestrates the triage workflow."""

from datetime import datetime
from typing import Dict, Any, List, Optional

from database.dao.triage_threads import TriageThreadsDao
from database.dao.messages import MessagesDao
from database.dao.artifacts import ArtifactsDao
from database.dao.patients import PatientsDao
from global_utils.exceptions import NotFoundError, ValidationError
from modules.triage.schemas import (
    TriageStatus,
    UIResponse,
    EmergencyBanner,
    InterviewerOutput,
    RiskAssessmentOutput,
    ICD10CodingOutput,
    SOAPNoteOutput,
)
from agents.rules_engine import RulesEngine


class TriageService:
    """Service class for triage operations."""

    def __init__(
        self,
        threads_dao: TriageThreadsDao,
        messages_dao: MessagesDao,
        artifacts_dao: ArtifactsDao,
        patients_dao: PatientsDao,
        graph_runner=None,  # LangGraph runner injected
    ):
        """Initialize TriageService.
        
        Args:
            threads_dao: Triage threads DAO
            messages_dao: Messages DAO
            artifacts_dao: Artifacts DAO
            patients_dao: Patients DAO
            graph_runner: LangGraph runner for agent orchestration
        """
        self.threads_dao = threads_dao
        self.messages_dao = messages_dao
        self.artifacts_dao = artifacts_dao
        self.patients_dao = patients_dao
        self.graph_runner = graph_runner

    async def create_thread(
        self,
        user_id: str,
        patient_id: str,
        chief_complaint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new triage thread.
        
        Args:
            user_id: User's ID
            patient_id: Patient's ID
            chief_complaint: Optional initial complaint
            
        Returns:
            Created thread data
        """
        # Verify patient exists and belongs to user
        patient = await self.patients_dao.get_patient_by_id(patient_id, user_id)
        if not patient:
            raise NotFoundError("Patient not found")

        # Create thread
        thread_data = {
            "user_id": user_id,
            "patient_id": patient_id,
            "chief_complaint": chief_complaint,
            "status": TriageStatus.INTERVIEWING.value,
            "intake_data": {},
            "missing_fields": [
                "symptoms",
                "duration",
                "severity",
                "location",
                "associated_symptoms",
            ],
        }

        thread_id = await self.threads_dao.create_thread(thread_data)
        thread = await self.threads_dao.get_thread_by_id(thread_id, user_id)

        # Create initial assistant message if chief complaint provided
        if chief_complaint:
            initial_message = (
                f"I understand you're experiencing: {chief_complaint}. "
                "Let me ask you a few questions to better understand your symptoms. "
                "Can you describe when these symptoms started?"
            )
            await self.messages_dao.create_message({
                "thread_id": thread_id,
                "role": "assistant",
                "content": initial_message,
                "agent_name": "interviewer",
            })

        return {
            "success": True,
            "data": thread
        }

    async def get_thread(
        self,
        thread_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get a triage thread.
        
        Args:
            thread_id: Thread's ID
            user_id: User's ID for scoping
            
        Returns:
            Thread data
        """
        thread = await self.threads_dao.get_thread_by_id(thread_id, user_id)
        if not thread:
            raise NotFoundError("Thread not found")

        return {
            "success": True,
            "data": thread
        }

    async def list_threads(
        self,
        user_id: str,
        patient_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """List triage threads.
        
        Args:
            user_id: User's ID
            patient_id: Optional patient filter
            status: Optional status filter
            skip: Number to skip
            limit: Maximum to return
            
        Returns:
            List of threads
        """
        if patient_id:
            threads = await self.threads_dao.get_threads_by_patient(
                patient_id=patient_id,
                user_id=user_id,
                skip=skip,
                limit=limit,
            )
        else:
            threads = await self.threads_dao.get_threads_by_user(
                user_id=user_id,
                status=status,
                skip=skip,
                limit=limit,
            )

        return {
            "success": True,
            "data": threads,
        }

    async def send_message(
        self,
        thread_id: str,
        user_id: str,
        content: str,
    ) -> Dict[str, Any]:
        """Send a message and run the LangGraph workflow.
        
        Args:
            thread_id: Thread's ID
            user_id: User's ID
            content: User's message content
            
        Returns:
            UIResponse with assistant message and status
        """
        # Get thread
        thread = await self.threads_dao.get_thread_by_id(thread_id, user_id)
        if not thread:
            raise NotFoundError("Thread not found")

        # Check if thread is already done
        if thread["status"] == TriageStatus.DONE.value:
            return {
                "success": True,
                "data": UIResponse(
                    assistant_message="This triage session has been completed.",
                    status=TriageStatus.DONE,
                    progress_missing_fields=[],
                ).model_dump()
            }

        # Save user message
        await self.messages_dao.create_message({
            "thread_id": thread_id,
            "role": "user",
            "content": content,
        })

        # Get conversation history
        messages = await self.messages_dao.get_messages_by_thread(thread_id)

        # Run LangGraph workflow if available
        if self.graph_runner:
            result = await self.graph_runner.run(
                thread_id=thread_id,
                user_id=user_id,
                messages=messages,
                intake_data=thread.get("intake_data", {}),
                user_message=content,
            )
            
            # Process result and update thread
            ui_response = await self._process_graph_result(
                thread_id=thread_id,
                user_id=user_id,
                result=result,
            )
        else:
            # Fallback when no graph runner (for testing)
            ui_response = await self._fallback_response(
                thread_id=thread_id,
                thread=thread,
                content=content,
            )

        return {
            "success": True,
            "data": ui_response.model_dump()
        }

    async def _process_graph_result(
        self,
        thread_id: str,
        user_id: str,
        result: Dict[str, Any],
    ) -> UIResponse:
        """Process LangGraph result and update thread state.
        
        Args:
            thread_id: Thread ID
            user_id: User ID
            result: Graph result dict
            
        Returns:
            UIResponse for the UI
        """
        # Extract outputs from result
        interviewer_output = result.get("interviewer_output")
        risk_output = result.get("risk_output")
        icd10_output = result.get("icd10_output")
        soap_output = result.get("soap_output")
        new_status = result.get("status", TriageStatus.INTERVIEWING.value)

        # Check for emergency
        emergency_banner = None
        if risk_output and risk_output.emergency:
            new_status = TriageStatus.EMERGENCY.value
            emergency_banner = EmergencyBanner(
                message="Emergency symptoms detected. Please seek immediate medical attention.",
                severity="CRITICAL",
                actions=["Call 911", "Go to nearest ER"],
            )

        # Update thread status and data
        update_data = {"status": new_status}
        
        # Set completed_at when thread is completed
        if new_status in [TriageStatus.DONE.value, TriageStatus.EMERGENCY.value]:
            from datetime import datetime
            update_data["completed_at"] = datetime.utcnow()
        
        if interviewer_output:
            # Merge captured updates into intake data
            intake_data = result.get("intake_data", {})
            intake_data.update(interviewer_output.captured_updates)
            update_data["intake_data"] = intake_data
            update_data["missing_fields"] = interviewer_output.missing_fields
            
            if interviewer_output.is_done:
                update_data["completion_reason"] = interviewer_output.done_reason

        await self.threads_dao.update_thread(thread_id, update_data, user_id)

        # Save assistant message
        assistant_message = (
            interviewer_output.assistant_message 
            if interviewer_output 
            else "Thank you for your response."
        )
        await self.messages_dao.create_message({
            "thread_id": thread_id,
            "role": "assistant",
            "content": assistant_message,
            "agent_name": "interviewer",
        })

        # Save artifacts if available
        artifacts = {}
        
        if risk_output:
            await self.artifacts_dao.upsert_artifact(
                thread_id=thread_id,
                artifact_type="risk_assessment",
                data=risk_output.model_dump(),
            )
            artifacts["risk_assessment"] = risk_output.model_dump()

        if icd10_output:
            await self.artifacts_dao.upsert_artifact(
                thread_id=thread_id,
                artifact_type="icd10_coding",
                data=icd10_output.model_dump(),
            )
            artifacts["icd10_coding"] = icd10_output.model_dump()

        if soap_output:
            await self.artifacts_dao.upsert_artifact(
                thread_id=thread_id,
                artifact_type="soap_note",
                data=soap_output.model_dump(),
            )
            artifacts["soap_note"] = soap_output.model_dump()

        return UIResponse(
            assistant_message=assistant_message,
            status=TriageStatus(new_status),
            progress_missing_fields=interviewer_output.missing_fields if interviewer_output else [],
            emergency_banner=emergency_banner,
            artifacts=artifacts if artifacts else None,
        )

    async def _fallback_response(
        self,
        thread_id: str,
        thread: Dict[str, Any],
        content: str,
    ) -> UIResponse:
        """Generate fallback response when graph runner not available.
        
        Used for testing or when LangGraph is not configured.
        Includes rules engine for emergency detection.
        """
        # Run rules engine to check for emergencies
        rules_engine = RulesEngine()
        risk_result = rules_engine.analyze_message(content)
        
        emergency_banner = None
        new_status = thread["status"]
        
        if risk_result.get("is_emergency"):
            new_status = TriageStatus.EMERGENCY.value
            emergency_banner = EmergencyBanner(
                message="🚨 EMERGENCY: Critical symptoms detected. Please call 911 or go to the nearest emergency room immediately.",
                severity="CRITICAL",
                actions=["Call 911 immediately", "Go to nearest emergency room", "Do not drive yourself"],
            )
            
            # Update thread status with completed_at timestamp
            from datetime import datetime
            await self.threads_dao.update_thread(
                thread_id, 
                {"status": new_status, "completed_at": datetime.utcnow()}, 
                thread["user_id"]
            )
            
            # Save risk artifact
            await self.artifacts_dao.upsert_artifact(
                thread_id=thread_id,
                artifact_type="risk_assessment",
                data={
                    "is_emergency": True,
                    "disposition": "EMERGENCY",
                    "confidence": risk_result.get("confidence", 0.95),
                    "red_flags": risk_result.get("red_flags", []),
                    "detected_symptoms": risk_result.get("detected_symptoms", []),
                    "reasoning": "Emergency symptoms detected by rules engine",
                },
            )
            
            assistant_message = (
                "⚠️ I'm detecting symptoms that require immediate medical attention. "
                "Please call 911 or go to the nearest emergency room immediately. "
                "Do not wait - these symptoms could indicate a serious medical emergency."
            )
        else:
            # Normal response
            assistant_message = (
                "Thank you for that information. "
                "Can you tell me more about your symptoms?"
            )
        
        await self.messages_dao.create_message({
            "thread_id": thread_id,
            "role": "assistant",
            "content": assistant_message,
            "agent_name": "interviewer",
        })

        return UIResponse(
            assistant_message=assistant_message,
            status=TriageStatus(new_status),
            progress_missing_fields=thread.get("missing_fields", []),
            emergency_banner=emergency_banner,
        )

    async def get_artifacts(
        self,
        thread_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get all artifacts for a thread.
        
        Args:
            thread_id: Thread's ID
            user_id: User's ID for scoping
            
        Returns:
            Dict of artifacts by type
        """
        # Verify access
        thread = await self.threads_dao.get_thread_by_id(thread_id, user_id)
        if not thread:
            raise NotFoundError("Thread not found")

        # Get all artifacts
        artifacts = await self.artifacts_dao.get_artifacts_by_thread(thread_id)

        # Organize by type
        result = {}
        for artifact in artifacts:
            artifact_type = artifact["artifact_type"]
            result[artifact_type] = artifact["data"]

        return {
            "success": True,
            "data": result
        }

    async def get_messages(
        self,
        thread_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get all messages for a thread.
        
        Args:
            thread_id: Thread's ID
            user_id: User's ID for scoping
            
        Returns:
            List of messages
        """
        # Verify access
        thread = await self.threads_dao.get_thread_by_id(thread_id, user_id)
        if not thread:
            raise NotFoundError("Thread not found")

        messages = await self.messages_dao.get_messages_by_thread(thread_id)

        return {
            "success": True,
            "data": messages
        }

