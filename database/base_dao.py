"""PostgreSQL Base DAO with common CRUD operations.

This module provides a base DAO class for PostgreSQL database access
with async support and common query patterns.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from database.models import Base


T = TypeVar("T", bound=DeclarativeBase)


def generate_objectid() -> str:
    """Generate a new UUID-style string ID.
    
    Returns:
        36-character UUID string
    """
    return str(uuid.uuid4())


class BasePostgresDao:
    """Base Data Access Object for PostgreSQL operations."""
    
    # Model class to be set by subclasses
    model: Type[Base]
    
    def __init__(self, session: AsyncSession):
        """Initialize the DAO with a database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self._session = session
        self._session_factory = None
        self._auto_commit = True

    @property
    def session(self) -> AsyncSession:
        """Get the current session."""
        return self._session

    @session.setter
    def session(self, value: AsyncSession):
        """Set the session."""
        self._session = value

    def set_session_factory(self, factory):
        """Set the session factory for creating new sessions.
        
        Args:
            factory: Callable that returns a new AsyncSession
        """
        self._session_factory = factory

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self._session.rollback()

    async def close(self) -> None:
        """Close the session."""
        await self._session.close()

    async def _refresh_session(self) -> None:
        """Refresh the session after commit if factory is available."""
        if self._auto_commit and self._session_factory:
            await self._session.close()
            self._session = self._session_factory()

    async def insert_one(self, data: Dict[str, Any]) -> str:
        """Insert a single record.
        
        Args:
            data: Record data as dictionary
            
        Returns:
            Inserted record ID
        """
        # Generate ID if not provided
        if "id" not in data:
            data["id"] = generate_objectid()

        # Add timestamps if model has them
        now = datetime.utcnow()
        if hasattr(self.model, "created_at") and "created_at" not in data:
            data["created_at"] = now
        if hasattr(self.model, "updated_at") and "updated_at" not in data:
            data["updated_at"] = now

        # Create and add instance
        instance = self.model(**data)
        self._session.add(instance)
        await self._session.flush()

        result_id = instance.id

        if self._auto_commit:
            await self._session.commit()
            await self._refresh_session()

        return result_id

    async def insert_many(self, records: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple records.
        
        Args:
            records: List of record data dictionaries
            
        Returns:
            List of inserted record IDs
        """
        ids = []
        for record in records:
            record_id = await self.insert_one(record)
            ids.append(record_id)
        return ids

    async def find_one(
        self,
        filters: Dict[str, Any],
        projection: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Find a single record matching filters.
        
        Args:
            filters: Query filters as {field: value} or {field: {operator: value}}
            projection: Fields to include (not fully implemented)
            
        Returns:
            Record as dictionary or None
        """
        filter_expr = self._build_filter_expression(filters)
        stmt = select(self.model).where(filter_expr).limit(1)

        result = await self._session.execute(stmt)
        instance = result.scalar_one_or_none()

        if instance is None:
            return None

        return self._instance_to_dict(instance)

    async def find_many(
        self,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: Optional[int] = None,
        sort: Optional[List[tuple]] = None,
    ) -> List[Dict[str, Any]]:
        """Find multiple records matching filters.
        
        Args:
            filters: Query filters
            skip: Number of records to skip
            limit: Maximum records to return
            sort: List of (field, direction) tuples. Direction: 1=asc, -1=desc
            
        Returns:
            List of records as dictionaries
        """
        stmt = select(self.model)

        if filters:
            filter_expr = self._build_filter_expression(filters)
            stmt = stmt.where(filter_expr)

        # Apply sorting
        if sort:
            for field, direction in sort:
                try:
                    column = getattr(self.model, field)
                    if direction == -1:
                        stmt = stmt.order_by(column.desc())
                    else:
                        stmt = stmt.order_by(column.asc())
                except AttributeError:
                    pass
        elif hasattr(self.model, "created_at"):
            stmt = stmt.order_by(self.model.created_at.desc())

        # Apply pagination
        if skip:
            stmt = stmt.offset(skip)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        instances = result.scalars().all()

        return [self._instance_to_dict(inst) for inst in instances]

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records matching filters.
        
        Args:
            filters: Query filters
            
        Returns:
            Count of matching records
        """
        stmt = select(func.count()).select_from(self.model)

        if filters:
            filter_expr = self._build_filter_expression(filters)
            stmt = stmt.where(filter_expr)

        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def update_one(
        self,
        filters: Dict[str, Any],
        update_data: Dict[str, Any]
    ) -> int:
        """Update a single record.
        
        Args:
            filters: Query filters to find record
            update_data: Fields to update
            
        Returns:
            Number of modified records
        """
        filter_expr = self._build_filter_expression(filters)
        stmt = select(self.model).where(filter_expr).limit(1)

        result = await self._session.execute(stmt)
        instance = result.scalar_one_or_none()

        if instance is None:
            return 0

        # Apply updates
        for key, value in update_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        # Update timestamp if model has it
        if hasattr(instance, "updated_at"):
            instance.updated_at = datetime.utcnow()

        await self._session.flush()

        if self._auto_commit:
            await self._session.commit()
            await self._refresh_session()

        return 1

    async def update_many(
        self,
        filters: Dict[str, Any],
        update_data: Dict[str, Any]
    ) -> int:
        """Update multiple records.
        
        Args:
            filters: Query filters
            update_data: Fields to update
            
        Returns:
            Number of modified records
        """
        filter_expr = self._build_filter_expression(filters)
        stmt = select(self.model).where(filter_expr)

        result = await self._session.execute(stmt)
        instances = result.scalars().all()

        count = 0
        for instance in instances:
            for key, value in update_data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            if hasattr(instance, "updated_at"):
                instance.updated_at = datetime.utcnow()
            count += 1

        await self._session.flush()

        if self._auto_commit:
            await self._session.commit()
            await self._refresh_session()

        return count

    async def delete_one(self, filters: Dict[str, Any]) -> int:
        """Delete a single record.
        
        Args:
            filters: Query filters
            
        Returns:
            Number of deleted records
        """
        filter_expr = self._build_filter_expression(filters)
        stmt = select(self.model).where(filter_expr).limit(1)

        result = await self._session.execute(stmt)
        instance = result.scalar_one_or_none()

        if instance is None:
            return 0

        await self._session.delete(instance)
        await self._session.flush()

        if self._auto_commit:
            await self._session.commit()
            await self._refresh_session()

        return 1

    async def delete_many(self, filters: Dict[str, Any]) -> int:
        """Delete multiple records.
        
        Args:
            filters: Query filters
            
        Returns:
            Number of deleted records
        """
        filter_expr = self._build_filter_expression(filters)
        stmt = select(self.model).where(filter_expr)

        result = await self._session.execute(stmt)
        instances = result.scalars().all()

        count = len(instances)
        for instance in instances:
            await self._session.delete(instance)

        await self._session.flush()

        if self._auto_commit:
            await self._session.commit()
            await self._refresh_session()

        return count

    async def get_paginated(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page_size: int = 10,
        page_number: int = 1,
        sort: Optional[List[tuple]] = None,
    ) -> tuple:
        """Get paginated results.
        
        Args:
            filters: Query filters
            page_size: Items per page
            page_number: Page number (1-indexed)
            sort: List of (field, direction) tuples
            
        Returns:
            Tuple of (results list, pagination info dict)
        """
        # Count total
        total_records = await self.count(filters)

        # Get page data
        skip = (page_number - 1) * page_size
        results = await self.find_many(
            filters=filters,
            skip=skip,
            limit=page_size,
            sort=sort,
        )

        pagination_info = {
            "page_size": page_size,
            "page_number": page_number,
            "has_next": total_records - page_size * page_number > 0,
            "total_records": total_records,
            "total_pages": (total_records + page_size - 1) // page_size,
        }

        return results, pagination_info

    def _build_filter_expression(self, filters: Dict[str, Any]) -> Any:
        """Build SQLAlchemy filter expression from query dict.
        
        Supports operators: $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin
        
        Args:
            filters: Query filters
            
        Returns:
            SQLAlchemy filter expression
        """
        conditions = []

        for field, value in filters.items():
            # Handle logical operators
            if field == "$or":
                or_conditions = [self._build_filter_expression(subq) for subq in value]
                conditions.append(or_(*or_conditions))
                continue

            if field == "$and":
                and_conditions = [self._build_filter_expression(subq) for subq in value]
                conditions.append(and_(*and_conditions))
                continue

            # Get column
            try:
                column = getattr(self.model, field)
            except AttributeError:
                continue  # Skip unknown fields

            # Handle operators
            if isinstance(value, dict):
                for op, op_value in value.items():
                    if op == "$eq":
                        conditions.append(column == op_value)
                    elif op == "$ne":
                        conditions.append(column != op_value)
                    elif op == "$gt":
                        conditions.append(column > op_value)
                    elif op == "$gte":
                        conditions.append(column >= op_value)
                    elif op == "$lt":
                        conditions.append(column < op_value)
                    elif op == "$lte":
                        conditions.append(column <= op_value)
                    elif op == "$in":
                        conditions.append(column.in_(op_value))
                    elif op == "$nin":
                        conditions.append(~column.in_(op_value))
                    elif op == "$exists":
                        if op_value:
                            conditions.append(column.isnot(None))
                        else:
                            conditions.append(column.is_(None))
                    elif op == "$regex" or op == "$ilike":
                        conditions.append(column.ilike(f"%{op_value}%"))
            else:
                # Simple equality
                conditions.append(column == value)

        if not conditions:
            return True  # No filter

        return and_(*conditions)

    def _instance_to_dict(self, instance: Any) -> Dict[str, Any]:
        """Convert SQLAlchemy instance to dictionary.
        
        Args:
            instance: SQLAlchemy model instance
            
        Returns:
            Dictionary representation
        """
        result = {}

        for column in instance.__table__.columns:
            value = getattr(instance, column.name)
            result[column.name] = value

        return result

