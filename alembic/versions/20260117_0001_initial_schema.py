"""Initial schema with all tables

Revision ID: 0001
Revises: 
Create Date: 2026-01-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    # Create sequences
    op.execute("CREATE SEQUENCE IF NOT EXISTS users_sl_no_seq")
    op.execute("CREATE SEQUENCE IF NOT EXISTS user_tokens_sl_no_seq")
    op.execute("CREATE SEQUENCE IF NOT EXISTS patients_sl_no_seq")
    op.execute("CREATE SEQUENCE IF NOT EXISTS triage_threads_sl_no_seq")
    op.execute("CREATE SEQUENCE IF NOT EXISTS messages_sl_no_seq")
    op.execute("CREATE SEQUENCE IF NOT EXISTS artifacts_sl_no_seq")
    op.execute("CREATE SEQUENCE IF NOT EXISTS rag_documents_sl_no_seq")
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('sl_no', sa.BigInteger(), server_default=sa.text("nextval('users_sl_no_seq')"), nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_login_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])
    op.create_index('ix_users_sl_no', 'users', ['sl_no'], unique=True)
    
    # User tokens table
    op.create_table(
        'user_tokens',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('sl_no', sa.BigInteger(), server_default=sa.text("nextval('user_tokens_sl_no_seq')"), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('token', sa.String(255), unique=True, nullable=False),
        sa.Column('is_revoked', sa.Boolean(), default=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_user_tokens_user_id', 'user_tokens', ['user_id'])
    op.create_index('ix_user_tokens_token', 'user_tokens', ['token'])
    op.create_index('ix_user_tokens_sl_no', 'user_tokens', ['sl_no'], unique=True)
    op.create_index('ix_user_tokens_validation', 'user_tokens', ['token', 'is_revoked', 'expires_at'])
    
    # Patients table
    op.create_table(
        'patients',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('sl_no', sa.BigInteger(), server_default=sa.text("nextval('patients_sl_no_seq')"), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('first_name', sa.String(255), nullable=False),
        sa.Column('last_name', sa.String(255), nullable=False),
        sa.Column('date_of_birth', sa.DateTime()),
        sa.Column('gender', sa.String(50)),
        sa.Column('phone', sa.String(50)),
        sa.Column('email', sa.String(255)),
        sa.Column('medical_history', postgresql.JSONB(), default={}),
        sa.Column('allergies', postgresql.JSONB(), default=[]),
        sa.Column('medications', postgresql.JSONB(), default=[]),
        sa.Column('emergency_contact', postgresql.JSONB(), default={}),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_patients_user_id', 'patients', ['user_id'])
    op.create_index('ix_patients_is_active', 'patients', ['is_active'])
    op.create_index('ix_patients_sl_no', 'patients', ['sl_no'], unique=True)
    op.create_index('ix_patients_user_name', 'patients', ['user_id', 'last_name', 'first_name'])
    
    # Triage threads table
    op.create_table(
        'triage_threads',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('sl_no', sa.BigInteger(), server_default=sa.text("nextval('triage_threads_sl_no_seq')"), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='INTERVIEWING'),
        sa.Column('chief_complaint', sa.Text()),
        sa.Column('intake_data', postgresql.JSONB(), default={}),
        sa.Column('missing_fields', postgresql.JSONB(), default=[]),
        sa.Column('completion_reason', sa.String(255)),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_triage_threads_user_id', 'triage_threads', ['user_id'])
    op.create_index('ix_triage_threads_patient_id', 'triage_threads', ['patient_id'])
    op.create_index('ix_triage_threads_status', 'triage_threads', ['status'])
    op.create_index('ix_triage_threads_sl_no', 'triage_threads', ['sl_no'], unique=True)
    op.create_index('ix_triage_threads_patient_status', 'triage_threads', ['patient_id', 'status'])
    op.create_index('ix_triage_threads_user_status', 'triage_threads', ['user_id', 'status'])
    
    # Messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('sl_no', sa.BigInteger(), server_default=sa.text("nextval('messages_sl_no_seq')"), nullable=False),
        sa.Column('thread_id', sa.String(36), sa.ForeignKey('triage_threads.id'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('agent_name', sa.String(100)),
        sa.Column('metadata_json', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_messages_thread_id', 'messages', ['thread_id'])
    op.create_index('ix_messages_sl_no', 'messages', ['sl_no'], unique=True)
    op.create_index('ix_messages_thread_created', 'messages', ['thread_id', 'created_at'])
    
    # Artifacts table
    op.create_table(
        'artifacts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('sl_no', sa.BigInteger(), server_default=sa.text("nextval('artifacts_sl_no_seq')"), nullable=False),
        sa.Column('thread_id', sa.String(36), sa.ForeignKey('triage_threads.id'), nullable=False),
        sa.Column('artifact_type', sa.String(50), nullable=False),
        sa.Column('data', postgresql.JSONB(), nullable=False),
        sa.Column('version', sa.Integer(), default=1),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_artifacts_thread_id', 'artifacts', ['thread_id'])
    op.create_index('ix_artifacts_artifact_type', 'artifacts', ['artifact_type'])
    op.create_index('ix_artifacts_sl_no', 'artifacts', ['sl_no'], unique=True)
    op.create_index('ix_artifacts_thread_type', 'artifacts', ['thread_id', 'artifact_type'])
    
    # RAG documents table
    op.create_table(
        'rag_documents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('sl_no', sa.BigInteger(), server_default=sa.text("nextval('rag_documents_sl_no_seq')"), nullable=False),
        sa.Column('corpus_type', sa.String(100), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(), default={}),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),  # Will use pgvector
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_rag_documents_corpus_type', 'rag_documents', ['corpus_type'])
    op.create_index('ix_rag_documents_sl_no', 'rag_documents', ['sl_no'], unique=True)
    
    # Add vector column with proper type
    op.execute("ALTER TABLE rag_documents DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE rag_documents ADD COLUMN embedding vector(1536)")
    
    # Create ivfflat index for vector similarity search
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_rag_documents_embedding 
        ON rag_documents 
        USING ivfflat (embedding vector_cosine_ops) 
        WITH (lists = 100)
    """)


def downgrade() -> None:
    op.drop_table('rag_documents')
    op.drop_table('artifacts')
    op.drop_table('messages')
    op.drop_table('triage_threads')
    op.drop_table('patients')
    op.drop_table('user_tokens')
    op.drop_table('users')
    
    op.execute("DROP SEQUENCE IF EXISTS rag_documents_sl_no_seq")
    op.execute("DROP SEQUENCE IF EXISTS artifacts_sl_no_seq")
    op.execute("DROP SEQUENCE IF EXISTS messages_sl_no_seq")
    op.execute("DROP SEQUENCE IF EXISTS triage_threads_sl_no_seq")
    op.execute("DROP SEQUENCE IF EXISTS patients_sl_no_seq")
    op.execute("DROP SEQUENCE IF EXISTS user_tokens_sl_no_seq")
    op.execute("DROP SEQUENCE IF EXISTS users_sl_no_seq")

