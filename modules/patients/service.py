"""Patients service."""

from datetime import datetime
from typing import Dict, Any, List, Optional

from database.dao.patients import PatientsDao
from global_utils.exceptions import NotFoundError, ValidationError


class PatientsService:
    """Service class for patient operations."""

    def __init__(self, patients_dao: PatientsDao):
        """Initialize PatientsService.
        
        Args:
            patients_dao: Patients DAO instance
        """
        self.patients_dao = patients_dao

    async def create_patient(
        self,
        user_id: str,
        patient_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new patient.
        
        Args:
            user_id: ID of the user creating the patient
            patient_data: Patient data
            
        Returns:
            Created patient data
        """
        # Add user_id to patient data
        patient_data["user_id"] = user_id

        # Convert date to datetime if needed
        if "date_of_birth" in patient_data and patient_data["date_of_birth"]:
            dob = patient_data["date_of_birth"]
            if hasattr(dob, "isoformat") and not isinstance(dob, datetime):
                patient_data["date_of_birth"] = datetime.combine(dob, datetime.min.time())

        patient_id = await self.patients_dao.create_patient(patient_data)
        patient = await self.patients_dao.get_patient_by_id(patient_id)

        return {
            "success": True,
            "data": patient
        }

    async def get_patient(
        self,
        patient_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get a patient by ID.
        
        Args:
            patient_id: Patient's ID
            user_id: User's ID for scoping
            
        Returns:
            Patient data
            
        Raises:
            NotFoundError: If patient not found
        """
        patient = await self.patients_dao.get_patient_by_id(patient_id, user_id)

        if not patient:
            raise NotFoundError("Patient not found")

        return {
            "success": True,
            "data": patient
        }

    async def list_patients(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List patients for a user.
        
        Args:
            user_id: User's ID
            skip: Number to skip
            limit: Maximum to return
            search: Optional search term
            
        Returns:
            List of patients with pagination info
        """
        patients = await self.patients_dao.get_patients_by_user(
            user_id=user_id,
            skip=skip,
            limit=limit,
            search=search,
        )

        total = await self.patients_dao.count_patients_by_user(user_id)

        return {
            "success": True,
            "data": patients,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total,
                "has_more": skip + len(patients) < total,
            }
        }

    async def update_patient(
        self,
        patient_id: str,
        user_id: str,
        update_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a patient.
        
        Args:
            patient_id: Patient's ID
            user_id: User's ID for scoping
            update_data: Fields to update
            
        Returns:
            Updated patient data
            
        Raises:
            NotFoundError: If patient not found
        """
        # Check patient exists
        existing = await self.patients_dao.get_patient_by_id(patient_id, user_id)
        if not existing:
            raise NotFoundError("Patient not found")

        # Filter out None values
        update_data = {k: v for k, v in update_data.items() if v is not None}

        # Convert date to datetime if needed
        if "date_of_birth" in update_data and update_data["date_of_birth"]:
            dob = update_data["date_of_birth"]
            if hasattr(dob, "isoformat") and not isinstance(dob, datetime):
                update_data["date_of_birth"] = datetime.combine(dob, datetime.min.time())

        await self.patients_dao.update_patient(patient_id, update_data, user_id)
        patient = await self.patients_dao.get_patient_by_id(patient_id, user_id)

        return {
            "success": True,
            "data": patient
        }

    async def delete_patient(
        self,
        patient_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Soft delete a patient.
        
        Args:
            patient_id: Patient's ID
            user_id: User's ID for scoping
            
        Returns:
            Success message
            
        Raises:
            NotFoundError: If patient not found
        """
        # Check patient exists
        existing = await self.patients_dao.get_patient_by_id(patient_id, user_id)
        if not existing:
            raise NotFoundError("Patient not found")

        await self.patients_dao.delete_patient(patient_id, user_id)

        return {
            "success": True,
            "message": "Patient deleted successfully"
        }

