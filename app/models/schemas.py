from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IssueType(str, Enum):
    STYLE = "style"
    BUG = "bug"
    PERFORMANCE = "performance"
    BEST_PRACTICE = "best_practice"


class AnalyzePRRequest(BaseModel):
    repo_url: HttpUrl
    pr_number: int
    github_token: Optional[str] = None


class Issue(BaseModel):
    type: IssueType
    line: int
    description: str
    suggestion: str


class FileAnalysis(BaseModel):
    name: str
    issues: List[Issue]


class AnalysisSummary(BaseModel):
    total_files: int
    total_issues: int
    critical_issues: int


class AnalysisResult(BaseModel):
    files: List[FileAnalysis]
    summary: AnalysisSummary


class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus


class TaskResultResponse(BaseModel):
    task_id: str
    status: TaskStatus
    results: Optional[AnalysisResult] = None
    error: Optional[str] = None


class TaskSubmissionResponse(BaseModel):
    task_id: str
    status: TaskStatus
    message: str
