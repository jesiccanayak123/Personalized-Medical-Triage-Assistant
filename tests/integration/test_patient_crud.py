"""
Integration tests for patient CRUD operations.
"""
import pytest
from httpx import AsyncClient

from database.models import Patient


class TestPatientCRUD:
    """Integration tests for patient endpoints."""

    @pytest.mark.asyncio
    async def test_create_patient(self, authenticated_client: AsyncClient):
        """Test patient creation."""
        response = await authenticated_client.post(
            "/api/v1/patients",
            json={
                "first_name": "Jane",
                "last_name": "Smith",
                "date_of_birth": "1985-06-20",
                "gender": "female",
                "phone": "555-987-6543",
                "email": "jane.smith@example.com",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["first_name"] == "Jane"
        assert data["data"]["last_name"] == "Smith"

    @pytest.mark.asyncio
    async def test_create_patient_minimal(self, authenticated_client: AsyncClient):
        """Test patient creation with minimal data."""
        response = await authenticated_client.post(
            "/api/v1/patients",
            json={
                "first_name": "John",
                "last_name": "Doe",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["first_name"] == "John"

    @pytest.mark.asyncio
    async def test_create_patient_unauthorized(self, client: AsyncClient):
        """Test patient creation without auth fails."""
        response = await client.post(
            "/api/v1/patients",
            json={
                "first_name": "Test",
                "last_name": "User",
            },
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_patients(self, authenticated_client: AsyncClient, test_patient: Patient):
        """Test listing patients."""
        response = await authenticated_client.get("/api/v1/patients")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 1

    @pytest.mark.asyncio
    async def test_list_patients_pagination(self, authenticated_client: AsyncClient):
        """Test patient listing with pagination."""
        # Create multiple patients
        for i in range(5):
            await authenticated_client.post(
                "/api/v1/patients",
                json={"first_name": f"Test{i}", "last_name": "Patient"},
            )
        
        # Get first page
        response = await authenticated_client.get(
            "/api/v1/patients",
            params={"skip": 0, "limit": 2},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 2

    @pytest.mark.asyncio
    async def test_get_patient(self, authenticated_client: AsyncClient, test_patient: Patient):
        """Test getting a specific patient."""
        response = await authenticated_client.get(f"/api/v1/patients/{test_patient.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == test_patient.id
        assert data["data"]["first_name"] == test_patient.first_name

    @pytest.mark.asyncio
    async def test_get_patient_not_found(self, authenticated_client: AsyncClient):
        """Test getting non-existent patient."""
        response = await authenticated_client.get("/api/v1/patients/nonexistent123")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_patient(self, authenticated_client: AsyncClient, test_patient: Patient):
        """Test updating patient."""
        response = await authenticated_client.put(
            f"/api/v1/patients/{test_patient.id}",
            json={
                "phone": "555-111-2222",
                "email": "updated@example.com",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["phone"] == "555-111-2222"
        assert data["data"]["email"] == "updated@example.com"

    @pytest.mark.asyncio
    async def test_patient_user_scoping(self, client: AsyncClient, test_patient: Patient, db_session):
        """Test that patients are scoped to their users."""
        # Create another user and authenticate
        from modules.auth.utils import hash_password, generate_id
        from database.models import User
        from database.dao.user_tokens import PostgresUserTokensDao
        
        other_user = User(
            id=generate_id(),
            email="other@example.com",
            password_hash=hash_password("password123"),
            name="Other User",
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.commit()
        
        # Get token for other user
        dao = PostgresUserTokensDao()
        token = await dao.create_token(db_session, other_user.id)
        
        # Try to access first user's patient
        client.headers["Authorization"] = f"Bearer {token}"
        response = await client.get(f"/api/v1/patients/{test_patient.id}")
        
        # Should not find it (belongs to different user)
        assert response.status_code == 404

