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


@router.post("/analyze-pr", response_model=TaskSubmissionResponse)
async def analyze_pr(request: AnalyzePRRequest):
    """Submit a PR for analysis"""
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


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get the status of an analysis task"""
    status = task_service.get_task_status(task_id)
    
    if status is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskStatusResponse(task_id=task_id, status=status)


@router.get("/results/{task_id}", response_model=TaskResultResponse)
async def get_task_results(task_id: str):
    """Get the results of an analysis task"""
    status, result, error = task_service.get_task_result(task_id)
    
    if status is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResultResponse(
        task_id=task_id,
        status=status,
        results=result,
        error=error
    )
