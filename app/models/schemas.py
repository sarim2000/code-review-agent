from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class TaskStatus(str, Enum):
    """Analysis task status values"""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"


class IssueType(str, Enum):
    """Code issue types detected by analysis"""
    STYLE = "style"
    BUG = "bug"
    PERFORMANCE = "performance"
    BEST_PRACTICE = "best_practice"


class AnalyzePRRequest(BaseModel):
    """Request to analyze a GitHub Pull Request"""
    repo_url: HttpUrl = Field(
        ...,
        description="GitHub repository URL (e.g., https://github.com/owner/repo)",
        example="https://github.com/sarim2000/code-review-agent"
    )
    pr_number: int = Field(
        ...,
        description="Pull request number to analyze",
        example=1,
        gt=0
    )
    github_token: Optional[str] = Field(
        None,
        description="GitHub personal access token for authentication (recommended for private repos)",
        example="ghp_xxxxxxxxxxxxxxxxxxxx"
    )


class Issue(BaseModel):
    """Individual code issue detected during analysis"""
    type: IssueType = Field(..., description="Category of the issue")
    line: int = Field(..., description="Line number where issue was found", example=15)
    description: str = Field(..., description="Description of the issue", example="Line too long (120 characters)")
    suggestion: str = Field(..., description="Suggested fix for the issue", example="Break line into multiple lines")


class FileAnalysis(BaseModel):
    """Analysis results for a single file"""
    name: str = Field(..., description="File path and name", example="src/main.py")
    issues: List[Issue] = Field(..., description="List of issues found in this file")


class AnalysisSummary(BaseModel):
    """Summary statistics of the analysis"""
    total_files: int = Field(..., description="Total number of files analyzed", example=5)
    total_issues: int = Field(..., description="Total number of issues found", example=12)
    critical_issues: int = Field(..., description="Number of critical/bug issues", example=2)


class AnalysisResult(BaseModel):
    """Complete analysis results"""
    files: List[FileAnalysis] = Field(..., description="Analysis results for each file")
    summary: AnalysisSummary = Field(..., description="Summary statistics")


class TaskStatusResponse(BaseModel):
    """Task status information"""
    task_id: str = Field(..., description="Unique task identifier", example="abc123-def456-ghi789")
    status: TaskStatus = Field(..., description="Current task status")


class TaskResultResponse(BaseModel):
    """Task results with analysis data or error information"""
    task_id: str = Field(..., description="Unique task identifier", example="abc123-def456-ghi789")
    status: TaskStatus = Field(..., description="Final task status")
    results: Optional[AnalysisResult] = Field(None, description="Analysis results (if completed successfully)")
    error: Optional[str] = Field(None, description="Error message (if task failed)")


class TaskSubmissionResponse(BaseModel):
    """Response when submitting a new analysis task"""
    task_id: str = Field(..., description="Unique task identifier for tracking", example="abc123-def456-ghi789")
    status: TaskStatus = Field(..., description="Initial task status (always 'pending')")
    message: str = Field(..., description="Confirmation message", example="Analysis task submitted successfully")
