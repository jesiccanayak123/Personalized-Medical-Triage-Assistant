"""Artifacts DAO."""

from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession

from database.base_dao import BasePostgresDao
from database.models import Artifact


class ArtifactsDao(BasePostgresDao):
    """Data Access Object for artifacts table."""

    model = Artifact

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_artifact(self, artifact_data: Dict[str, Any]) -> str:
        """Create a new artifact.
        
        Args:
            artifact_data: Artifact data (thread_id, artifact_type, data)
            
        Returns:
            Inserted artifact ID
        """
        now = datetime.utcnow()
        artifact_data["created_at"] = now
        artifact_data["updated_at"] = now
        artifact_data["version"] = artifact_data.get("version", 1)
        return await self.insert_one(artifact_data)

    async def get_artifact_by_id(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Get artifact by ID.
        
        Args:
            artifact_id: Artifact's ID
            
        Returns:
            Artifact data or None
        """
        return await self.find_one({"id": artifact_id})

    async def get_artifacts_by_thread(
        self,
        thread_id: str,
        artifact_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all artifacts for a thread.
        
        Args:
            thread_id: Thread's ID
            artifact_type: Optional filter by type
            
        Returns:
            List of artifacts
        """
        filters = {"thread_id": thread_id}
        if artifact_type:
            filters["artifact_type"] = artifact_type
        
        return await self.find_many(
            filters=filters,
            sort=[("created_at", -1)]
        )

    async def get_latest_artifact(
        self,
        thread_id: str,
        artifact_type: str,
    ) -> Optional[Dict[str, Any]]:
        """Get the latest artifact of a type for a thread.
        
        Args:
            thread_id: Thread's ID
            artifact_type: Type of artifact
            
        Returns:
            Latest artifact or None
        """
        artifacts = await self.find_many(
            filters={"thread_id": thread_id, "artifact_type": artifact_type},
            limit=1,
            sort=[("version", -1)]
        )
        return artifacts[0] if artifacts else None

    async def update_artifact(
        self,
        artifact_id: str,
        data: Dict[str, Any],
    ) -> int:
        """Update artifact data with version increment.
        
        Args:
            artifact_id: Artifact's ID
            data: New artifact data
            
        Returns:
            Number of modified records
        """
        # Get current version
        artifact = await self.get_artifact_by_id(artifact_id)
        if not artifact:
            return 0
        
        update_data = {
            "data": data,
            "version": artifact.get("version", 0) + 1,
            "updated_at": datetime.utcnow()
        }
        return await self.update_one({"id": artifact_id}, update_data)

    async def upsert_artifact(
        self,
        thread_id: str,
        artifact_type: str,
        data: Dict[str, Any],
    ) -> str:
        """Create or update artifact for a thread.
        
        Args:
            thread_id: Thread's ID
            artifact_type: Type of artifact
            data: Artifact data
            
        Returns:
            Artifact ID
        """
        existing = await self.get_latest_artifact(thread_id, artifact_type)
        
        if existing:
            await self.update_artifact(existing["id"], data)
            return existing["id"]
        else:
            return await self.create_artifact({
                "thread_id": thread_id,
                "artifact_type": artifact_type,
                "data": data,
            })

