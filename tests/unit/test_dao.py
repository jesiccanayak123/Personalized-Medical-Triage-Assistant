"""
Unit tests for DAO layer, including pgvector operations.
"""
import pytest
import pytest_asyncio
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from database.dao.users import PostgresUsersDao
from database.dao.patients import PostgresPatientsDao
from database.dao.triage_threads import PostgresTriageThreadsDao
from database.dao.messages import PostgresMessagesDao
from database.dao.artifacts import PostgresArtifactsDao
from database.dao.rag_documents import PostgresRAGDocumentsDao
from database.models import User, Patient, TriageThread
from modules.auth.utils import hash_password, generate_id


class TestUsersDao:
    """Tests for Users DAO."""

    @pytest_asyncio.fixture
    async def dao(self):
        return PostgresUsersDao()

    @pytest.mark.asyncio
    async def test_create_user(self, dao, db_session: AsyncSession):
        """Test user creation."""
        user = await dao.create_user(
            session=db_session,
            email="newuser@example.com",
            password_hash=hash_password("password123"),
            name="New User",
        )
        
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.name == "New User"
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, dao, db_session: AsyncSession, test_user: User):
        """Test getting user by email."""
        user = await dao.get_user_by_email(db_session, test_user.email)
        
        assert user is not None
        assert user.id == test_user.id

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, dao, db_session: AsyncSession):
        """Test getting non-existent user by email."""
        user = await dao.get_user_by_email(db_session, "nonexistent@example.com")
        
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, dao, db_session: AsyncSession, test_user: User):
        """Test getting user by ID."""
        user = await dao.get_user_by_id(db_session, test_user.id)
        
        assert user is not None
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_email_exists(self, dao, db_session: AsyncSession, test_user: User):
        """Test email existence check."""
        exists = await dao.email_exists(db_session, test_user.email)
        assert exists is True
        
        exists = await dao.email_exists(db_session, "nonexistent@example.com")
        assert exists is False

    @pytest.mark.asyncio
    async def test_update_user(self, dao, db_session: AsyncSession, test_user: User):
        """Test user update."""
        updated = await dao.update_user(
            db_session,
            test_user.id,
            {"name": "Updated Name"},
        )
        
        assert updated is not None
        assert updated.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_deactivate_user(self, dao, db_session: AsyncSession, test_user: User):
        """Test user deactivation."""
        result = await dao.deactivate_user(db_session, test_user.id)
        
        assert result is True
        
        user = await dao.get_user_by_id(db_session, test_user.id)
        assert user.is_active is False


class TestPatientsDao:
    """Tests for Patients DAO."""

    @pytest_asyncio.fixture
    async def dao(self):
        return PostgresPatientsDao()

    @pytest.mark.asyncio
    async def test_create_patient(self, dao, db_session: AsyncSession, test_user: User):
        """Test patient creation."""
        patient = await dao.create_patient(
            session=db_session,
            user_id=test_user.id,
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1985, 6, 20),
            gender="female",
        )
        
        assert patient.id is not None
        assert patient.first_name == "Jane"
        assert patient.user_id == test_user.id

    @pytest.mark.asyncio
    async def test_get_patient(self, dao, db_session: AsyncSession, test_patient: Patient):
        """Test getting patient by ID."""
        patient = await dao.get_patient(db_session, test_patient.id)
        
        assert patient is not None
        assert patient.first_name == test_patient.first_name

    @pytest.mark.asyncio
    async def test_get_patient_with_user_scope(self, dao, db_session: AsyncSession, test_patient: Patient, test_user: User):
        """Test patient retrieval with user scoping."""
        # Should find patient for correct user
        patient = await dao.get_patient_by_user(
            db_session,
            test_patient.id,
            test_user.id,
        )
        assert patient is not None
        
        # Should not find patient for wrong user
        patient = await dao.get_patient_by_user(
            db_session,
            test_patient.id,
            "wrong_user_id",
        )
        assert patient is None

    @pytest.mark.asyncio
    async def test_list_patients(self, dao, db_session: AsyncSession, test_patient: Patient, test_user: User):
        """Test listing patients for user."""
        patients = await dao.list_patients(db_session, test_user.id)
        
        assert len(patients) >= 1
        assert any(p.id == test_patient.id for p in patients)

    @pytest.mark.asyncio
    async def test_update_patient(self, dao, db_session: AsyncSession, test_patient: Patient):
        """Test patient update."""
        updated = await dao.update_patient(
            db_session,
            test_patient.id,
            {"phone": "555-999-8888"},
        )
        
        assert updated is not None
        assert updated.phone == "555-999-8888"


