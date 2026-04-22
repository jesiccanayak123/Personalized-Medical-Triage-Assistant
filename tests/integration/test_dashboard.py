"""
Integration tests for dashboard endpoints.
"""
import pytest
from httpx import AsyncClient

from database.models import Patient, TriageThread


class TestDashboard:
    """Integration tests for dashboard endpoints."""

    @pytest.mark.asyncio
    async def test_get_summary(self, authenticated_client: AsyncClient, test_patient: Patient, test_thread: TriageThread):
        """Test getting dashboard summary."""
        response = await authenticated_client.get("/api/v1/dashboard/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        summary = data["data"]
        assert "total_patients" in summary
        assert "active_threads" in summary
        assert "emergencies_today" in summary
        assert "completed_today" in summary
        
        # Should have at least our test data
        assert summary["total_patients"] >= 1

    @pytest.mark.asyncio
    async def test_get_patients_with_status(self, authenticated_client: AsyncClient, test_patient: Patient, test_thread: TriageThread):
        """Test getting patients with their last triage status."""
        response = await authenticated_client.get("/api/v1/dashboard/patients")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        patients = data["data"]
        assert len(patients) >= 1
        
        # Should include triage info
        patient_data = next((p for p in patients if p["id"] == test_patient.id), None)
        assert patient_data is not None
        assert "last_triage_status" in patient_data or "active_threads_count" in patient_data

    @pytest.mark.asyncio
    async def test_dashboard_pagination(self, authenticated_client: AsyncClient):
        """Test dashboard pagination."""
        response = await authenticated_client.get(
            "/api/v1/dashboard/patients",
            params={"skip": 0, "limit": 5},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 5

    @pytest.mark.asyncio
    async def test_dashboard_unauthorized(self, client: AsyncClient):
        """Test dashboard requires authentication."""
        response = await client.get("/api/v1/dashboard/summary")
        assert response.status_code == 401

