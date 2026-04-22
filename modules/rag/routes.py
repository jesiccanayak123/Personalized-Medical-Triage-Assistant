"""RAG API routes."""

from fastapi import APIRouter, Depends, HTTPException

from modules.rag.schemas import (
    ICD10IngestRequest,
    SearchRequest,
    SearchResponse,
    IngestResponse,
)
from modules.rag.service import RAGService
from database.dao.rag_documents import RAGDocumentsDao
from app.dependencies import get_rag_documents_dao, get_current_user
from global_utils.exceptions import AppException


router = APIRouter(prefix="/rag", tags=["RAG"])


def get_rag_service(
    rag_dao: RAGDocumentsDao = Depends(get_rag_documents_dao),
) -> RAGService:
    """Get RAGService instance."""
    return RAGService(rag_dao=rag_dao)


@router.post("/ingest/icd10", response_model=IngestResponse)
async def ingest_icd10(
    payload: ICD10IngestRequest,
    current_user: dict = Depends(get_current_user),
    service: RAGService = Depends(get_rag_service),
):
    """Ingest ICD-10 documents into the vector store.
    
    Accepts a list of ICD-10 codes with descriptions and generates
    embeddings for vector search.
    """
    try:
        return await service.ingest_icd10(documents=payload.documents)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/search", response_model=SearchResponse)
async def search(
    payload: SearchRequest,
    current_user: dict = Depends(get_current_user),
    service: RAGService = Depends(get_rag_service),
):
    """Search the RAG corpus.
    
    Performs semantic search over the specified corpus.
    """
    try:
        return await service.search(
            query=payload.query,
            corpus_type=payload.corpus_type,
            top_k=payload.top_k,
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/corpus/{corpus_type}/stats")
async def get_corpus_stats(
    corpus_type: str,
    current_user: dict = Depends(get_current_user),
    service: RAGService = Depends(get_rag_service),
):
    """Get statistics for a corpus."""
    try:
        return await service.get_corpus_stats(corpus_type=corpus_type)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete("/corpus/{corpus_type}")
async def delete_corpus(
    corpus_type: str,
    current_user: dict = Depends(get_current_user),
    service: RAGService = Depends(get_rag_service),
):
    """Delete all documents in a corpus."""
    try:
        return await service.delete_corpus(corpus_type=corpus_type)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

