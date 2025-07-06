"""Webhook endpoints for GitHub integration"""
import json
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
from app.models.webhook_schemas import WebhookPullRequestEvent, WebhookResponse
from app.services import webhook_service, task_service


router = APIRouter()


@router.post("/webhook/github", response_model=WebhookResponse)
async def github_webhook(
    request: Request,
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256")
):
    """
    Handle GitHub webhook events
    
    Supports pull request events for automated code review
    """
    # Get raw payload for signature verification
    payload = await request.body()
    
    # Validate webhook signature
    webhook_service.validate_webhook_request(payload, x_hub_signature_256)
    
    try:
        # Parse JSON payload
        payload_data = json.loads(payload.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Handle different event types
    if x_github_event == "pull_request":
        return await handle_pull_request_event(payload_data)
    else:
        return WebhookResponse(
            message=f"Unsupported event type: {x_github_event}",
            action=payload_data.get("action", "unknown")
        )


async def handle_pull_request_event(payload_data: dict) -> WebhookResponse:
    """
    Handle pull request webhook events
    
    Args:
        payload_data: Parsed webhook payload
        
    Returns:
        Webhook response with task information
    """
    try:
        # Parse webhook event
        event = WebhookPullRequestEvent(**payload_data)
        
        # Check if this action should trigger analysis
        if not webhook_service.should_trigger_analysis(event.action):
            return WebhookResponse(
                message=f"PR action '{event.action}' ignored - no analysis triggered",
                action=event.action,
                pr_number=event.number
            )
        
        # Build repository URL
        repo_url = webhook_service.build_repo_url(event.repository.model_dump())
        
        # Submit analysis task
        task_id = task_service.submit_analysis_task(
            repo_url=repo_url,
            pr_number=event.number,
            github_token=None  # Webhooks don't include tokens
        )
        
        return WebhookResponse(
            message=f"PR analysis started for #{event.number}",
            task_id=task_id,
            pr_number=event.number,
            action=event.action
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process webhook: {str(e)}"
        )