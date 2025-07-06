"""Task service for managing analysis tasks"""
from typing import Optional, Tuple, Any
from app.models.schemas import TaskStatus
from app.core.celery_app import celery_app
from app.tasks.analysis_tasks import analyze_pr_task


def submit_analysis_task(repo_url: str, pr_number: int, github_token: Optional[str] = None) -> str:
    """Submit a new analysis task and return task ID"""
    task = analyze_pr_task.delay(repo_url, pr_number, github_token)
    return task.id


def get_task_status(task_id: str) -> Optional[TaskStatus]:
    """Get the status of a task by ID"""
    try:
        result = celery_app.AsyncResult(task_id)
        
        # Map Celery states to our TaskStatus enum
        state_mapping = {
            'PENDING': TaskStatus.PENDING,
            'PROGRESS': TaskStatus.PROCESSING,
            'SUCCESS': TaskStatus.COMPLETED,
            'FAILURE': TaskStatus.FAILED,
            'RETRY': TaskStatus.PROCESSING,
            'REVOKED': TaskStatus.FAILED,
        }
        
        return state_mapping.get(result.state, TaskStatus.PENDING)
        
    except Exception:
        return None


def get_task_result(task_id: str) -> Tuple[Optional[TaskStatus], Optional[Any], Optional[str]]:
    """Get the result of a task by ID
    
    Returns:
        Tuple of (status, result, error_message)
    """
    try:
        result = celery_app.AsyncResult(task_id)
        
        # Map Celery states to our TaskStatus enum
        state_mapping = {
            'PENDING': TaskStatus.PENDING,
            'PROGRESS': TaskStatus.PROCESSING,
            'SUCCESS': TaskStatus.COMPLETED,
            'FAILURE': TaskStatus.FAILED,
            'RETRY': TaskStatus.PROCESSING,
            'REVOKED': TaskStatus.FAILED,
        }
        
        status = state_mapping.get(result.state, TaskStatus.PENDING)
        
        if result.state == 'SUCCESS':
            return status, result.result, None
        elif result.state == 'FAILURE':
            error_msg = str(result.result) if result.result else "Task failed"
            return status, None, error_msg
        else:
            return status, None, None
            
    except Exception:
        return None, None, None
