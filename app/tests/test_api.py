import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.main import app
from app.models.schemas import TaskStatus


client = TestClient(app)


class TestAnalyzePREndpoint:
    """Test the POST /analyze-pr endpoint"""
    
    def test_analyze_pr_valid_request(self):
        """Test that valid PR analysis request returns task ID"""
        request_data = {
            "repo_url": "https://github.com/test/repo",
            "pr_number": 123
        }
        
        with patch('app.services.task_service.submit_analysis_task') as mock_submit:
            mock_submit.return_value = "test-task-id"
            
            response = client.post("/analyze-pr", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test-task-id"
            assert data["status"] == TaskStatus.PENDING
            assert "submitted" in data["message"].lower()
    
    def test_analyze_pr_with_github_token(self):
        """Test PR analysis with GitHub token"""
        request_data = {
            "repo_url": "https://github.com/test/repo",
            "pr_number": 123,
            "github_token": "test-token"
        }
        
        with patch('app.services.task_service.submit_analysis_task') as mock_submit:
            mock_submit.return_value = "test-task-id"
            
            response = client.post("/analyze-pr", json=request_data)
            
            assert response.status_code == 200
            mock_submit.assert_called_once_with(
                "https://github.com/test/repo", 
                123, 
                "test-token"
            )
    
    def test_analyze_pr_invalid_url(self):
        """Test PR analysis with invalid URL"""
        request_data = {
            "repo_url": "invalid-url",
            "pr_number": 123
        }
        
        response = client.post("/analyze-pr", json=request_data)
        
        assert response.status_code == 422
    
    def test_analyze_pr_missing_fields(self):
        """Test PR analysis with missing required fields"""
        request_data = {
            "repo_url": "https://github.com/test/repo"
        }
        
        response = client.post("/analyze-pr", json=request_data)
        
        assert response.status_code == 422


class TestStatusEndpoint:
    """Test the GET /status/<task_id> endpoint"""
    
    def test_get_status_pending(self):
        """Test getting status of pending task"""
        with patch('app.services.task_service.get_task_status') as mock_status:
            mock_status.return_value = TaskStatus.PENDING
            
            response = client.get("/status/test-task-id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test-task-id"
            assert data["status"] == TaskStatus.PENDING
    
    def test_get_status_processing(self):
        """Test getting status of processing task"""
        with patch('app.services.task_service.get_task_status') as mock_status:
            mock_status.return_value = TaskStatus.PROCESSING
            
            response = client.get("/status/test-task-id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == TaskStatus.PROCESSING
    
    def test_get_status_nonexistent_task(self):
        """Test getting status of non-existent task"""
        with patch('app.services.task_service.get_task_status') as mock_status:
            mock_status.return_value = None
            
            response = client.get("/status/nonexistent-task")
            
            assert response.status_code == 404


class TestResultsEndpoint:
    """Test the GET /results/<task_id> endpoint"""
    
    def test_get_results_completed(self):
        """Test getting results of completed task"""
        mock_result = {
            "files": [
                {
                    "name": "test.py",
                    "issues": [
                        {
                            "type": "style",
                            "line": 10,
                            "description": "Line too long",
                            "suggestion": "Break into multiple lines"
                        }
                    ]
                }
            ],
            "summary": {
                "total_files": 1,
                "total_issues": 1,
                "critical_issues": 0
            }
        }
        
        with patch('app.services.task_service.get_task_result') as mock_get_result:
            mock_get_result.return_value = (TaskStatus.COMPLETED, mock_result, None)
            
            response = client.get("/results/test-task-id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test-task-id"
            assert data["status"] == TaskStatus.COMPLETED
            assert data["results"] is not None
            assert data["error"] is None
    
    def test_get_results_failed(self):
        """Test getting results of failed task"""
        with patch('app.services.task_service.get_task_result') as mock_get_result:
            mock_get_result.return_value = (TaskStatus.FAILED, None, "Analysis failed")
            
            response = client.get("/results/test-task-id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == TaskStatus.FAILED
            assert data["results"] is None
            assert data["error"] == "Analysis failed"
    
    def test_get_results_pending(self):
        """Test getting results of pending task"""
        with patch('app.services.task_service.get_task_result') as mock_get_result:
            mock_get_result.return_value = (TaskStatus.PENDING, None, None)
            
            response = client.get("/results/test-task-id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == TaskStatus.PENDING
            assert data["results"] is None
    
    def test_get_results_nonexistent_task(self):
        """Test getting results of non-existent task"""
        with patch('app.services.task_service.get_task_result') as mock_get_result:
            mock_get_result.return_value = (None, None, None)
            
            response = client.get("/results/nonexistent-task")
            
            assert response.status_code == 404