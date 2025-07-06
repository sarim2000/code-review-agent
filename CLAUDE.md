# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an autonomous code review agent system that uses AI to analyze GitHub pull requests. The system implements a goal-oriented AI agent that can plan and execute code reviews independently, process them asynchronously using Celery, and interact with developers through a structured API.

## Architecture

The system follows a microservices architecture with these key components:

- **FastAPI Application**: Main REST API server providing endpoints for PR analysis
- **Celery Worker**: Asynchronous task processing for code analysis
- **AI Agent**: Core review engine using agent frameworks (langchain, crewai, autogen, etc.)
- **Data Storage**: Redis or PostgreSQL for task results and caching
- **GitHub Integration**: Tools for fetching code, diffs, and PR metadata

## Core API Endpoints

- `POST /analyze-pr`: Submit GitHub PR for analysis (accepts repo_url, pr_number, github_token)
- `GET /status/<task_id>`: Check analysis task status
- `GET /results/<task_id>`: Retrieve completed analysis results

## Key Technologies

- Python 3.8+
- uv as package manager
- FastAPI for API framework
- Celery for asynchronous task processing
- Redis or PostgreSQL for data storage
- OpenAI GPT-4o-mini for AI-powered analysis (with rule-based fallback)
- PyGithub for GitHub API integration
- pytest for testing

## Development Commands

Based on the PRD requirements, typical commands would be:

```bash
# Install dependencies
uv sync

# Run the API server
uv run uvicorn main:app --reload

# Start Celery worker
uv run celery -A app.celery worker --loglevel=info

# Run tests
uv run pytest

# Start Redis (if using Redis)
redis-server
```

## Analysis Output Format

The AI agent produces structured analysis results with:
- File-level issues (style, bugs, performance, best practices)
- Line-specific recommendations
- Issue categorization and severity
- Summary statistics (total files, issues, critical issues)

## Agent Implementation Notes

The AI agent should be built using established agent frameworks and include:
- GitHub API integration for fetching PR data
- Code diff analysis capabilities
- Multi-language support for various programming languages
- Proper error handling and logging

## Coding Standards

Follow these principles when developing:

1. **DRY (Don't Repeat Yourself)**: If anything is written twice, abstract it out into reusable functions or classes
2. **Write Simple Code**: Prefer clarity and simplicity over clever solutions
3. **Use Official Packages**: Always use official SDKs and packages instead of making raw API calls (e.g., use `PyGithub` for GitHub API, official database drivers)
4. **Good Repository Structure**: Organize code into logical modules with clear separation of concerns
5. **Test-Driven Development (TDD)**: Write tests first, then implement functionality. Follow the red-green-refactor cycle for each feature

## Deployment Considerations

- Docker configuration for containerized deployment
- Support for live deployment on platforms like Railway, Render
- Environment variable management (.env files)
- Rate limiting and caching for API efficiency
- GitHub webhook support for automated triggering