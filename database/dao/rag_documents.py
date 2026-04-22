"""RAG Documents DAO with pgvector support."""

from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database.base_dao import BasePostgresDao, generate_objectid
from database.models import RAGDocument
from config.settings import settings


class RAGDocumentsDao(BasePostgresDao):
    """Data Access Object for rag_documents table with vector search."""

    model = RAGDocument

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_document(
        self,
        corpus_type: str,
        text: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new RAG document with embedding.
        
        Args:
            corpus_type: Type of corpus (e.g., 'icd10')
            text: Document text content
            embedding: Vector embedding
            metadata: Optional metadata dict
            
        Returns:
            Inserted document ID
        """
        doc_data = {
            "corpus_type": corpus_type,
            "text": text,
            "embedding": embedding,
            "metadata_json": metadata or {},
        }
        return await self.insert_one(doc_data)

    async def bulk_create_documents(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[str]:
        """Bulk create RAG documents.
        
        Args:
            documents: List of document dicts with corpus_type, text, embedding, metadata_json
            
        Returns:
            List of inserted document IDs
        """
        ids = []
        for doc in documents:
            doc_id = await self.create_document(
                corpus_type=doc["corpus_type"],
                text=doc["text"],
                embedding=doc["embedding"],
                metadata=doc.get("metadata_json", {}),
            )
            ids.append(doc_id)
        return ids

    async def search_similar(
        self,
        embedding: List[float],
        corpus_type: Optional[str] = None,
        top_k: int = None,
        threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using cosine similarity.
        
        Args:
            embedding: Query embedding vector
            corpus_type: Optional filter by corpus type
            top_k: Number of results to return
            threshold: Minimum similarity threshold (0-1)
            
        Returns:
            List of similar documents with similarity scores
        """
        top_k = top_k or settings.vector_top_k
        
        # Build query with pgvector cosine distance
        # Note: pgvector uses distance, so we convert to similarity
        query = """
            SELECT 
                id, corpus_type, text, metadata_json, created_at,
                1 - (embedding <=> :embedding::vector) as similarity
            FROM rag_documents
            WHERE 1 - (embedding <=> :embedding::vector) >= :threshold
        """
        
        if corpus_type:
            query += " AND corpus_type = :corpus_type"
        
        query += " ORDER BY similarity DESC LIMIT :top_k"
        
        params = {
            "embedding": str(embedding),
            "threshold": threshold,
            "top_k": top_k,
        }
        if corpus_type:
            params["corpus_type"] = corpus_type
        
        result = await self._session.execute(text(query), params)
        rows = result.fetchall()
        
        documents = []
        for row in rows:
            documents.append({
                "id": row[0],
                "corpus_type": row[1],
                "text": row[2],
                "metadata_json": row[3],
                "created_at": row[4],
                "similarity": float(row[5]),
            })
        
        return documents

    async def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document data or None
        """
        return await self.find_one({"id": doc_id})

    async def get_documents_by_corpus(
        self,
        corpus_type: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get all documents for a corpus type.
        
        Args:
            corpus_type: Type of corpus
            skip: Number to skip
            limit: Maximum to return
            
        Returns:
            List of documents
        """
        return await self.find_many(
            filters={"corpus_type": corpus_type},
            skip=skip,
            limit=limit,
        )

    async def count_by_corpus(self, corpus_type: str) -> int:
        """Count documents in a corpus.
        
        Args:
            corpus_type: Type of corpus
            
        Returns:
            Document count
        """
        return await self.count({"corpus_type": corpus_type})

    async def delete_corpus(self, corpus_type: str) -> int:
        """Delete all documents in a corpus.
        
        Args:
            corpus_type: Type of corpus
            
        Returns:
            Number of deleted documents
        """
        return await self.delete_many({"corpus_type": corpus_type})

    async def update_embedding(
        self,
        doc_id: str,
        embedding: List[float],
    ) -> int:
        """Update document embedding.
        
        Args:
            doc_id: Document ID
            embedding: New embedding vector
            
        Returns:
            Number of modified records
        """
        return await self.update_one(
            {"id": doc_id},
            {"embedding": embedding}
        )

