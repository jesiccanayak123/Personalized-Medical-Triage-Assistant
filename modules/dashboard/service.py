"""Dashboard service."""

from datetime import datetime, timedelta
from typing import Dict, Any, List

from database.dao.patients import PatientsDao
from database.dao.triage_threads import TriageThreadsDao


class DashboardService:
    """Service class for dashboard operations."""

    def __init__(
        self,
        patients_dao: PatientsDao,
        threads_dao: TriageThreadsDao,
    ):
        """Initialize DashboardService.
        
        Args:
            patients_dao: Patients DAO
            threads_dao: Triage threads DAO
        """
        self.patients_dao = patients_dao
        self.threads_dao = threads_dao

    async def get_summary(self, user_id: str) -> Dict[str, Any]:
        """Get dashboard summary statistics.
        
        Args:
            user_id: User's ID
            
        Returns:
            Dashboard stats
        """
        # Count total patients
        total_patients = await self.patients_dao.count_patients_by_user(user_id)

        # Count threads by status
        status_counts = await self.threads_dao.count_by_status(user_id)
        
        active_threads = sum([
            status_counts.get("INTERVIEWING", 0),
            status_counts.get("CODING", 0),
            status_counts.get("SCRIBING", 0),
        ])

        # Count emergencies today
        emergencies_today = await self.threads_dao.count_today(user_id, "EMERGENCY")

        # Count completed today
        completed_today = await self.threads_dao.count_today(user_id, "DONE")

        # Count completed this week
        week_ago = datetime.utcnow() - timedelta(days=7)
        completed_this_week = await self.threads_dao.count({
            "user_id": user_id,
            "status": "DONE",
            "completed_at": {"$gte": week_ago},
        })

        return {
            "success": True,
            "data": {
                "total_patients": total_patients,
                "active_threads": active_threads,
                "emergencies_today": emergencies_today,
                "completed_today": completed_today,
                "completed_this_week": completed_this_week,
            }
        }

    async def get_patients_with_status(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Get patients list with last triage status.
        
        Args:
            user_id: User's ID
            skip: Number to skip
            limit: Maximum to return
            
        Returns:
            List of patients with status info
        """
        # Get patients
        patients = await self.patients_dao.get_patients_by_user(
            user_id=user_id,
            skip=skip,
            limit=limit,
        )

        # Enrich with thread info
        patient_summaries = []
        for patient in patients:
            # Get latest thread for this patient
            threads = await self.threads_dao.get_threads_by_patient(
                patient_id=patient["id"],
                user_id=user_id,
                limit=1,
            )

            last_status = None
            last_activity = None
            active_count = 0

            if threads:
                latest_thread = threads[0]
                last_status = latest_thread.get("status")
                last_activity = latest_thread.get("updated_at")

                # Count active threads
                all_threads = await self.threads_dao.get_threads_by_patient(
                    patient_id=patient["id"],
                    user_id=user_id,
                    limit=100,
                )
                active_count = sum(
                    1 for t in all_threads 
                    if t.get("status") not in ["DONE", "EMERGENCY"]
                )

            patient_summaries.append({
                "id": patient["id"],
                "first_name": patient["first_name"],
                "last_name": patient["last_name"],
                "last_triage_status": last_status,
                "last_activity_at": last_activity,
                "active_threads_count": active_count,
            })

        total = await self.patients_dao.count_patients_by_user(user_id)

        return {
            "success": True,
            "data": patient_summaries,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total,
                "has_more": skip + len(patient_summaries) < total,
            }
        }

