"""Celery tasks for code analysis"""
from celery import current_task
from celery.exceptions import Retry, WorkerLostError
from app.core.celery_app import celery_app
from app.services import github_service, analysis_service
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 60})
def analyze_pr_task(self, repo_url: str, pr_number: int, github_token: Optional[str] = None):
    """
    Analyze a GitHub PR asynchronously
    
    Args:
        repo_url: GitHub repository URL
        pr_number: Pull request number
        github_token: Optional GitHub token for authentication
    
    Returns:
        Analysis results dictionary
    """
    try:
        # Update task state to processing
        current_task.update_state(
            state='PROGRESS',
            meta={'status': 'Fetching PR data from GitHub'}
        )
        
        # Fetch PR data from GitHub
        pr_data = github_service.fetch_pr_data(repo_url, pr_number, github_token)
        
        # Update task state
        current_task.update_state(
            state='PROGRESS',
            meta={'status': 'Analyzing code changes'}
        )
        
        # Analyze the code
        analysis_result = analysis_service.analyze_code(pr_data)
        
        return analysis_result
        
    except Exception as exc:
        # Log the error for debugging
        logger.error(f"Task {self.request.id} failed: {exc}", exc_info=True)
        
        # Update task state to failure with proper error info
        error_msg = str(exc)
        error_type = type(exc).__name__
        
        try:
            current_task.update_state(
                state='FAILURE',
                meta={
                    'error': error_msg,
                    'exc_type': error_type,
                    'exc_message': error_msg,
                    'repo_url': repo_url,
                    'pr_number': pr_number
                }
            )
        except Exception as state_exc:
            logger.error(f"Failed to update task state: {state_exc}")
        
        # Check if this is a retry attempt
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task {self.request.id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60, exc=exc)
        
        # Final failure - re-raise as a simple Exception to avoid serialization issues
        raise Exception(f"{error_type}: {error_msg}")
