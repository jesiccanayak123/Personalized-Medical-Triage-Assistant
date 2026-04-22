"""LangGraph workflow definition for medical triage."""

from typing import Dict, Any, List, Optional
import asyncio

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from agents.state import TriageState, create_initial_state
from agents.nodes.interviewer import interviewer_node
from agents.nodes.risk_assessor import risk_assessor_node
from agents.nodes.medical_coder import medical_coder_node
from agents.nodes.scribe import scribe_node
from modules.triage.schemas import (
    TriageStatus,
    InterviewerOutput,
    RiskAssessmentOutput,
    ICD10CodingOutput,
    SOAPNoteOutput,
)
from config.logging import logger


def should_interrupt(state: TriageState) -> str:
    """Check if we should interrupt for emergency.
    
    Args:
        state: Current state
        
    Returns:
        Next node or END
    """
    if state.get("should_interrupt"):
        return "emergency_response"
    return "continue"


def after_interview(state: TriageState) -> str:
    """Determine next step after interviewer.
    
    Args:
        state: Current state
        
    Returns:
        Next node name
    """
    interviewer_output = state.get("interviewer_output")
    
    if interviewer_output and interviewer_output.is_done:
        return "medical_coder"
    
    # Continue interviewing
    return END


def after_risk_check(state: TriageState) -> str:
    """Determine next step after risk assessment.
    
    Args:
        state: Current state
        
    Returns:
        Next node name or END
    """
    if state.get("should_interrupt"):
        return END  # Emergency - return immediately
    
    return "interviewer"


def build_triage_graph() -> StateGraph:
    """Build the LangGraph state graph for triage workflow.
    
    Workflow:
    1. On each user message: Risk Assessor + Interviewer run
    2. If emergency detected: immediate EMERGENCY response
    3. If interview complete: Medical Coder -> Scribe -> DONE
    4. Else: return interviewer's next question
    
    Returns:
        Compiled StateGraph
    """
    graph = StateGraph(TriageState)
    
    # Add nodes
    graph.add_node("risk_assessor", risk_assessor_node)
    graph.add_node("interviewer", interviewer_node)
    graph.add_node("medical_coder", medical_coder_node)
    graph.add_node("scribe", scribe_node)
    
    # Entry point - always check risk first
    graph.set_entry_point("risk_assessor")
    
    # From risk assessor: check for emergency or continue to interviewer
    graph.add_conditional_edges(
        "risk_assessor",
        after_risk_check,
        {
            "interviewer": "interviewer",
            END: END,
        }
    )
    
    # From interviewer: check if done or return
    graph.add_conditional_edges(
        "interviewer",
        after_interview,
        {
            "medical_coder": "medical_coder",
            END: END,
        }
    )
    
    # Medical coder -> Scribe
    graph.add_edge("medical_coder", "scribe")
    
    # Scribe -> END
    graph.add_edge("scribe", END)
    
    return graph.compile()


class TriageGraph:
    """High-level interface for running the triage graph."""
    
    def __init__(self, rag_dao=None):
        """Initialize the triage graph.
        
        Args:
            rag_dao: Optional RAG documents DAO for medical coder
        """
        self.graph = build_triage_graph()
        self.rag_dao = rag_dao
    
    async def run(
        self,
        thread_id: str,
        user_id: str,
        patient_id: str = None,
        messages: List[Dict[str, Any]] = None,
        intake_data: Dict[str, Any] = None,
        user_message: str = None,
    ) -> Dict[str, Any]:
        """Run the triage workflow.
        
        Args:
            thread_id: Thread ID
            user_id: User ID
            patient_id: Patient ID
            messages: Existing conversation messages
            intake_data: Existing intake data
            user_message: New user message
            
        Returns:
            Result dict with agent outputs and updated state
        """
        # Convert messages to LangChain format
        lc_messages = []
        if messages:
            for msg in messages:
                if isinstance(msg, dict):
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "user":
                        lc_messages.append(HumanMessage(content=content))
                    else:
                        lc_messages.append(AIMessage(content=content))
                else:
                    lc_messages.append(msg)
        
        # Add new user message
        if user_message:
            lc_messages.append(HumanMessage(content=user_message))
        
        # Create initial state
        initial_state = create_initial_state(
            thread_id=thread_id,
            user_id=user_id,
            patient_id=patient_id or "",
            intake_data=intake_data,
        )
        initial_state["messages"] = lc_messages
        
        # Run the graph
        try:
            result = await self.graph.ainvoke(initial_state)
            
            logger.info(
                "Triage graph completed",
                thread_id=thread_id,
                status=result.get("status"),
                is_done=result.get("interviewer_output", {}).is_done if result.get("interviewer_output") else False,
            )
            
            return {
                "status": result.get("status", TriageStatus.INTERVIEWING.value),
                "interviewer_output": result.get("interviewer_output"),
                "risk_output": result.get("risk_output"),
                "icd10_output": result.get("icd10_output"),
                "soap_output": result.get("soap_output"),
                "intake_data": self._merge_intake_data(
                    intake_data or {},
                    result.get("interviewer_output"),
                ),
                "missing_fields": result.get("missing_fields", []),
                "should_interrupt": result.get("should_interrupt", False),
            }
            
        except Exception as e:
            logger.error(f"Triage graph error: {e}")
            raise
    
    def _merge_intake_data(
        self,
        existing: Dict[str, Any],
        interviewer_output: Optional[InterviewerOutput],
    ) -> Dict[str, Any]:
        """Merge existing intake data with new captured updates.
        
        Args:
            existing: Existing intake data
            interviewer_output: Interviewer output with captured_updates
            
        Returns:
            Merged intake data
        """
        result = dict(existing)
        
        if interviewer_output and interviewer_output.captured_updates:
            result.update(interviewer_output.captured_updates)
        
        return result


# Global graph instance
_triage_graph: Optional[TriageGraph] = None


def get_triage_graph(rag_dao=None) -> TriageGraph:
    """Get or create the global triage graph.
    
    Args:
        rag_dao: Optional RAG DAO
        
    Returns:
        TriageGraph instance
    """
    global _triage_graph
    
    if _triage_graph is None:
        _triage_graph = TriageGraph(rag_dao=rag_dao)
    
    return _triage_graph

