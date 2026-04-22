"""SQLAlchemy models for Medical Triage Assistant.

This module defines all database models using SQLAlchemy ORM with:
- UUID-style string IDs for compatibility
- pgvector support for embeddings
- JSONB columns for flexible nested data
- Proper indexes for query performance
"""

from datetime import datetime
from typing import Optional, List, Any

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer, Index,
    ForeignKey, UniqueConstraint, func, BigInteger, Sequence, Float
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from config.settings import settings


# Sequences for auto-increment serial numbers
users_sl_no_seq = Sequence("users_sl_no_seq")
patients_sl_no_seq = Sequence("patients_sl_no_seq")
triage_threads_sl_no_seq = Sequence("triage_threads_sl_no_seq")
messages_sl_no_seq = Sequence("messages_sl_no_seq")
artifacts_sl_no_seq = Sequence("artifacts_sl_no_seq")
rag_documents_sl_no_seq = Sequence("rag_documents_sl_no_seq")
user_tokens_sl_no_seq = Sequence("user_tokens_sl_no_seq")


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    sl_no: Mapped[int] = mapped_column(
        BigInteger, users_sl_no_seq,
        server_default=users_sl_no_seq.next_value(),
        nullable=False, index=True, unique=True
    )

    # Core fields
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Timestamps
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    tokens: Mapped[List["UserToken"]] = relationship("UserToken", back_populates="user", cascade="all, delete-orphan")
    patients: Mapped[List["Patient"]] = relationship("Patient", back_populates="user", cascade="all, delete-orphan")
    triage_threads: Mapped[List["TriageThread"]] = relationship("TriageThread", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class UserToken(Base):
    """User authentication tokens."""
    __tablename__ = "user_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    sl_no: Mapped[int] = mapped_column(
        BigInteger, user_tokens_sl_no_seq,
        server_default=user_tokens_sl_no_seq.next_value(),
        nullable=False, index=True, unique=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tokens")

    __table_args__ = (
        Index("ix_user_tokens_validation", "token", "is_revoked", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<UserToken(id={self.id}, user_id={self.user_id})>"


class Patient(Base):
    """Patient model for medical records."""
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    sl_no: Mapped[int] = mapped_column(
        BigInteger, patients_sl_no_seq,
        server_default=patients_sl_no_seq.next_value(),
        nullable=False, index=True, unique=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Patient info
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(DateTime)
    gender: Mapped[Optional[str]] = mapped_column(String(50))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))

    # Medical info (JSONB for flexibility)
    medical_history: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    allergies: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    medications: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    emergency_contact: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="patients")
    triage_threads: Mapped[List["TriageThread"]] = relationship("TriageThread", back_populates="patient", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_patients_user_name", "user_id", "last_name", "first_name"),
    )

    def __repr__(self) -> str:
        return f"<Patient(id={self.id}, name={self.first_name} {self.last_name})>"


class TriageThread(Base):
    """Triage conversation thread."""
    __tablename__ = "triage_threads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    sl_no: Mapped[int] = mapped_column(
        BigInteger, triage_threads_sl_no_seq,
        server_default=triage_threads_sl_no_seq.next_value(),
        nullable=False, index=True, unique=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), nullable=False, index=True)

    # Thread status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="INTERVIEWING", index=True
    )  # INTERVIEWING, EMERGENCY, CODING, SCRIBING, DONE

    # Chief complaint (initial reason for triage)
    chief_complaint: Mapped[Optional[str]] = mapped_column(Text)

    # Structured interview data (captured during conversation)
    intake_data: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    missing_fields: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    completion_reason: Mapped[Optional[str]] = mapped_column(String(255))

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="triage_threads")
    patient: Mapped["Patient"] = relationship("Patient", back_populates="triage_threads")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="thread", cascade="all, delete-orphan")
    artifacts: Mapped[List["Artifact"]] = relationship("Artifact", back_populates="thread", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_triage_threads_patient_status", "patient_id", "status"),
        Index("ix_triage_threads_user_status", "user_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<TriageThread(id={self.id}, status={self.status})>"


class Message(Base):
    """Chat messages in triage thread."""
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    sl_no: Mapped[int] = mapped_column(
        BigInteger, messages_sl_no_seq,
        server_default=messages_sl_no_seq.next_value(),
        nullable=False, index=True, unique=True
    )
    thread_id: Mapped[str] = mapped_column(String(36), ForeignKey("triage_threads.id"), nullable=False, index=True)

    # Message content
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # user, assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Metadata
    agent_name: Mapped[Optional[str]] = mapped_column(String(100))  # Which agent generated this
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())

    # Relationships
    thread: Mapped["TriageThread"] = relationship("TriageThread", back_populates="messages")

    __table_args__ = (
        Index("ix_messages_thread_created", "thread_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role})>"


class Artifact(Base):
    """Triage artifacts (risk assessment, ICD-10 codes, SOAP notes)."""
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    sl_no: Mapped[int] = mapped_column(
        BigInteger, artifacts_sl_no_seq,
        server_default=artifacts_sl_no_seq.next_value(),
        nullable=False, index=True, unique=True
    )
    thread_id: Mapped[str] = mapped_column(String(36), ForeignKey("triage_threads.id"), nullable=False, index=True)

    # Artifact type and data
    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Types: risk_assessment, icd10_coding, soap_note
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Version for updates
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    thread: Mapped["TriageThread"] = relationship("TriageThread", back_populates="artifacts")

    __table_args__ = (
        Index("ix_artifacts_thread_type", "thread_id", "artifact_type"),
    )

    def __repr__(self) -> str:
        return f"<Artifact(id={self.id}, type={self.artifact_type})>"


class RAGDocument(Base):
    """RAG documents for ICD-10 codes and other reference data."""
    __tablename__ = "rag_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    sl_no: Mapped[int] = mapped_column(
        BigInteger, rag_documents_sl_no_seq,
        server_default=rag_documents_sl_no_seq.next_value(),
        nullable=False, index=True, unique=True
    )

    # Document info
    corpus_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # Types: icd10, clinical_guidelines, etc.
    
    # Content
    text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    # For ICD-10: {"code": "J06.9", "description": "...", "category": "..."}

    # Embedding vector
    embedding: Mapped[Any] = mapped_column(Vector(settings.vector_dimension))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index(
            "ix_rag_documents_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    def __repr__(self) -> str:
        return f"<RAGDocument(id={self.id}, corpus_type={self.corpus_type})>"

