# Medical Triage Assistant - Complete Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Features Implemented](#features-implemented)
5. [Project Structure](#project-structure)
6. [Setup Guide](#setup-guide)
7. [Running the Project](#running-the-project)
8. [API Documentation](#api-documentation)
9. [Database Schema](#database-schema)
10. [LangGraph Agent Workflow](#langgraph-agent-workflow)
11. [Frontend Guide](#frontend-guide)
12. [Testing](#testing)
13. [Troubleshooting](#troubleshooting)

---

## Project Overview

The **Personalized Medical Triage Assistant** is an AI-powered medical triage system that uses multiple AI agents to:
- Conduct patient interviews
- Assess medical risk levels
- Generate ICD-10 diagnostic codes
- Create SOAP (Subjective, Objective, Assessment, Plan) notes

The system provides a modern React frontend with a chat interface for patient interactions and a dashboard for healthcare providers.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐│
│  │  Login   │  │Dashboard │  │ Patients │  │   Triage Chat    ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘│
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTP/REST API
┌─────────────────────────────▼───────────────────────────────────┐
│                     Backend (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Routes/Views Layer                     │  │
│  │  auth_routes │ patient_routes │ triage_routes │ dashboard │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│  ┌──────────────────────────▼───────────────────────────────┐  │
│  │                    Services Layer                         │  │
│  │  AuthService │ PatientService │ TriageService │ Dashboard │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│  ┌──────────────────────────▼───────────────────────────────┐  │
│  │                      DAO Layer                            │  │
│  │  UsersDao │ PatientsDao │ ThreadsDao │ MessagesDao │ etc  │  │
│  └──────────────────────────┬───────────────────────────────┘  │
└─────────────────────────────┼───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                    LangGraph Agents                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐ │
│  │Interviewer │  │   Risk     │  │  Medical   │  │   Scribe  │ │
│  │   Agent    │  │  Assessor  │  │   Coder    │  │   Agent   │ │
│  └────────────┘  └────────────┘  └────────────┘  └───────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                     PostgreSQL + pgvector                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐│
│  │  users   │  │ patients │  │ threads  │  │ rag_embeddings   ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Backend
- **Python 3.11+** - Core programming language
- **FastAPI** - High-performance web framework
- **SQLAlchemy** - ORM for database operations
- **Alembic** - Database migrations
- **LangGraph** - Multi-agent orchestration framework
- **OpenAI API** - LLM for agent intelligence
- **pgvector** - Vector similarity search for RAG
- **Pydantic** - Data validation and serialization
- **structlog** - Structured logging

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Zustand** - State management
- **React Query** - Data fetching and caching
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Lucide React** - Icon library

### Database
- **PostgreSQL 15+** - Primary database
- **pgvector extension** - Vector similarity search

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration

---

## Features Implemented

### 1. Authentication Module
- User registration with email/password
- Login with JWT token authentication
- Logout with token invalidation
- Password hashing with bcrypt
- Session management

### 2. Patient Management
- Create new patients
- List all patients (user-scoped)
- View patient details
- Update patient information
- Patient search functionality

### 3. Triage System (Core Feature)
- Create triage threads for patients
- Real-time chat interface
- Multi-agent AI processing:
  - **Interviewer Agent**: Conducts patient interviews
  - **Risk Assessor Agent**: Evaluates medical urgency
  - **Medical Coder Agent**: Assigns ICD-10 codes
  - **Scribe Agent**: Generates SOAP notes
- Emergency detection with immediate alerts
- Structured output validation

### 4. Dashboard
- Patient statistics (total, active, emergencies)
- Recent patient activity
- Triage status overview
- Weekly completion metrics

### 5. RAG System (ICD-10)
- Vector embeddings for ICD-10 codes
- Semantic search for diagnosis matching
- Top-k candidate retrieval

### 6. Dark/Light Mode
- Persistent theme preference
- Smooth transitions
- System-wide theming

---

## Project Structure

```
personal_project/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   └── dependencies.py      # Dependency injection
├── agents/
│   ├── __init__.py
│   ├── graph.py             # LangGraph workflow definition
│   ├── state.py             # Agent state management
│   ├── prompts.py           # System prompts for agents
│   ├── rules_engine.py      # Deterministic rules for risk assessment
│   └── nodes/
│       ├── interviewer.py   # Interviewer agent node
│       ├── risk_assessor.py # Risk assessment node
│       ├── medical_coder.py # ICD-10 coding node
│       └── scribe.py        # SOAP note generation node
├── config/
│   ├── __init__.py
│   └── settings.py          # Application configuration
├── database/
│   ├── __init__.py
│   ├── engine.py            # SQLAlchemy engine setup
│   ├── base_dao.py          # Base DAO class
│   ├── connection_manager.py # Database connection management
│   └── models/
│       ├── user.py
│       ├── patient.py
│       ├── triage_thread.py
│       ├── message.py
│       ├── artifact.py
│       └── rag.py
├── integrations/
│   └── openai/
│       ├── __init__.py
│       └── client.py        # OpenAI API wrapper
├── modules/
│   ├── auth/
│   │   ├── routes.py
│   │   ├── service.py
│   │   ├── schemas.py
│   │   ├── dao.py
│   │   └── utils.py
│   ├── patients/
│   │   ├── routes.py
│   │   ├── service.py
│   │   ├── schemas.py
│   │   └── dao.py
│   ├── triage/
│   │   ├── routes.py
│   │   ├── service.py
│   │   ├── schemas.py
│   │   └── dao.py
│   ├── dashboard/
│   │   ├── routes.py
│   │   ├── service.py
│   │   └── schemas.py
│   └── rag/
│       ├── routes.py
│       ├── service.py
│       └── dao.py
├── migrations/
│   ├── versions/            # Alembic migration files
│   ├── env.py
│   └── script.py.mako
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_rules_engine.py
│   │   ├── test_schemas.py
│   │   ├── test_dao.py
│   │   └── test_auth_utils.py
│   └── integration/
│       ├── test_auth_flow.py
│       ├── test_patient_crud.py
│       ├── test_triage_flow.py
│       └── test_dashboard.py
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── index.css
│   │   ├── vite-env.d.ts
│   │   ├── api/
│   │   │   └── client.ts
│   │   ├── components/
│   │   │   └── Layout.tsx
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── PatientsPage.tsx
│   │   │   ├── PatientDetailPage.tsx
│   │   │   └── TriageChatPage.tsx
│   │   └── store/
│   │       ├── auth.ts
│   │       └── theme.ts
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── Dockerfile
├── scripts/
│   ├── run_tests.sh
│   └── setup_dev.sh
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── env.example
├── alembic.ini
├── pytest.ini
├── pyproject.toml
└── README.md
```

---

## Setup Guide

### Prerequisites

Before setting up the project, ensure you have the following installed:

- **Python 3.11+**: [Download Python](https://www.python.org/downloads/)
- **Node.js 18+**: [Download Node.js](https://nodejs.org/)
- **Docker & Docker Compose**: [Download Docker](https://www.docker.com/get-started)
- **Git**: [Download Git](https://git-scm.com/)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd personal_project
```

### Step 2: Environment Configuration

Create the environment file from the example:

```bash
cp env.example .env
```

Edit `.env` and configure the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://triage:triage_password@localhost:5433/medical_triage

# OpenAI Configuration (Required for AI features)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRY_DAYS=15

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000

# Logging
LOG_LEVEL=INFO
```

### Step 3: Start PostgreSQL with Docker

```bash
# Start the PostgreSQL database with pgvector
docker-compose up -d postgres
```

This starts PostgreSQL on port **5433** (to avoid conflicts with local PostgreSQL).

Verify the database is running:

```bash
docker-compose ps
```

### Step 4: Backend Setup

```bash
# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install psycopg2 for Alembic migrations
pip install psycopg2-binary
```

### Step 5: Run Database Migrations

```bash
# Run Alembic migrations to create database tables
alembic upgrade head
```

### Step 6: Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Return to project root
cd ..
```

### Step 7: Seed ICD-10 Data for RAG (Required for Medical Coding)

The RAG system requires ICD-10 codes to be loaded into pgvector for semantic search:

```bash
# Make sure you're in the project root with venv activated
source venv/bin/activate

# Ensure OPENAI_API_KEY is set (needed for generating embeddings)
export OPENAI_API_KEY=your_openai_api_key_here

# Run the seeding script
python scripts/seed_icd10.py
```

This script will:
- Load 62 common ICD-10 codes from `scripts/seed_icd10_data.json`
- Generate embeddings using OpenAI's embedding model
- Store the vectors in pgvector for semantic search
- Test the search functionality

**Note**: The seeding takes a few minutes due to embedding generation. You only need to run this once.

---

## Running the Project

### Option 1: Run Locally (Development Mode)

#### Terminal 1 - Start Backend

```bash
# Activate virtual environment
source venv/bin/activate

# Start the FastAPI server
python -m app.main
```

The backend will be available at: `http://localhost:8000`

#### Terminal 2 - Start Frontend

```bash
# Navigate to frontend directory
cd frontend

# Start the Vite development server
npm run dev
```

The frontend will be available at: `http://localhost:3000`

### Option 2: Run with Docker Compose (Production-like)

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

Services will be available at:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

### Stopping the Services

```bash
# Stop Docker services
docker-compose down

# Stop with volume removal (deletes database data)
docker-compose down -v
```

---

## API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | User login |
| POST | `/api/v1/auth/logout` | User logout |
| GET | `/api/v1/auth/me` | Get current user |

### Patient Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/patients` | Create patient |
| GET | `/api/v1/patients` | List patients |
| GET | `/api/v1/patients/{id}` | Get patient details |
| PUT | `/api/v1/patients/{id}` | Update patient |

### Triage Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/triage/threads` | Create triage thread |
| GET | `/api/v1/triage/threads` | List triage threads |
| GET | `/api/v1/triage/threads/{id}` | Get thread details |
| POST | `/api/v1/triage/threads/{id}/messages` | Send message |
| GET | `/api/v1/triage/threads/{id}/messages` | Get messages |
| GET | `/api/v1/triage/threads/{id}/artifacts` | Get artifacts (SOAP, ICD-10) |

### Dashboard Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/dashboard/summary` | Get dashboard statistics |
| GET | `/api/v1/dashboard/patients` | Get patients with triage info |

### Interactive API Documentation

Access the Swagger UI documentation at: `http://localhost:8000/docs`

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    last_login_at TIMESTAMP
);
```

### Patients Table
```sql
CREATE TABLE patients (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(20),
    phone VARCHAR(20),
    email VARCHAR(255),
    medical_record_number VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

### Triage Threads Table
```sql
CREATE TABLE triage_threads (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    patient_id UUID REFERENCES patients(id),
    status VARCHAR(20) DEFAULT 'INTERVIEWING',
    chief_complaint TEXT,
    intake_data JSONB,
    missing_fields JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### Messages Table
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    thread_id UUID REFERENCES triage_threads(id),
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Artifacts Table
```sql
CREATE TABLE artifacts (
    id UUID PRIMARY KEY,
    thread_id UUID REFERENCES triage_threads(id),
    artifact_type VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### RAG Embeddings Table
```sql
CREATE TABLE rag_embeddings (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES rag_documents(id),
    chunk_text TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## LangGraph Agent Workflow

### Agent Descriptions

#### 1. Interviewer Agent
- **Purpose**: Conducts patient-facing medical interviews
- **Behavior**: 
  - Asks one question at a time
  - Uses reflective listening techniques
  - Captures structured intake data
  - Determines when sufficient information is gathered

#### 2. Risk Assessor Agent
- **Purpose**: Evaluates medical risk and urgency
- **Behavior**:
  - Runs on every user message
  - Checks for red-flag symptoms
  - Can trigger emergency interruption
  - Returns disposition (emergency, urgent, routine)

#### 3. Medical Coder Agent
- **Purpose**: Assigns ICD-10 diagnostic codes
- **Behavior**:
  - Uses RAG over ICD-10 corpus
  - Returns top candidates with confidence scores
  - Includes evidence and source references

#### 4. Scribe Agent
- **Purpose**: Generates clinical documentation
- **Behavior**:
  - Creates structured SOAP notes
  - Includes all captured data
  - Formats for clinical use

### Workflow Diagram

```
                    ┌─────────────────┐
                    │   User Input    │
                    └────────┬────────┘
                             │
              ┌──────────────▼──────────────┐
              │      Risk Assessor          │
              │  (runs on every message)    │
              └──────────────┬──────────────┘
                             │
              ┌──────────────▼──────────────┐
              │     Emergency Check         │
              │   (emergency=true?)         │
              └──────────────┬──────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │ YES               │ NO                │
         ▼                   ▼                   │
┌─────────────────┐  ┌─────────────────┐        │
│  EMERGENCY      │  │   Interviewer   │        │
│  Response       │  │     Agent       │        │
│  (interrupt)    │  └────────┬────────┘        │
└─────────────────┘           │                 │
                              │                 │
              ┌───────────────▼───────────────┐ │
              │      Interview Done?          │ │
              └───────────────┬───────────────┘ │
                              │                 │
         ┌────────────────────┼─────────────────┤
         │ YES                │ NO              │
         ▼                    ▼                 │
┌─────────────────┐  ┌─────────────────┐        │
│ Medical Coder   │  │ Return next     │        │
│    Agent        │  │   question      │◄───────┘
└────────┬────────┘  └─────────────────┘
         │
         ▼
┌─────────────────┐
│  Scribe Agent   │
│ (SOAP Note)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   DONE          │
│  (complete)     │
└─────────────────┘
```

### State Structure

```python
class TriageState(TypedDict):
    thread_id: str
    user_id: str
    patient_id: str
    messages: List[Dict[str, str]]
    intake_data: Dict[str, Any]
    status: str  # INTERVIEWING, CODING, SCRIBING, DONE, EMERGENCY
    interviewer_output: Optional[InterviewerOutput]
    risk_output: Optional[RiskAssessmentOutput]
    icd10_output: Optional[ICD10CodingOutput]
    soap_output: Optional[SOAPNoteOutput]
    missing_fields: List[str]
    completion_reason: Optional[str]
    should_interrupt: bool
```

---

## Frontend Guide

### Pages

| Page | Route | Description |
|------|-------|-------------|
| Login | `/login` | User authentication |
| Dashboard | `/dashboard` | Overview and statistics |
| Patients | `/patients` | Patient list and creation |
| Patient Detail | `/patients/:id` | Patient info and triage history |
| Triage Chat | `/triage/:threadId` | Chat interface for triage |

### State Management

The frontend uses **Zustand** for state management:

#### Auth Store (`store/auth.ts`)
```typescript
interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (user: User, token: string) => void
  logout: () => void
}
```

#### Theme Store (`store/theme.ts`)
```typescript
interface ThemeState {
  theme: 'light' | 'dark'
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
}
```

### Styling

The frontend uses **Tailwind CSS** with custom CSS variables for theming:

```css
/* Light theme (default) */
:root {
  --color-bg-primary: #f8fafc;
  --color-text-primary: #0f172a;
  /* ... */
}

/* Dark theme */
.dark {
  --color-bg-primary: #0a0f1a;
  --color-text-primary: #f9fafb;
  /* ... */
}
```

---

## Testing

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests with coverage
pytest --cov=. --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_rules_engine.py

# Run with verbose output
pytest -v

# Run integration tests only
pytest tests/integration/
```

### Test Coverage

The project targets **>80% code coverage**. View the HTML coverage report at `htmlcov/index.html` after running tests.

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── unit/
│   ├── test_rules_engine.py    # Rules engine unit tests
│   ├── test_schemas.py         # Pydantic schema tests
│   ├── test_dao.py             # DAO unit tests
│   └── test_auth_utils.py      # Auth utility tests
└── integration/
    ├── test_auth_flow.py       # Auth API tests
    ├── test_patient_crud.py    # Patient CRUD tests
    ├── test_triage_flow.py     # Triage workflow tests
    └── test_dashboard.py       # Dashboard API tests
```

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Problem**: `Port 8000 is already in use` or `Port 3000 is already in use`

**Solution**:
```bash
# Find and kill process on port 8000
lsof -ti :8000 | xargs kill -9

# Find and kill process on port 3000
lsof -ti :3000 | xargs kill -9
```

#### 2. Database Connection Failed

**Problem**: `connection to server at "localhost" port 5432 failed`

**Solution**: The project uses port **5433** for PostgreSQL to avoid conflicts:
```bash
# Check if postgres container is running
docker-compose ps

# Restart postgres if needed
docker-compose restart postgres

# Verify port mapping
docker-compose port postgres 5432
```

#### 3. Alembic Migration Failed

**Problem**: `ModuleNotFoundError: No module named 'psycopg2'`

**Solution**:
```bash
pip install psycopg2-binary
```

#### 4. OpenAI API Key Missing

**Problem**: `OpenAI API key not configured`

**Solution**: Ensure your `.env` file contains a valid OpenAI API key:
```env
OPENAI_API_KEY=sk-your-api-key-here
```

#### 5. Frontend Not Connecting to Backend

**Problem**: API requests fail with network errors

**Solution**: 
- Ensure backend is running on port 8000
- Check that Vite proxy is configured correctly in `vite.config.ts`
- If frontend is on a different port, requests go through the proxy

#### 6. Password Validation Error

**Problem**: `ValueError: password cannot be longer than 72 bytes`

**Solution**: This is handled automatically. Passwords are limited to 128 characters maximum.

#### 7. Theme Not Persisting

**Problem**: Theme resets on page refresh

**Solution**: Clear localStorage and refresh:
```javascript
localStorage.removeItem('theme-storage')
```

#### 8. RAG/ICD-10 Search Not Working

**Problem**: Medical Coder agent returns no ICD-10 codes

**Solution**: The pgvector database needs to be seeded with ICD-10 data:
```bash
# Check if ICD-10 data exists
curl -X GET "http://localhost:8000/api/v1/rag/corpus/icd10/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"

# If document_count is 0, run the seed script:
source venv/bin/activate
export OPENAI_API_KEY=your_key
python scripts/seed_icd10.py
```

#### 9. OpenAI Embedding Errors During Seeding

**Problem**: `openai.AuthenticationError` or rate limit errors

**Solution**: 
- Verify your OpenAI API key is valid and has sufficient credits
- For rate limits, wait a few minutes and try again
- Check your OpenAI usage dashboard: https://platform.openai.com/usage

### Logs

View backend logs for debugging:
```bash
# If running directly
python -m app.main  # Logs appear in terminal

# If running with Docker
docker-compose logs -f backend
```

### Health Checks

```bash
# Check backend health
curl http://localhost:8000/health

# Check database connection
curl http://localhost:8000/api/v1/auth/me  # Should return 401 if not authenticated
```

---

## Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **React Documentation**: https://react.dev/
- **Tailwind CSS**: https://tailwindcss.com/docs
- **PostgreSQL**: https://www.postgresql.org/docs/
- **pgvector**: https://github.com/pgvector/pgvector

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `pytest`
5. Commit changes: `git commit -m 'Add my feature'`
6. Push to branch: `git push origin feature/my-feature`
7. Submit a pull request

---

## License

This project is proprietary and confidential.

---

*Documentation last updated: January 17, 2026*

