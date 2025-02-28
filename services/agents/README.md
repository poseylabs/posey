# @posey.ai/agents

A FastAPI-based backend service for managing AI agents, their tasks, and interactions.

## Overview

The @posey.ai/agents service provides a robust backend infrastructure for managing AI agents, handling task delegation, maintaining agent memory, and processing user interactions. The service integrates with multiple databases for different purposes:

- **Couchbase**: Agent metadata and configuration storage
- **PostgreSQL**: Task and user data management
- **Qdrant**: Vector database for agent memory and context retrieval

## Getting Started

### Prerequisites

- Python 3.10
- Docker (for containerized deployment)
- Access to required databases (Couchbase, PostgreSQL, Qdrant)

### Installation

1. Set up the Python environment:
```bash
conda env create -f environment.yml
conda activate agent_backend
```

2. Configure environment variables in `.env`:
```bash
COUCHBASE_USER=your_username
COUCHBASE_PASSWORD=your_password
COUCHBASE_BUCKET=your_bucket
COUCHBASE_URL=your_url

POSTGRES_DB_POSEY=your_db
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=your_host

QDRANT_URL=your_qdrant_url
```

### Running the Service

#### Local Development
```bash
uvicorn main:app --host 0.0.0.0 --port 5555 --reload
```

#### Docker Deployment
```bash
npm run docker:build
npm run docker:start
```

## API Endpoints

### Agents
- `GET /agents/{agent_id}` - Retrieve agent metadata
- `PUT /agents/{agent_id}` - Create or update agent metadata

### Tasks
- `POST /tasks` - Create a new task
- `GET /tasks/{task_id}` - Get task details
- `PATCH /tasks/{task_id}/status` - Update task status

### Memory
- `GET /memory/context` - Retrieve context based on vector similarity
- `GET /memory/enhanced-context` - Get enhanced context with relevance scoring

### Delegation
- `POST /delegation/delegate_task` - Delegate a task to an appropriate agent
- `GET /delegation/status/{task_id}` - Check delegation status

### Analytics
- `GET /analytics/tasks` - Get task-related metrics
- `GET /analytics/agents` - Get agent performance metrics

### Health
- `GET /health` - Check service health status

## Architecture

### Database Structure

1. **Couchbase**
   - Stores agent metadata, capabilities, and configurations
   - Handles agent-specific data and settings

2. **PostgreSQL**
   - Manages task records and user data
   - Tracks task status and history

3. **Qdrant**
   - Vector database for semantic search
   - Stores and retrieves agent memory contexts

### Key Components

1. **Agent Management**
   - Agent metadata storage and retrieval
   - Capability tracking and updates

2. **Task Delegation System**
   - Intelligent task classification
   - Agent-task matching based on capabilities
   - Task status tracking

3. **Memory System**
   - Context retrieval using vector similarity
   - Enhanced context processing with relevance scoring
   - Historical interaction management

4. **Monitoring and Analytics**
   - Task completion metrics
   - Agent performance tracking
   - System health monitoring

## Docker Support

The service includes Docker support for containerized deployment. The Docker configuration:
- Uses Python 3.10 slim base image
- Installs required dependencies
- Sets up appropriate environment variables
- Exposes port 5555 for API access

## Error Handling

The service implements comprehensive error handling:
- Database connection error management
- Request validation
- Proper HTTP status codes
- Detailed error logging
