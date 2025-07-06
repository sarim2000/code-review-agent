"""Webhook service for handling GitHub events"""
import os
import hmac
import hashlib
from typing import Optional
from fastapi import HTTPException


def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify GitHub webhook signature
    
    Args:
        payload: Raw request payload
        signature: GitHub signature from X-Hub-Signature-256 header
        secret: Webhook secret
        
    Returns:
        True if signature is valid, False otherwise
    """
    if not signature.startswith('sha256='):
        return False
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    provided_signature = signature[7:]  # Remove 'sha256=' prefix
    
    return hmac.compare_digest(expected_signature, provided_signature)


def validate_webhook_request(payload: bytes, signature: Optional[str]) -> None:
    """
    Validate incoming webhook request
    
    Args:
        payload: Raw request payload
        signature: GitHub signature from header
        
    Raises:
        HTTPException: If validation fails
    """
    webhook_secret = os.getenv('GITHUB_WEBHOOK_SECRET')
    
    # If no secret is configured, skip signature verification
    if not webhook_secret:
        return
    
    # If secret is configured, signature is required
    if not signature:
        raise HTTPException(
            status_code=403,
            detail="Webhook signature required"
        )
    
    # Verify signature
    if not verify_github_signature(payload, signature, webhook_secret):
        raise HTTPException(
            status_code=403,
            detail="Invalid webhook signature"
        )


def should_trigger_analysis(action: str) -> bool:
    """
    Determine if PR action should trigger analysis
    
    Args:
        action: GitHub PR action (opened, synchronize, closed, etc.)
        
    Returns:
        True if analysis should be triggered
    """
    # Trigger analysis for new PRs and when code changes
    trigger_actions = ['opened', 'synchronize', 'reopened']
    return action in trigger_actions


def extract_repo_info(repository_data: dict) -> tuple[str, str]:
    """
    Extract repository information from webhook payload
    
    Args:
        repository_data: Repository data from webhook
        
    Returns:
        Tuple of (owner, repo_name)
    """
    full_name = repository_data['full_name']
    owner, repo_name = full_name.split('/', 1)
    return owner, repo_name


def build_repo_url(repository_data: dict) -> str:
    """
    Build repository URL from webhook data
    
    Args:
        repository_data: Repository data from webhook
        
    Returns:
        GitHub repository URL
    """
    return repository_data['html_url']