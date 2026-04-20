# Personalized Medical Triage Assistant

An AI-powered medical triage system using LangGraph for multi-agent orchestration, FastAPI backend, React frontend, and PostgreSQL with pgvector for RAG capabilities.

## Features

- **Multi-Agent Workflow**: LangGraph orchestrates 4 specialized agents:
  1. **Interviewer Agent**: Patient-facing, collects symptoms using reflective listening
  2. **Risk Assessor Agent**: Real-time emergency detection with rules engine
  3. **Medical Coder Agent**: Maps symptoms to ICD-10 codes using RAG
  4. **Scribe Agent**: Generates structured SOAP notes for EHR

- **Emergency Detection**: Immediate interrupt capability for red-flag symptoms
- **RAG Integration**: ICD-10 code mapping using pgvector embeddings
- **Structured Outputs**: All agent outputs are validated via Pydantic models
- **User Authentication**: JWT-based auth with session management
- **Patient Management**: User-scoped patient records and triage history

## Tech Stack

- **Backend**: Python FastAPI
- **Agent Orchestration**: LangGraph
- **LLM + Embeddings**: OpenAI (GPT-4, text-embedding-3-small)
- **Database**: PostgreSQL with pgvector extension
- **Frontend**: React with TypeScript
- **Testing**: pytest with >80% coverage

## Project Structure

```
├── app/                    # FastAPI application
│   ├── main.py            # Entry point
│   ├── application.py     # App factory
│   └── router.py          # Route aggregation
├── config/                 # Configuration
│   ├── settings.py        # Environment config
│   └── logging.py         # Structured logging
├── database/              # Database layer
│   ├── engine.py          # SQLAlchemy engine
│   ├── models.py          # SQLAlchemy models
│   ├── base_dao.py        # Base DAO class
│   └── dao/               # Collection DAOs
├── modules/               # Feature modules
│   ├── auth/              # Authentication
│   ├── patients/          # Patient management
│   ├── triage/            # Triage workflow
│   ├── dashboard/         # Dashboard analytics
│   └── rag/               # RAG/Vector search
├── agents/                # LangGraph agents
│   ├── graph.py           # LangGraph graph definition
│   ├── nodes/             # Agent nodes
│   ├── state.py           # Graph state
│   └── schemas.py         # Pydantic outputs
├── integrations/          # External integrations
│   └── openai/            # OpenAI client wrapper
├── frontend/              # React application
├── tests/                 # Test suite
├── alembic/               # Database migrations
└── docker/                # Docker configs
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with pgvector extension
- Docker & Docker Compose (optional)

### Local Development

1. **Clone and setup backend:**
   ```bash
   cd personal_project
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   ```

2. **Setup database:**
   ```bash
   # Start PostgreSQL with pgvector
   docker-compose up -d postgres
   
   # Run migrations
   alembic upgrade head
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key and database credentials
   ```

4. **Run backend:**
   ```bash
   python -m app.main
   ```

5. **Setup and run frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Docker Compose

```bash
# Build and run all services
docker-compose up --build

# Access:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/logout` - Logout
- `POST /api/v1/users` - Create user
- `GET /api/v1/users/me` - Get current user

### Patients
- `POST /api/v1/patients` - Create patient
- `GET /api/v1/patients` - List patients
- `GET /api/v1/patients/{id}` - Get patient
- `PUT /api/v1/patients/{id}` - Update patient

### Triage
- `POST /api/v1/triage/threads` - Create triage thread
- `GET /api/v1/triage/threads` - List threads
- `GET /api/v1/triage/threads/{id}` - Get thread
- `POST /api/v1/triage/threads/{id}/messages` - Send message (runs LangGraph)
- `GET /api/v1/triage/threads/{id}/artifacts` - Get artifacts

### Dashboard
- `GET /api/v1/dashboard/summary` - Get summary stats
- `GET /api/v1/dashboard/patients` - Get patient list with status

### RAG (Admin)
- `POST /api/v1/rag/ingest/icd10` - Ingest ICD-10 corpus

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_agents.py -v
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://...` |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `JWT_SECRET` | JWT signing secret | Required |
| `DEBUG` | Enable debug mode | `false` |

## License

MIT

