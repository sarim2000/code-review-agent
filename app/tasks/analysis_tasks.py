"""Celery tasks for code analysis"""
from celery import current_task
from app.core.celery_app import celery_app
from app.services import github_service, analysis_service
from typing import Optional


@celery_app.task(bind=True)
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
        # Update task state to failure
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(exc)}
        )
        raise exc
