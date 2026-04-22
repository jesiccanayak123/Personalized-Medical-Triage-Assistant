"""RAG service for vector search and retrieval."""

from typing import Dict, Any, List, Optional

from database.dao.rag_documents import RAGDocumentsDao
from integrations.openai.client import OpenAIClient
from global_utils.exceptions import ServiceError
from config.settings import settings


class RAGService:
    """Service class for RAG operations."""

    def __init__(
        self,
        rag_dao: RAGDocumentsDao,
        openai_client: Optional[OpenAIClient] = None,
    ):
        """Initialize RAGService.
        
        Args:
            rag_dao: RAG documents DAO
            openai_client: OpenAI client for embeddings
        """
        self.rag_dao = rag_dao
        self.openai_client = openai_client or OpenAIClient()

    async def ingest_icd10(
        self,
        documents: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Ingest ICD-10 documents into the vector store.
        
        Args:
            documents: List of ICD-10 documents with code, description
            
        Returns:
            Ingestion result
        """
        ingested_count = 0
        errors = []

        for doc in documents:
            try:
                # Build text for embedding
                code = doc.get("code", "")
                description = doc.get("description", "")
                long_desc = doc.get("long_description", "")
                category = doc.get("category", "")
                
                text = f"{code}: {description}"
                if long_desc:
                    text += f". {long_desc}"
                if category:
                    text += f" (Category: {category})"

                # Generate embedding
                embedding = await self.openai_client.get_embedding(text)

                # Store document
                await self.rag_dao.create_document(
                    corpus_type="icd10",
                    text=text,
                    embedding=embedding,
                    metadata={
                        "code": code,
                        "description": description,
                        "category": category,
                        "long_description": long_desc,
                    },
                )
                ingested_count += 1

            except Exception as e:
                errors.append({"code": doc.get("code"), "error": str(e)})

        return {
            "success": True,
            "message": f"Ingested {ingested_count} documents",
            "documents_ingested": ingested_count,
            "errors": errors if errors else None,
        }

    async def search(
        self,
        query: str,
        corpus_type: str = "icd10",
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """Search for similar documents.
        
        Args:
            query: Search query text
            corpus_type: Corpus to search
            top_k: Number of results
            
        Returns:
            List of similar documents
        """
        # Generate query embedding
        query_embedding = await self.openai_client.get_embedding(query)

        # Search similar documents
        results = await self.rag_dao.search_similar(
            embedding=query_embedding,
            corpus_type=corpus_type,
            top_k=top_k,
            threshold=0.5,  # Lower threshold for broader results
        )

        # Format results
        formatted_results = []
        for doc in results:
            formatted_results.append({
                "id": doc["id"],
                "text": doc["text"],
                "metadata": doc.get("metadata_json", {}),
                "similarity": doc["similarity"],
            })

        return {
            "success": True,
            "data": formatted_results,
        }

    async def get_icd10_candidates(
        self,
        symptoms_text: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get ICD-10 code candidates for given symptoms.
        
        This is the main retrieval method used by the Medical Coder agent.
        
        Args:
            symptoms_text: Text describing patient symptoms
            top_k: Number of candidates to retrieve
            
        Returns:
            List of ICD-10 candidates with scores
        """
        result = await self.search(
            query=symptoms_text,
            corpus_type="icd10",
            top_k=top_k,
        )
        
        return result.get("data", [])

    async def get_corpus_stats(self, corpus_type: str) -> Dict[str, Any]:
        """Get statistics for a corpus.
        
        Args:
            corpus_type: Type of corpus
            
        Returns:
            Corpus statistics
        """
        count = await self.rag_dao.count_by_corpus(corpus_type)
        
        return {
            "success": True,
            "data": {
                "corpus_type": corpus_type,
                "document_count": count,
            }
        }

    async def delete_corpus(self, corpus_type: str) -> Dict[str, Any]:
        """Delete all documents in a corpus.
        
        Args:
            corpus_type: Type of corpus
            
        Returns:
            Deletion result
        """
        deleted = await self.rag_dao.delete_corpus(corpus_type)
        
        return {
            "success": True,
            "message": f"Deleted {deleted} documents from {corpus_type} corpus",
        }

