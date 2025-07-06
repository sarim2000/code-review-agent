"""Webhook-specific schemas for GitHub events"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class GitHubUser(BaseModel):
    """GitHub user model"""
    login: str
    id: int
    avatar_url: str
    html_url: str


class GitHubRepository(BaseModel):
    """GitHub repository model"""
    id: int
    name: str
    full_name: str
    owner: GitHubUser
    html_url: str
    clone_url: str
    ssh_url: str
    default_branch: str


class GitHubPullRequest(BaseModel):
    """GitHub pull request model"""
    id: int
    number: int
    title: str
    body: Optional[str] = None
    state: str
    user: GitHubUser
    head: Dict[str, Any]
    base: Dict[str, Any]
    html_url: str
    diff_url: str
    patch_url: str
    created_at: str
    updated_at: str


class WebhookPullRequestEvent(BaseModel):
    """GitHub pull request webhook event"""
    action: str
    number: int
    pull_request: GitHubPullRequest
    repository: GitHubRepository
    sender: GitHubUser


class WebhookResponse(BaseModel):
    """Response for webhook events"""
    message: str
    task_id: Optional[str] = None
    pr_number: Optional[int] = None
    action: str