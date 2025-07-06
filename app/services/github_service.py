"""GitHub service for fetching PR data"""
from typing import Optional, Dict, Any, List
from github import Github
from github.Repository import Repository
from github.PullRequest import PullRequest
import re


def fetch_pr_data(repo_url: str, pr_number: int, github_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch PR data from GitHub
    
    Args:
        repo_url: GitHub repository URL
        pr_number: Pull request number  
        github_token: Optional GitHub token for authentication
    
    Returns:
        Dictionary containing PR data including files and diff
    """
    # Extract owner and repo name from URL
    owner, repo_name = _extract_repo_info(repo_url)
    
    # Initialize GitHub client
    github_client = Github(github_token) if github_token else Github()
    
    try:
        # Get repository and PR
        repo = github_client.get_repo(f"{owner}/{repo_name}")
        pr = repo.get_pull(pr_number)
        
        # Get PR files and their content
        files_data = _get_pr_files(pr)
        
        # Get PR diff
        diff_data = _get_pr_diff(pr)
        
        return {
            "repo_url": repo_url,
            "pr_number": pr_number,
            "title": pr.title,
            "description": pr.body,
            "files": files_data,
            "diff": diff_data,
            "base_branch": pr.base.ref,
            "head_branch": pr.head.ref,
            "author": pr.user.login,
            "created_at": pr.created_at.isoformat(),
            "updated_at": pr.updated_at.isoformat()
        }
        
    finally:
        github_client.close()


def _extract_repo_info(repo_url: str) -> tuple[str, str]:
    """Extract owner and repo name from GitHub URL"""
    # Remove .git suffix if present
    url = repo_url.rstrip('.git')
    
    # Match GitHub URL patterns
    patterns = [
        r'https://github\.com/([^/]+)/([^/]+)/?$',
        r'git@github\.com:([^/]+)/([^/]+)\.git$',
        r'github\.com/([^/]+)/([^/]+)/?$'
    ]
    
    for pattern in patterns:
        match = re.match(pattern, url)
        if match:
            return match.groups()
    
    raise ValueError(f"Invalid GitHub repository URL: {repo_url}")


def _get_pr_files(pr: PullRequest) -> List[Dict[str, Any]]:
    """Get list of files changed in the PR"""
    files = []
    
    for file in pr.get_files():
        files.append({
            "filename": file.filename,
            "status": file.status,  # added, modified, removed
            "additions": file.additions,
            "deletions": file.deletions,
            "changes": file.changes,
            "patch": file.patch,
            "raw_url": file.raw_url,
            "blob_url": file.blob_url
        })
    
    return files


def _get_pr_diff(pr: PullRequest) -> str:
    """Get the complete diff for the PR"""
    # Get the diff using GitHub API
    diff_url = pr.diff_url
    
    # For now, we'll use the patch from individual files
    # In a real implementation, you might want to fetch the complete diff
    diff_parts = []
    
    for file in pr.get_files():
        if file.patch:
            diff_parts.append(f"--- a/{file.filename}")
            diff_parts.append(f"+++ b/{file.filename}")
            diff_parts.append(file.patch)
    
    return "\n".join(diff_parts)