class TestTriageThreadsDao:
    """Tests for Triage Threads DAO."""

    @pytest_asyncio.fixture
    async def dao(self):
        return PostgresTriageThreadsDao()

    @pytest.mark.asyncio
    async def test_create_thread(self, dao, db_session: AsyncSession, test_user: User, test_patient: Patient):
        """Test thread creation."""
        thread = await dao.create_thread(
            session=db_session,
            user_id=test_user.id,
            patient_id=test_patient.id,
            chief_complaint="Test complaint",
        )
        
        assert thread.id is not None
        assert thread.status == "INTERVIEWING"
        assert thread.chief_complaint == "Test complaint"

    @pytest.mark.asyncio
    async def test_get_thread(self, dao, db_session: AsyncSession, test_thread: TriageThread):
        """Test getting thread by ID."""
        thread = await dao.get_thread(db_session, test_thread.id)
        
        assert thread is not None
        assert thread.id == test_thread.id

    @pytest.mark.asyncio
    async def test_update_thread_status(self, dao, db_session: AsyncSession, test_thread: TriageThread):
        """Test updating thread status."""
        updated = await dao.update_status(
            db_session,
            test_thread.id,
            "EMERGENCY",
        )
        
        assert updated is not None
        assert updated.status == "EMERGENCY"

    @pytest.mark.asyncio
    async def test_update_intake_struct(self, dao, db_session: AsyncSession, test_thread: TriageThread):
        """Test updating intake structure."""
        intake = {
            "symptoms": ["headache", "nausea"],
            "severity": 7,
            "duration_hours": 4,
        }
        
        updated = await dao.update_intake(
            db_session,
            test_thread.id,
            intake,
        )
        
        assert updated is not None
        assert updated.intake_struct["symptoms"] == ["headache", "nausea"]

    @pytest.mark.asyncio
    async def test_list_threads_by_patient(self, dao, db_session: AsyncSession, test_thread: TriageThread, test_patient: Patient, test_user: User):
        """Test listing threads for a patient."""
        threads = await dao.list_by_patient(
            db_session,
            test_patient.id,
            test_user.id,
        )
        
        assert len(threads) >= 1
        assert any(t.id == test_thread.id for t in threads)


class TestMessagesDao:
    """Tests for Messages DAO."""

    @pytest_asyncio.fixture
    async def dao(self):
        return PostgresMessagesDao()

    @pytest.mark.asyncio
    async def test_create_message(self, dao, db_session: AsyncSession, test_thread: TriageThread):
        """Test message creation."""
        message = await dao.create_message(
            session=db_session,
            thread_id=test_thread.id,
            role="user",
            content="I have a headache",
        )
        
        assert message.id is not None
        assert message.role == "user"
        assert message.content == "I have a headache"

    @pytest.mark.asyncio
    async def test_list_messages(self, dao, db_session: AsyncSession, test_thread: TriageThread):
        """Test listing messages for thread."""
        # Create some messages
        await dao.create_message(db_session, test_thread.id, "user", "Message 1")
        await dao.create_message(db_session, test_thread.id, "assistant", "Response 1")
        
        messages = await dao.list_messages(db_session, test_thread.id)
        
        assert len(messages) >= 2


