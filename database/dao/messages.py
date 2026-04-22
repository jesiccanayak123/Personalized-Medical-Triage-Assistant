"""Messages DAO."""

from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession

from database.base_dao import BasePostgresDao
from database.models import Message


class MessagesDao(BasePostgresDao):
    """Data Access Object for messages table."""

    model = Message

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_message(self, message_data: Dict[str, Any]) -> str:
        """Create a new message.
        
        Args:
            message_data: Message data (thread_id, role, content, etc.)
            
        Returns:
            Inserted message ID
        """
        message_data["created_at"] = datetime.utcnow()
        return await self.insert_one(message_data)

    async def get_messages_by_thread(
        self,
        thread_id: str,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get all messages for a thread.
        
        Args:
            thread_id: Thread's ID
            skip: Number to skip
            limit: Maximum to return
            
        Returns:
            List of messages ordered by creation time
        """
        return await self.find_many(
            filters={"thread_id": thread_id},
            skip=skip,
            limit=limit,
            sort=[("created_at", 1)]  # Ascending order
        )

    async def get_last_message(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get the last message in a thread.
        
        Args:
            thread_id: Thread's ID
            
        Returns:
            Last message or None
        """
        messages = await self.find_many(
            filters={"thread_id": thread_id},
            limit=1,
            sort=[("created_at", -1)]  # Descending to get last
        )
        return messages[0] if messages else None

    async def count_messages(self, thread_id: str) -> int:
        """Count messages in a thread.
        
        Args:
            thread_id: Thread's ID
            
        Returns:
            Message count
        """
        return await self.count({"thread_id": thread_id})

    async def get_user_messages(
        self,
        thread_id: str,
    ) -> List[Dict[str, Any]]:
        """Get only user messages for a thread.
        
        Args:
            thread_id: Thread's ID
            
        Returns:
            List of user messages
        """
        return await self.find_many(
            filters={"thread_id": thread_id, "role": "user"},
            sort=[("created_at", 1)]
        )

    async def get_assistant_messages(
        self,
        thread_id: str,
    ) -> List[Dict[str, Any]]:
        """Get only assistant messages for a thread.
        
        Args:
            thread_id: Thread's ID
            
        Returns:
            List of assistant messages
        """
        return await self.find_many(
            filters={"thread_id": thread_id, "role": "assistant"},
            sort=[("created_at", 1)]
        )

