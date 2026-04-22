"""Pydantic schemas for RAG."""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class ICD10IngestRequest(BaseModel):
    """ICD-10 corpus ingestion request."""
    
    documents: List[Dict[str, Any]] = Field(
        ...,
        description="List of ICD-10 documents with code, description, category"
    )


class ICD10Document(BaseModel):
    """ICD-10 document for ingestion."""
    
    code: str = Field(..., description="ICD-10 code (e.g., 'J06.9')")
    description: str = Field(..., description="Code description")
    category: Optional[str] = Field(None, description="Code category")
    long_description: Optional[str] = Field(None, description="Extended description")


class SearchRequest(BaseModel):
    """RAG search request."""
    
    query: str = Field(..., min_length=1, description="Search query text")
    corpus_type: str = Field(default="icd10", description="Corpus to search")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results")


class SearchResult(BaseModel):
    """Single search result."""
    
    id: str
    text: str
    metadata: Dict[str, Any]
    similarity: float


class SearchResponse(BaseModel):
    """RAG search response."""
    
    success: bool = True
    data: List[SearchResult]


class IngestResponse(BaseModel):
    """Corpus ingestion response."""
    
    success: bool = True
    message: str
    documents_ingested: int

