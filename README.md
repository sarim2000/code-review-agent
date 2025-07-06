# Code Review Agent

Autonomous code review agent system that uses AI to analyze GitHub pull requests, process them asynchronously, and provide structured feedback through an API.

## Features

- **FastAPI REST API** with endpoints for PR analysis
- **Asynchronous processing** using Celery
- **GitHub integration** using PyGithub
- **AI-powered code analysis** with OpenAI GPT-4o-mini integration:
  - Advanced AI analysis for comprehensive code review
  - Automatic fallback to rule-based analysis
  - Detects style, bugs, performance, and best practices issues
- **Robust analysis engine** with dual-mode operation:
  - Primary: OpenAI LLM analysis (when API key provided)
  - Fallback: Rule-based pattern detection
- **Docker support** for easy deployment
- **Redis backend** for task management
- **Comprehensive testing** with pytest (33 passing tests)
- **Flower monitoring** for Celery tasks

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone and setup**:
   ```bash
   git clone <repo-url>
   cd code-review
   cp .env.example .env
   # Edit .env with your GitHub token
   ```

2. **Start services**:
   ```bash
   docker-compose up -d
   ```

3. **Access the API**:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Flower (Celery monitoring): http://localhost:5555

### Local Development

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Start Redis**:
   ```bash
   redis-server
   ```

3. **Start Celery worker**:
   ```bash
   uv run celery -A app.core.celery_app worker --loglevel=info
   ```

4. **Start API server**:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

## API Usage

### Analyze a PR

```bash
curl -X POST "http://localhost:8000/analyze-pr" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/owner/repo",
    "pr_number": 123,
    "github_token": "your_token_here"
  }'
```

Response:
```json
{
  "task_id": "abc123",
  "status": "pending",
  "message": "Analysis task submitted successfully"
}
```

### Check Task Status

```bash
curl "http://localhost:8000/status/abc123"
```

### Get Results

```bash
curl "http://localhost:8000/results/abc123"
```

## Testing

Run all tests:
```bash
uv run pytest
```

Run specific test file:
```bash
uv run pytest app/tests/test_api.py -v
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# GitHub Configuration
GITHUB_TOKEN=your_github_token_here

# OpenAI Configuration (optional - system will fallback to rule-based if not provided)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI API   │    │  Celery Worker  │    │   GitHub API    │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ POST /analyze   │───▶│ Fetch PR data   │───▶│ Pull request    │
│ GET /status     │    │ Analyze code    │    │ File content    │
│ GET /results    │    │ Store results   │    │ Diff data       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       
         ▼                       ▼                       
┌─────────────────┐    ┌─────────────────┐              
│      Redis      │    │   Analysis AI   │              
├─────────────────┤    ├─────────────────┤              
│ Task queue      │    │ Style checks    │              
│ Results store   │    │ Bug detection   │              
│ Status cache    │    │ Performance     │              
└─────────────────┘    └─────────────────┘              
```

## Project Structure

```
app/
├── api/
│   └── endpoints.py        # FastAPI route definitions
├── core/
│   └── celery_app.py      # Celery configuration
├── models/
│   └── schemas.py         # Pydantic models
├── services/
│   ├── analysis_service.py # Code analysis logic
│   ├── github_service.py   # GitHub API integration
│   ├── llm_service.py      # OpenAI LLM integration
│   └── task_service.py     # Task management
├── tasks/
│   └── analysis_tasks.py   # Celery task definitions
├── tests/
│   ├── test_api.py        # API endpoint tests
│   ├── test_celery_tasks.py # Celery task tests
│   ├── test_llm_service.py  # LLM service tests
│   └── test_analysis_integration.py # Integration tests
└── main.py                # FastAPI application
```

## Development

This project follows Test-Driven Development (TDD) principles:
- Write tests first
- Implement minimal code to pass tests
- Refactor and improve

### Coding Standards

1. **DRY**: Abstract duplicated code
2. **Simple Code**: Prefer clarity over cleverness
3. **Official Packages**: Use PyGithub over raw API calls
4. **Good Structure**: Logical module organization
5. **TDD**: Test-driven development approach

## AI Analysis

The system now includes **OpenAI GPT-4o-mini integration** for advanced code analysis:

### How it works:
1. **Primary Mode**: When `OPENAI_API_KEY` is configured, the system uses GPT-4o-mini for intelligent code review
2. **Fallback Mode**: If OpenAI is unavailable or fails, automatically falls back to rule-based analysis
3. **Intelligent Prompting**: Constructs detailed prompts with PR context, file changes, and specific analysis requirements
4. **Structured Output**: AI responses are parsed and validated to ensure consistent JSON format

### Analysis Capabilities:
- **Style Issues**: Formatting, naming conventions, code organization
- **Bug Detection**: Potential errors, null pointer exceptions, logic issues
- **Performance**: Inefficient algorithms, memory usage, optimization opportunities  
- **Best Practices**: Design patterns, maintainability, security considerations

## Future Enhancements

- Multi-language support beyond Python/JavaScript
- Webhook integration for automatic PR analysis
- Caching system for improved performance
- Rate limiting and authentication
- Support for additional LLM providers (Anthropic, Ollama)
- Detailed logging and monitoring
