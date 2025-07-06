"""Main FastAPI application"""
from fastapi import FastAPI
from app.api.endpoints import router
from scalar_fastapi import get_scalar_api_reference


app = FastAPI(
    title="Code Review Agent API",
    description="""**Autonomous AI-powered code review system for GitHub Pull Requests**

This API provides comprehensive code analysis capabilities using advanced AI models and rule-based analysis to review GitHub Pull Requests automatically.

## Key Features

- 🤖 **AI-Powered Analysis**: Uses OpenAI GPT-4o-mini for intelligent code review
- 🔄 **Automatic Fallback**: Rule-based analysis when AI is unavailable  
- ⚡ **Asynchronous Processing**: Non-blocking analysis with task tracking
- 🔍 **Comprehensive Detection**: Style, bugs, performance, and best practices
- 🔐 **Secure**: GitHub token authentication and webhook signature verification

## Analysis Capabilities

- **Style Issues**: Formatting, naming conventions, code organization
- **Bug Detection**: Potential errors, null pointers, logic issues
- **Performance**: Algorithm efficiency, memory usage, optimizations
- **Best Practices**: Design patterns, maintainability, security

## Getting Started

1. **Submit Analysis**: POST to `/analyze-pr` with GitHub repo and PR number
2. **Monitor Progress**: GET `/status/{task_id}` to check analysis status  
3. **Get Results**: GET `/results/{task_id}` when analysis completes

## Authentication

- **GitHub Token**: Recommended for private repos and higher rate limits
- **Public Access**: Basic analysis available without authentication""",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    contact={
        "name": "Code Review Agent",
        "url": "https://github.com/sarim2000/code-review-agent",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    tags_metadata=[
        {
            "name": "Code Analysis",
            "description": "Core endpoints for submitting and retrieving code analysis results",
        },
        {
            "name": "System", 
            "description": "System health and information endpoints",
        },
        {
            "name": "Documentation",
            "description": "API documentation and reference endpoints",
        },
    ]
)

app.include_router(router)


@app.get(
    "/",
    tags=["System"],
    summary="API Welcome",
    description="""
    **Welcome endpoint providing basic API information.**
    
    This endpoint serves as the main entry point to the Code Review Agent API.
    It provides basic information about the service and current version.
    
    ## Use Cases
    
    - **Health verification**: Confirm the API is running
    - **Version checking**: Get current API version
    - **Service discovery**: Basic service information
    
    ## Response
    
    Returns welcome message and version information.
    """,
    response_description="API welcome message and version",
    responses={
        200: {
            "description": "API information retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Code Review Agent API",
                        "version": "1.0.0"
                    }
                }
            }
        }
    }
)
async def root():
    """Get API welcome message and version information"""
    return {"message": "Code Review Agent API", "version": "1.0.0"}


@app.get("/docs", include_in_schema=False)
async def docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url or "/openapi.json",
        title=app.title,
    )


@app.get(
    "/health",
    tags=["System"],
    summary="Health Check",
    description="""
    **System health and readiness check endpoint.**
    
    This endpoint provides health status information for monitoring and load balancing.
    It confirms that the API server is running and responsive.
    
    ## Monitoring Use Cases
    
    - **Load balancer health checks**: Verify service availability
    - **Container orchestration**: Kubernetes/Docker health probes
    - **Monitoring systems**: Service uptime verification
    - **CI/CD pipelines**: Deployment verification
    
    ## Health Indicators
    
    - **API responsiveness**: Server is accepting requests
    - **Basic functionality**: Core systems operational
    - **Response time**: Service performance indicator
    
    ## Status Values
    
    - **healthy**: All systems operational
    - **degraded**: Partial functionality (if implemented)
    - **unhealthy**: Critical systems down (if implemented)
    """,
    response_description="System health status",
    responses={
        200: {
            "description": "System is healthy and operational",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy"
                    }
                }
            }
        },
        503: {
            "description": "System is unhealthy or degraded",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "details": "Database connection failed"
                    }
                }
            }
        }
    }
)
async def health_check():
    """Check system health and availability"""
    return {"status": "healthy"}
