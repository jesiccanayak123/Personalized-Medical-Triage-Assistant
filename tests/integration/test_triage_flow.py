"""
Integration tests for triage workflow including emergency interrupt.
"""
import pytest
from httpx import AsyncClient

from database.models import Patient, TriageThread


class TestTriageFlow:
    """Integration tests for triage endpoints and flow."""

    @pytest.mark.asyncio
    async def test_create_triage_thread(self, authenticated_client: AsyncClient, test_patient: Patient):
        """Test creating a triage thread."""
        response = await authenticated_client.post(
            "/api/v1/triage/threads",
            json={
                "patient_id": test_patient.id,
                "chief_complaint": "Headache for 2 days",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["patient_id"] == test_patient.id
        assert data["data"]["status"] == "INTERVIEWING"

    @pytest.mark.asyncio
    async def test_create_thread_without_complaint(self, authenticated_client: AsyncClient, test_patient: Patient):
        """Test creating thread without chief complaint."""
        response = await authenticated_client.post(
            "/api/v1/triage/threads",
            json={
                "patient_id": test_patient.id,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["chief_complaint"] is None

    @pytest.mark.asyncio
    async def test_get_thread(self, authenticated_client: AsyncClient, test_thread: TriageThread):
        """Test getting a triage thread."""
        response = await authenticated_client.get(f"/api/v1/triage/threads/{test_thread.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == test_thread.id

    @pytest.mark.asyncio
    async def test_list_threads_by_patient(self, authenticated_client: AsyncClient, test_thread: TriageThread, test_patient: Patient):
        """Test listing threads for a patient."""
        response = await authenticated_client.get(
            "/api/v1/triage/threads",
            params={"patient_id": test_patient.id},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 1

    @pytest.mark.asyncio
    async def test_send_message(self, authenticated_client: AsyncClient, test_thread: TriageThread):
        """Test sending a message to triage thread."""
        response = await authenticated_client.post(
            f"/api/v1/triage/threads/{test_thread.id}/messages",
            json={
                "content": "I have a mild headache that started yesterday",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Response should include UI response with next question
        assert "message" in data["data"]

    @pytest.mark.asyncio
    async def test_get_messages(self, authenticated_client: AsyncClient, test_thread: TriageThread):
        """Test getting messages for a thread."""
        # First send a message
        await authenticated_client.post(
            f"/api/v1/triage/threads/{test_thread.id}/messages",
            json={"content": "Test message"},
        )
        
        # Get messages
        response = await authenticated_client.get(
            f"/api/v1/triage/threads/{test_thread.id}/messages"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["data"], list)

    @pytest.mark.asyncio
    async def test_emergency_interrupt(self, authenticated_client: AsyncClient, test_patient: Patient):
        """Test that emergency symptoms trigger immediate interrupt."""
        # Create a new thread
        create_response = await authenticated_client.post(
            "/api/v1/triage/threads",
            json={
                "patient_id": test_patient.id,
                "chief_complaint": "Mild discomfort",
            },
        )
        thread_id = create_response.json()["data"]["id"]
        
        # Send message with emergency symptoms
        response = await authenticated_client.post(
            f"/api/v1/triage/threads/{thread_id}/messages",
            json={
                "content": "I'm having severe crushing chest pain that radiates to my left arm and I can't breathe",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should detect emergency
        assert data["data"]["is_emergency"] is True
        assert "EMERGENCY" in data["data"]["message"].upper() or data["data"]["status"] == "EMERGENCY"

    @pytest.mark.asyncio
    async def test_get_artifacts(self, authenticated_client: AsyncClient, test_thread: TriageThread, db_session):
        """Test getting artifacts for a completed thread."""
        from database.dao.artifacts import PostgresArtifactsDao
        
        # Add some artifacts
        dao = PostgresArtifactsDao()
        await dao.save_artifact(
            db_session,
            test_thread.id,
            "risk_assessment",
            {"disposition": "ROUTINE", "is_emergency": False},
        )
        
        response = await authenticated_client.get(
            f"/api/v1/triage/threads/{test_thread.id}/artifacts"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "risk_assessment" in data["data"]

    @pytest.mark.asyncio
    async def test_thread_user_scoping(self, client: AsyncClient, test_thread: TriageThread, db_session):
        """Test that threads are scoped to their users."""
        from modules.auth.utils import hash_password, generate_id
        from database.models import User
        from database.dao.user_tokens import PostgresUserTokensDao
        
        # Create another user
        other_user = User(
            id=generate_id(),
            email="other2@example.com",
            password_hash=hash_password("password123"),
            name="Other User 2",
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.commit()
        
        # Get token for other user
        dao = PostgresUserTokensDao()
        token = await dao.create_token(db_session, other_user.id)
        
        # Try to access first user's thread
        client.headers["Authorization"] = f"Bearer {token}"
        response = await client.get(f"/api/v1/triage/threads/{test_thread.id}")
        
        # Should not find it
        assert response.status_code == 404


class TestTriageWorkflowStates:
    """Tests for triage workflow state transitions."""

    @pytest.mark.asyncio
    async def test_normal_flow_completion(self, authenticated_client: AsyncClient, test_patient: Patient):
        """Test normal interview completion flow."""
        # This is a longer test that simulates a full interview
        # In practice, you'd mock the LLM responses
        
        # Create thread
        response = await authenticated_client.post(
            "/api/v1/triage/threads",
            json={
                "patient_id": test_patient.id,
                "chief_complaint": "Mild headache",
            },
        )
        thread_id = response.json()["data"]["id"]
        
        # Simulate answering questions
        # (In real tests, you'd mock the agent responses)
        messages = [
            "I have a mild headache",
            "It started about 2 hours ago",
            "The pain is about 3 out of 10",
            "No, I don't have any other symptoms",
            "No allergies or medications",
        ]
        
        for msg in messages:
            response = await authenticated_client.post(
                f"/api/v1/triage/threads/{thread_id}/messages",
                json={"content": msg},
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_status_transitions(self, authenticated_client: AsyncClient, test_thread: TriageThread, db_session):
        """Test thread status transitions."""
        from database.dao.triage_threads import PostgresTriageThreadsDao
        
        dao = PostgresTriageThreadsDao()
        
        # Verify initial status
        thread = await dao.get_thread(db_session, test_thread.id)
        assert thread.status == "INTERVIEWING"
        
        # Update to CODING
        await dao.update_status(db_session, test_thread.id, "CODING")
        thread = await dao.get_thread(db_session, test_thread.id)
        assert thread.status == "CODING"
        
        # Update to SCRIBING
        await dao.update_status(db_session, test_thread.id, "SCRIBING")
        thread = await dao.get_thread(db_session, test_thread.id)
        assert thread.status == "SCRIBING"
        
        # Update to DONE
        await dao.update_status(db_session, test_thread.id, "DONE")
        thread = await dao.get_thread(db_session, test_thread.id)
        assert thread.status == "DONE"

