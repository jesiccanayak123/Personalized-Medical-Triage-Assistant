"""Medical Coder agent node - maps symptoms to ICD-10 codes."""

import json
from typing import Dict, Any, List

from agents.state import TriageState
from agents.prompts import MEDICAL_CODER_SYSTEM_PROMPT
from modules.triage.schemas import ICD10CodingOutput, ICD10Code
from modules.rag.service import RAGService
from database.dao.rag_documents import RAGDocumentsDao
from integrations.openai.client import OpenAIClient
from config.logging import logger


async def medical_coder_node(state: TriageState, rag_dao: RAGDocumentsDao = None) -> Dict[str, Any]:
    """Medical Coder agent - maps symptoms to ICD-10 codes using RAG.
    
    Only runs after interview is complete.
    MUST only select codes from retrieved candidates.
    
    Args:
        state: Current triage state
        rag_dao: RAG documents DAO for vector search
        
    Returns:
        Updated state with icd10_output
    """
    client = OpenAIClient()
    
    # Build interview summary
    intake_data = state["intake_data"]
    interview_summary = f"""
Chief Complaint: {intake_data.get('symptoms', 'Not specified')}
Duration: {intake_data.get('duration', 'Not specified')}
Severity: {intake_data.get('severity', 'Not specified')}/10
Location: {intake_data.get('location', 'Not specified')}
Associated Symptoms: {intake_data.get('associated_symptoms', 'None reported')}
Medical History: {intake_data.get('medical_history', 'Not provided')}
Medications: {intake_data.get('medications', 'None')}
Allergies: {intake_data.get('allergies', 'None')}
"""
    
    # Get ICD-10 candidates via RAG
    candidates = []
    if rag_dao:
        try:
            rag_service = RAGService(rag_dao=rag_dao)
            candidates = await rag_service.get_icd10_candidates(
                symptoms_text=interview_summary,
                top_k=15,
            )
        except Exception as e:
            logger.error(f"RAG retrieval error: {e}")
    
    # If no RAG results, use a default set (fallback)
    if not candidates:
        candidates = [
            {
                "text": "R10.9: Unspecified abdominal pain",
                "metadata": {"code": "R10.9", "description": "Unspecified abdominal pain"},
            },
            {
                "text": "R51.9: Headache, unspecified",
                "metadata": {"code": "R51.9", "description": "Headache, unspecified"},
            },
            {
                "text": "R05: Cough",
                "metadata": {"code": "R05", "description": "Cough"},
            },
            {
                "text": "J06.9: Acute upper respiratory infection, unspecified",
                "metadata": {"code": "J06.9", "description": "Acute upper respiratory infection, unspecified"},
            },
        ]
    
    # Format candidates for prompt
    candidates_text = "\n".join([
        f"- {c.get('text', '')} (similarity: {c.get('similarity', 'N/A')})"
        for c in candidates
    ])
    
    system_prompt = MEDICAL_CODER_SYSTEM_PROMPT.format(
        interview_summary=interview_summary,
        candidates=candidates_text,
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Select the appropriate ICD-10 codes from the candidates."},
    ]
    
    try:
        output = await client.structured_output(
            messages=messages,
            response_model=ICD10CodingOutput,
            temperature=0.2,  # Low temperature for accurate coding
        )
        
        # Validate that all codes come from candidates
        candidate_codes = {
            c.get("metadata", {}).get("code", "") 
            for c in candidates
        }
        
        validated_codes = []
        for code in output.codes:
            if code.icd10 in candidate_codes or len(candidate_codes) == 0:
                validated_codes.append(code)
            else:
                logger.warning(f"Code {code.icd10} not in candidates, skipping")
        
        output.codes = validated_codes
        
        logger.info(
            "Medical coding completed",
            codes=[c.icd10 for c in output.codes],
        )
        
        return {
            "icd10_output": output,
        }
        
    except Exception as e:
        logger.error(f"Medical Coder error: {e}")
        
        # Return empty result
        return {
            "icd10_output": ICD10CodingOutput(codes=[]),
        }

