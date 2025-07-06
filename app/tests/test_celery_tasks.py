import pytest
from unittest.mock import Mock, patch
from app.core.celery_app import celery_app
from app.models.schemas import TaskStatus, IssueType


class TestCeleryTasks:
    """Test Celery task functionality"""
    
    def test_analyze_pr_task_success(self):
        """Test successful PR analysis task"""
        from app.tasks.analysis_tasks import analyze_pr_task
        
        mock_analysis_result = {
            "files": [
                {
                    "name": "test.py",
                    "issues": [
                        {
                            "type": IssueType.STYLE,
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
        
        with patch('app.services.github_service.fetch_pr_data') as mock_fetch:
            with patch('app.services.analysis_service.analyze_code') as mock_analyze:
                mock_fetch.return_value = {"files": ["test.py"], "diff": "mock diff"}
                mock_analyze.return_value = mock_analysis_result
                
                result = analyze_pr_task.apply(
                    args=["https://github.com/test/repo", 123, None]
                )
                
                assert result.status == 'SUCCESS'
                assert result.result == mock_analysis_result
    
    def test_analyze_pr_task_github_error(self):
        """Test PR analysis task with GitHub fetch error"""
        from app.tasks.analysis_tasks import analyze_pr_task
        
        with patch('app.services.github_service.fetch_pr_data') as mock_fetch:
            mock_fetch.side_effect = Exception("GitHub API error")
            
            result = analyze_pr_task.apply(
                args=["https://github.com/test/repo", 123, None]
            )
            
            assert result.status == 'FAILURE'
            assert "GitHub API error" in str(result.result)
    
    def test_analyze_pr_task_analysis_error(self):
        """Test PR analysis task with analysis error"""
        from app.tasks.analysis_tasks import analyze_pr_task
        
        with patch('app.services.github_service.fetch_pr_data') as mock_fetch:
            with patch('app.services.analysis_service.analyze_code') as mock_analyze:
                mock_fetch.return_value = {"files": ["test.py"], "diff": "mock diff"}
                mock_analyze.side_effect = Exception("Analysis failed")
                
                result = analyze_pr_task.apply(
                    args=["https://github.com/test/repo", 123, None]
                )
                
                assert result.status == 'FAILURE'
                assert "Analysis failed" in str(result.result)


class TestTaskService:
    """Test task service with Celery integration"""
    
    def test_submit_analysis_task_integration(self):
        """Test task submission returns valid task ID"""
        from app.services.task_service import submit_analysis_task
        
        with patch('app.tasks.analysis_tasks.analyze_pr_task.delay') as mock_delay:
            mock_task = Mock()
            mock_task.id = "test-task-id"
            mock_delay.return_value = mock_task
            
            task_id = submit_analysis_task(
                "https://github.com/test/repo", 123, "token"
            )
            
            assert task_id == "test-task-id"
            mock_delay.assert_called_once_with(
                "https://github.com/test/repo", 123, "token"
            )
    
    def test_get_task_status_integration(self):
        """Test getting task status from Celery"""
        from app.services.task_service import get_task_status
        
        with patch('app.core.celery_app.celery_app.AsyncResult') as mock_result:
            mock_task = Mock()
            mock_task.state = 'PENDING'
            mock_result.return_value = mock_task
            
            status = get_task_status("test-task-id")
            
            assert status == TaskStatus.PENDING
            mock_result.assert_called_once_with("test-task-id")
    
    def test_get_task_result_integration(self):
        """Test getting task result from Celery"""
        from app.services.task_service import get_task_result
        
        with patch('app.core.celery_app.celery_app.AsyncResult') as mock_result:
            mock_task = Mock()
            mock_task.state = 'SUCCESS'
            mock_task.result = {"test": "result"}
            mock_result.return_value = mock_task
            
            status, result, error = get_task_result("test-task-id")
            
            assert status == TaskStatus.COMPLETED
            assert result == {"test": "result"}
            assert error is None