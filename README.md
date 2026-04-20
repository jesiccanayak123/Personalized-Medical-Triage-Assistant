# Personalized-Medical-Triage-Assistant
An empathetic multi-agent healthcare assistant that conducts structured patient interviews using reflective listening, maps symptoms to ICD-10 codes, assesses emergency risks in real time, and generates EHR-ready SOAP notes—ensuring early detection of critical conditions and improved clinical accuracy.

# Core Requirements
Architecture: Must use a multi-agent framework (LangGraph, CrewAI, or AutoGen).

Validation: All agent outputs must be structured (JSON/Pydantic models), not free text.

Memory: Must implement "Short-term" (thread state) and "Long-term" (Vector DB/SQL/Document DB) memory.

UI: All projects must have a login page, interactive UI and a chat interface. Use React framework for frontend.

RAG & MCP Servers: Feel free to integrate RAG, Function/Tool calling and MCP as per use case.

Test Coverage: Should be more than 80%

Docker: Use dockerfile for running for microservice.

Domain: Healthcare Problem: Patients often struggle to articulate symptoms, leading to misdirection in hospitals. 

Objective: An empathetic agent interface that conducts a preliminary medical interview and prepares a summary for the doctor.

Agent 1: The Interviewer. Uses "Reflective Listening" techniques. It asks one question at a time to gather symptoms, duration, and severity. It stops when it has enough info.

Agent 2: The Medical Coder. Analyzes the conversation and maps symptoms to standard ICD-10 codes (e.g., "Headache" -> "R51").

Agent 3: The Risk Assessor. Checks against a rules engine. If symptoms indicate "Heart Attack" or "Stroke," it triggers an immediate "EMERGENCY" override flag.

Agent 4: The Scribe. Generates a SOAP Note (Subjective, Objective, Assessment, Plan) formatted specifically for Electronic Health Records (EHR).
Agentic Solution: Implement Guardrails. The Risk Assessor must run in parallel to the Interviewer. If the Risk Assessor detects "red flag" keywords (chest pain, numbness), it must interrupt the flow immediately to direct the user to Emergency Services.

