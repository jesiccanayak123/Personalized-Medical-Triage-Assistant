"""Triage Threads DAO."""

from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.base_dao import BasePostgresDao
from database.models import TriageThread


class TriageThreadsDao(BasePostgresDao):
    """Data Access Object for triage_threads table."""

    model = TriageThread

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_thread(self, thread_data: Dict[str, Any]) -> str:
        """Create a new triage thread.
        
        Args:
            thread_data: Thread data
            
        Returns:
            Inserted thread ID
        """
        now = datetime.utcnow()
        thread_data["created_at"] = now
        thread_data["updated_at"] = now
        thread_data["started_at"] = now
        thread_data["status"] = thread_data.get("status", "INTERVIEWING")
        return await self.insert_one(thread_data)

    async def get_thread_by_id(
        self,
        thread_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get thread by ID, optionally scoped to user.
        
        Args:
            thread_id: Thread's ID
            user_id: Optional user ID for scoping
            
        Returns:
            Thread data or None
        """
        filters = {"id": thread_id}
        if user_id:
            filters["user_id"] = user_id
        return await self.find_one(filters)

    async def get_threads_by_patient(
        self,
        patient_id: str,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get all threads for a patient.
        
        Args:
            patient_id: Patient's ID
            user_id: Optional user ID for scoping
            skip: Number to skip
            limit: Maximum to return
            
        Returns:
            List of threads
        """
        filters = {"patient_id": patient_id}
        if user_id:
            filters["user_id"] = user_id
        
        return await self.find_many(
            filters=filters,
            skip=skip,
            limit=limit,
            sort=[("created_at", -1)]
        )

    async def get_threads_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get all threads for a user.
        
        Args:
            user_id: User's ID
            status: Optional status filter
            skip: Number to skip
            limit: Maximum to return
            
        Returns:
            List of threads
        """
        filters = {"user_id": user_id}
        if status:
            filters["status"] = status
        
        return await self.find_many(
            filters=filters,
            skip=skip,
            limit=limit,
            sort=[("updated_at", -1)]
        )

    async def update_thread(
        self,
        thread_id: str,
        update_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> int:
        """Update thread data.
        
        Args:
            thread_id: Thread's ID
            update_data: Fields to update
            user_id: Optional user ID for scoping
            
        Returns:
            Number of modified records
        """
        filters = {"id": thread_id}
        if user_id:
            filters["user_id"] = user_id
        
        update_data["updated_at"] = datetime.utcnow()
        return await self.update_one(filters, update_data)

    async def update_status(
        self,
        thread_id: str,
        status: str,
        user_id: Optional[str] = None
    ) -> int:
        """Update thread status.
        
        Args:
            thread_id: Thread's ID
            status: New status
            user_id: Optional user ID for scoping
            
        Returns:
            Number of modified records
        """
        update_data = {"status": status}
        if status == "DONE":
            update_data["completed_at"] = datetime.utcnow()
        
        return await self.update_thread(thread_id, update_data, user_id)

    async def count_by_status(self, user_id: str) -> Dict[str, int]:
        """Count threads by status for a user.
        
        Args:
            user_id: User's ID
            
        Returns:
            Dict of status: count
        """
        # Get counts for each status
        statuses = ["INTERVIEWING", "EMERGENCY", "CODING", "SCRIBING", "DONE"]
        counts = {}
        
        for status in statuses:
            counts[status] = await self.count({"user_id": user_id, "status": status})
        
        return counts

    async def count_today(self, user_id: str, status: Optional[str] = None) -> int:
        """Count threads created today.
        
        Args:
            user_id: User's ID
            status: Optional status filter
            
        Returns:
            Count of threads
        """
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        filters = {
            "user_id": user_id,
            "created_at": {"$gte": today_start}
        }
        if status:
            filters["status"] = status
        
        return await self.count(filters)

    async def get_active_threads(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get active (non-DONE) threads.
        
        Args:
            user_id: User's ID
            limit: Maximum to return
            
        Returns:
            List of active threads
        """
        filters = {
            "user_id": user_id,
            "status": {"$nin": ["DONE"]}
        }
        
        return await self.find_many(
            filters=filters,
            limit=limit,
            sort=[("updated_at", -1)]
        )

