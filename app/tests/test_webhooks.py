import pytest
import json
import hmac
import hashlib
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.main import app


client = TestClient(app)


class TestGitHubWebhooks:
    """Test GitHub webhook functionality"""
    
    def create_webhook_signature(self, payload: str, secret: str) -> str:
        """Create GitHub webhook signature"""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    def get_sample_pr_payload(self) -> dict:
        """Get sample PR webhook payload"""
        return {
            "action": "opened",
            "number": 123,
            "pull_request": {
                "id": 123456,
                "number": 123,
                "title": "Add new feature",
                "body": "This PR adds a new feature",
                "state": "open",
                "user": {
                    "login": "testuser",
                    "id": 12345,
                    "avatar_url": "https://github.com/testuser.png",
                    "html_url": "https://github.com/testuser"
                },
                "head": {
                    "ref": "feature-branch",
                    "sha": "abc123"
                },
                "base": {
                    "ref": "main",
                    "sha": "def456"
                },
                "html_url": "https://github.com/test/repo/pull/123",
                "diff_url": "https://github.com/test/repo/pull/123.diff",
                "patch_url": "https://github.com/test/repo/pull/123.patch",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            },
            "repository": {
                "id": 123456,
                "name": "repo",
                "full_name": "test/repo",
                "owner": {
                    "login": "test",
                    "id": 11111,
                    "avatar_url": "https://github.com/test.png",
                    "html_url": "https://github.com/test"
                },
                "html_url": "https://github.com/test/repo",
                "clone_url": "https://github.com/test/repo.git",
                "ssh_url": "git@github.com:test/repo.git",
                "default_branch": "main"
            },
            "sender": {
                "login": "testuser",
                "id": 12345,
                "avatar_url": "https://github.com/testuser.png",
                "html_url": "https://github.com/testuser"
            }
        }
    
    def test_webhook_pr_opened_triggers_analysis(self):
        """Test that PR opened event triggers analysis"""
        payload = self.get_sample_pr_payload()
        payload_str = json.dumps(payload)
        
        with patch.dict('os.environ', {'GITHUB_WEBHOOK_SECRET': 'test-secret'}):
            with patch('app.services.task_service.submit_analysis_task') as mock_submit:
                mock_submit.return_value = "task-123"
                
                signature = self.create_webhook_signature(payload_str, 'test-secret')
                
                response = client.post(
                    "/webhook/github",
                    data=payload_str,
                    headers={
                        "X-GitHub-Event": "pull_request",
                        "X-Hub-Signature-256": signature,
                        "Content-Type": "application/json"
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["task_id"] == "task-123"
                assert data["pr_number"] == 123
                assert data["action"] == "opened"
                assert "analysis started" in data["message"].lower()
                
                mock_submit.assert_called_once_with(
                    repo_url="https://github.com/test/repo",
                    pr_number=123,
                    github_token=None  # No GitHub token in webhook
                )
    
    def test_webhook_pr_synchronize_triggers_analysis(self):
        """Test that PR synchronize event triggers analysis"""
        payload = self.get_sample_pr_payload()
        payload["action"] = "synchronize"
        payload_str = json.dumps(payload)
        
        with patch.dict('os.environ', {'GITHUB_WEBHOOK_SECRET': 'test-secret'}):
            with patch('app.services.task_service.submit_analysis_task') as mock_submit:
                mock_submit.return_value = "task-456"
                
                signature = self.create_webhook_signature(payload_str, 'test-secret')
                
                response = client.post(
                    "/webhook/github",
                    data=payload_str,
                    headers={
                        "X-GitHub-Event": "pull_request",
                        "X-Hub-Signature-256": signature,
                        "Content-Type": "application/json"
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["task_id"] == "task-456"
                assert data["action"] == "synchronize"
    
    def test_webhook_pr_closed_ignored(self):
        """Test that PR closed event is ignored"""
        payload = self.get_sample_pr_payload()
        payload["action"] = "closed"
        payload_str = json.dumps(payload)
        
        with patch.dict('os.environ', {'GITHUB_WEBHOOK_SECRET': 'test-secret'}):
            signature = self.create_webhook_signature(payload_str, 'test-secret')
            
            response = client.post(
                "/webhook/github",
                data=payload_str,
                headers={
                    "X-GitHub-Event": "pull_request",
                    "X-Hub-Signature-256": signature,
                    "Content-Type": "application/json"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] is None
            assert data["action"] == "closed"
            assert "ignored" in data["message"].lower()
    
    def test_webhook_invalid_signature(self):
        """Test webhook with invalid signature"""
        payload = self.get_sample_pr_payload()
        payload_str = json.dumps(payload)
        
        with patch.dict('os.environ', {'GITHUB_WEBHOOK_SECRET': 'test-secret'}):
            response = client.post(
                "/webhook/github",
                data=payload_str,
                headers={
                    "X-GitHub-Event": "pull_request",
                    "X-Hub-Signature-256": "sha256=invalid-signature",
                    "Content-Type": "application/json"
                }
            )
            
            assert response.status_code == 403
    
    def test_webhook_missing_signature(self):
        """Test webhook with missing signature"""
        payload = self.get_sample_pr_payload()
        payload_str = json.dumps(payload)
        
        with patch.dict('os.environ', {'GITHUB_WEBHOOK_SECRET': 'test-secret'}):
            response = client.post(
                "/webhook/github",
                data=payload_str,
                headers={
                    "X-GitHub-Event": "pull_request",
                    "Content-Type": "application/json"
                }
            )
            
            assert response.status_code == 403
    
    def test_webhook_unsupported_event(self):
        """Test webhook with unsupported event type"""
        payload = {"action": "test"}
        payload_str = json.dumps(payload)
        
        with patch.dict('os.environ', {'GITHUB_WEBHOOK_SECRET': 'test-secret'}):
            signature = self.create_webhook_signature(payload_str, 'test-secret')
            
            response = client.post(
                "/webhook/github",
                data=payload_str,
                headers={
                    "X-GitHub-Event": "issues",
                    "X-Hub-Signature-256": signature,
                    "Content-Type": "application/json"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "unsupported" in data["message"].lower()
    
    def test_webhook_no_secret_configured(self):
        """Test webhook when no secret is configured"""
        payload = self.get_sample_pr_payload()
        payload_str = json.dumps(payload)
        
        with patch.dict('os.environ', {}, clear=True):
            response = client.post(
                "/webhook/github",
                data=payload_str,
                headers={
                    "X-GitHub-Event": "pull_request",
                    "Content-Type": "application/json"
                }
            )
            
            # Should work without signature verification when no secret is set
            assert response.status_code == 200
    
    def test_webhook_invalid_json(self):
        """Test webhook with invalid JSON payload"""
        payload_str = "invalid json"
        
        with patch.dict('os.environ', {'GITHUB_WEBHOOK_SECRET': 'test-secret'}):
            signature = self.create_webhook_signature(payload_str, 'test-secret')
            
            response = client.post(
                "/webhook/github",
                data=payload_str,
                headers={
                    "X-GitHub-Event": "pull_request",
                    "X-Hub-Signature-256": signature,
                    "Content-Type": "application/json"
                }
            )
            
            assert response.status_code == 400