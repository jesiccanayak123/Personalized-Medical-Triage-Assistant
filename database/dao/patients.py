"""Patients DAO."""

from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession

from database.base_dao import BasePostgresDao
from database.models import Patient


class PatientsDao(BasePostgresDao):
    """Data Access Object for patients table."""

    model = Patient

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_patient(self, patient_data: Dict[str, Any]) -> str:
        """Create a new patient.
        
        Args:
            patient_data: Patient data
            
        Returns:
            Inserted patient ID
        """
        now = datetime.utcnow()
        patient_data["created_at"] = now
        patient_data["updated_at"] = now
        patient_data["is_active"] = patient_data.get("is_active", True)
        return await self.insert_one(patient_data)

    async def get_patient_by_id(
        self,
        patient_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get patient by ID, optionally scoped to user.
        
        Args:
            patient_id: Patient's ID
            user_id: Optional user ID for scoping
            
        Returns:
            Patient data or None
        """
        filters = {"id": patient_id}
        if user_id:
            filters["user_id"] = user_id
        return await self.find_one(filters)

    async def get_patients_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all patients for a user.
        
        Args:
            user_id: User's ID
            skip: Number of records to skip
            limit: Maximum records to return
            search: Optional search term for name
            
        Returns:
            List of patients
        """
        filters = {"user_id": user_id, "is_active": True}
        
        # Note: Search would need special handling for ILIKE
        # For simplicity, we'll return all and filter in service
        
        return await self.find_many(
            filters=filters,
            skip=skip,
            limit=limit,
            sort=[("last_name", 1), ("first_name", 1)]
        )

    async def update_patient(
        self,
        patient_id: str,
        update_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> int:
        """Update patient data.
        
        Args:
            patient_id: Patient's ID
            update_data: Fields to update
            user_id: Optional user ID for scoping
            
        Returns:
            Number of modified records
        """
        filters = {"id": patient_id}
        if user_id:
            filters["user_id"] = user_id
        
        update_data["updated_at"] = datetime.utcnow()
        return await self.update_one(filters, update_data)

    async def delete_patient(
        self,
        patient_id: str,
        user_id: Optional[str] = None
    ) -> int:
        """Soft delete a patient (set is_active=False).
        
        Args:
            patient_id: Patient's ID
            user_id: Optional user ID for scoping
            
        Returns:
            Number of modified records
        """
        filters = {"id": patient_id}
        if user_id:
            filters["user_id"] = user_id
        return await self.update_one(filters, {"is_active": False})

    async def count_patients_by_user(self, user_id: str) -> int:
        """Count patients for a user.
        
        Args:
            user_id: User's ID
            
        Returns:
            Count of patients
        """
        return await self.count({"user_id": user_id, "is_active": True})

