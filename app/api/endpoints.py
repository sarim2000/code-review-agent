"""API endpoints for the code review system"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    AnalyzePRRequest,
    TaskSubmissionResponse,
    TaskStatusResponse,
    TaskResultResponse,
    TaskStatus
)
from app.services import task_service


router = APIRouter()


@router.post(
    "/analyze-pr", 
    response_model=TaskSubmissionResponse,
    tags=["Code Analysis"],
    summary="Submit PR for Code Analysis",
    description="""**Submit a GitHub Pull Request for comprehensive AI-powered code analysis.**

This endpoint accepts a GitHub repository URL and PR number, then initiates an asynchronous analysis task that examines the code changes for:

- **Style Issues**: Code formatting, naming conventions, organization
- **Bug Detection**: Potential errors, null pointer exceptions, logic issues
- **Performance**: Inefficient algorithms, memory usage, optimization opportunities  
- **Best Practices**: Design patterns, maintainability, security considerations

## Analysis Modes

- **AI Analysis**: Uses OpenAI GPT-4o-mini for intelligent code review (when API key configured)
- **Rule-based Fallback**: Automatic fallback to pattern-based analysis if AI unavailable

## Authentication

- **GitHub Token**: Optional but recommended for private repos and higher rate limits
- **Public Repos**: Can analyze without token (subject to GitHub rate limits)

## Response

Returns a task ID that can be used to check analysis status and retrieve results.""",
    response_description="Task submission confirmation with unique task ID",
    responses={
        200: {
            "description": "Analysis task submitted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "task_id": "abc123-def456-ghi789",
                        "status": "pending",
                        "message": "Analysis task submitted successfully"
                    }
                }
            }
        },
        422: {
            "description": "Invalid request data",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "repo_url"],
                                "msg": "invalid or missing URL",
                                "type": "value_error"
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Server error during task submission"
        }
    }
)
async def analyze_pr(request: AnalyzePRRequest):
    """Submit a GitHub Pull Request for comprehensive code analysis"""
    try:
        task_id = task_service.submit_analysis_task(
            str(request.repo_url), 
            request.pr_number, 
            request.github_token
        )
        
        return TaskSubmissionResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message="Analysis task submitted successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {str(e)}")


@router.get(
    "/status/{task_id}", 
    response_model=TaskStatusResponse,
    tags=["Code Analysis"],
    summary="Check Analysis Task Status",
    description="""
    **Check the current status of a code analysis task.**
    
    Use this endpoint to monitor the progress of your submitted analysis task. 
    The task goes through several states during processing:
    
    ## Task States
    
    - **pending** - Task queued, waiting to start
    - **processing** - Analysis in progress (fetching PR data, running analysis)
    - **completed** - Analysis finished successfully, results available
    - **failed** - Analysis encountered an error
    
    ## Polling Guidelines
    
    - **Recommended interval**: 2-5 seconds for active monitoring
    - **Timeout**: Most analysis tasks complete within 30-60 seconds
    - **Long-running tasks**: Large PRs may take 2-3 minutes
    
    ## Next Steps
    
    - If status is `completed`, call `/results/{task_id}` to get analysis results
    - If status is `failed`, check the error details in `/results/{task_id}`
    """,
    response_description="Current task status and metadata",
    responses={
        200: {
            "description": "Task status retrieved successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "pending": {
                            "summary": "Task Pending",
                            "value": {
                                "task_id": "abc123-def456-ghi789",
                                "status": "pending"
                            }
                        },
                        "processing": {
                            "summary": "Task Processing", 
                            "value": {
                                "task_id": "abc123-def456-ghi789",
                                "status": "processing"
                            }
                        },
                        "completed": {
                            "summary": "Task Completed",
                            "value": {
                                "task_id": "abc123-def456-ghi789", 
                                "status": "completed"
                            }
                        }
                    }
                }
            }
        },
        404: {
            "description": "Task not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Task not found"
                    }
                }
            }
        }
    }
)
async def get_task_status(task_id: str):
    """Get the current status of an analysis task"""
    status = task_service.get_task_status(task_id)
    
    if status is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskStatusResponse(task_id=task_id, status=status)


@router.get(
    "/results/{task_id}", 
    response_model=TaskResultResponse,
    tags=["Code Analysis"],
    summary="Get Analysis Results",
    description="""
    **Retrieve the complete analysis results for a completed task.**
    
    This endpoint returns the detailed code analysis results including all detected issues,
    suggestions, and summary statistics.
    
    ## Analysis Results Include
    
    ### File-level Analysis
    - **Individual file reports** with specific issues found
    - **Line-by-line feedback** with exact locations
    - **Issue categorization** by type and severity
    
    ### Issue Types
    - **Style**: Code formatting, naming conventions, organization
    - **Bug**: Potential errors, null pointer exceptions, logic issues
    - **Performance**: Inefficient algorithms, memory usage, optimization opportunities  
    - **Best Practice**: Design patterns, maintainability, security considerations
    
    ### Summary Statistics
    - **Total files analyzed**
    - **Total issues found**
    - **Critical issues count**
    - **Issue breakdown by type**
    
    ## Task Status Requirements
    
    - **Completed tasks**: Returns full analysis results
    - **Failed tasks**: Returns error information 
    - **Pending/Processing tasks**: Returns status without results
    
    ## Result Structure
    
    Each issue includes:
    - **Type**: Category of the issue
    - **Line number**: Exact location in the file
    - **Description**: What the issue is
    - **Suggestion**: How to fix it
    """,
    response_description="Complete analysis results with issues and suggestions",
    responses={
        200: {
            "description": "Analysis results retrieved successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "completed_with_results": {
                            "summary": "Completed Analysis",
                            "value": {
                                "task_id": "abc123-def456-ghi789",
                                "status": "completed",
                                "results": {
                                    "files": [
                                        {
                                            "name": "src/main.py",
                                            "issues": [
                                                {
                                                    "type": "style",
                                                    "line": 15,
                                                    "description": "Line too long (120 characters)",
                                                    "suggestion": "Break line into multiple lines"
                                                },
                                                {
                                                    "type": "bug", 
                                                    "line": 23,
                                                    "description": "Potential null pointer exception",
                                                    "suggestion": "Add null check before accessing object"
                                                }
                                            ]
                                        }
                                    ],
                                    "summary": {
                                        "total_files": 1,
                                        "total_issues": 2,
                                        "critical_issues": 1
                                    }
                                },
                                "error": None
                            }
                        },
                        "failed_task": {
                            "summary": "Failed Analysis",
                            "value": {
                                "task_id": "abc123-def456-ghi789",
                                "status": "failed", 
                                "results": None,
                                "error": "GitHub repository not found or access denied"
                            }
                        },
                        "pending_task": {
                            "summary": "Pending Analysis",
                            "value": {
                                "task_id": "abc123-def456-ghi789",
                                "status": "processing",
                                "results": None,
                                "error": None
                            }
                        }
                    }
                }
            }
        },
        404: {
            "description": "Task not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Task not found"
                    }
                }
            }
        }
    }
)
async def get_task_results(task_id: str):
    """Get the complete analysis results for a task"""
    status, result, error = task_service.get_task_result(task_id)
    
    if status is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResultResponse(
        task_id=task_id,
        status=status,
        results=result,
        error=error
    )