class TestArtifactsDao:
    """Tests for Artifacts DAO."""

    @pytest_asyncio.fixture
    async def dao(self):
        return PostgresArtifactsDao()

    @pytest.mark.asyncio
    async def test_save_risk_assessment(self, dao, db_session: AsyncSession, test_thread: TriageThread):
        """Test saving risk assessment artifact."""
        risk_data = {
            "is_emergency": False,
            "disposition": "ROUTINE",
            "confidence": 0.85,
            "red_flags": [],
        }
        
        artifact = await dao.save_artifact(
            session=db_session,
            thread_id=test_thread.id,
            artifact_type="risk_assessment",
            data=risk_data,
        )
        
        assert artifact.id is not None
        assert artifact.artifact_type == "risk_assessment"

    @pytest.mark.asyncio
    async def test_get_artifacts_by_thread(self, dao, db_session: AsyncSession, test_thread: TriageThread):
        """Test retrieving all artifacts for a thread."""
        # Save multiple artifacts
        await dao.save_artifact(db_session, test_thread.id, "risk_assessment", {"disposition": "ROUTINE"})
        await dao.save_artifact(db_session, test_thread.id, "icd10_coding", {"codes": []})
        
        artifacts = await dao.get_by_thread(db_session, test_thread.id)
        
        assert len(artifacts) >= 2


class TestRAGDocumentsDao:
    """Tests for RAG Documents DAO with pgvector."""

    @pytest_asyncio.fixture
    async def dao(self):
        return PostgresRAGDocumentsDao()

    @pytest.mark.asyncio
    async def test_ingest_document(self, dao, db_session: AsyncSession):
        """Test document ingestion."""
        # Mock embedding (1536 dimensions for OpenAI)
        embedding = [0.1] * 1536
        
        doc = await dao.ingest_document(
            session=db_session,
            source="icd10",
            code="R51.9",
            title="Headache, unspecified",
            content="Pain in head, headache NOS, cephalgia",
            embedding=embedding,
            metadata={"category": "R codes", "chapter": 18},
        )
        
        assert doc.id is not None
        assert doc.code == "R51.9"

    @pytest.mark.asyncio
    async def test_vector_search(self, dao, db_session: AsyncSession):
        """Test vector similarity search."""
        # First, ingest some documents
        embedding1 = [0.1] * 1536
        embedding2 = [0.2] * 1536
        
        await dao.ingest_document(
            session=db_session,
            source="icd10",
            code="R51.9",
            title="Headache",
            content="Head pain",
            embedding=embedding1,
        )
        
        await dao.ingest_document(
            session=db_session,
            source="icd10",
            code="G43.909",
            title="Migraine",
            content="Severe headache with visual disturbance",
            embedding=embedding2,
        )
        
        # Search with similar embedding
        query_embedding = [0.15] * 1536
        
        results = await dao.search(
            session=db_session,
            query_embedding=query_embedding,
            source="icd10",
            top_k=5,
        )
        
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_bulk_ingest(self, dao, db_session: AsyncSession):
        """Test bulk document ingestion."""
        documents = [
            {
                "source": "icd10",
                "code": f"TEST.{i}",
                "title": f"Test Code {i}",
                "content": f"Test content {i}",
                "embedding": [0.1 * (i + 1)] * 1536,
            }
            for i in range(5)
        ]
        
        count = await dao.bulk_ingest(db_session, documents)
        
        assert count == 5

    @pytest.mark.asyncio
    async def test_get_by_code(self, dao, db_session: AsyncSession):
        """Test retrieving document by code."""
        embedding = [0.5] * 1536
        
        await dao.ingest_document(
            session=db_session,
            source="icd10",
            code="UNIQUE.CODE",
            title="Unique Test",
            content="Unique content",
            embedding=embedding,
        )
        
        doc = await dao.get_by_code(db_session, "UNIQUE.CODE", "icd10")
        
        assert doc is not None
        assert doc.code == "UNIQUE.CODE"

