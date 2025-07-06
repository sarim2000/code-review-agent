import pytest
from unittest.mock import Mock, patch
from app.services.analysis_service import analyze_code, _analyze_code_rule_based


class TestAnalysisIntegration:
    """Test analysis service with OpenAI integration"""
    
    def test_analyze_code_with_openai_key(self):
        """Test that analysis uses AI when OpenAI key is available"""
        mock_ai_result = {
            "files": [
                {
                    "name": "test.py",
                    "issues": [
                        {
                            "type": "style",
                            "line": 10,
                            "description": "AI detected style issue",
                            "suggestion": "AI suggestion"
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
        
        pr_data = {
            "title": "Test PR",
            "files": [
                {
                    "filename": "test.py",
                    "status": "modified",
                    "additions": 5,
                    "deletions": 2,
                    "patch": "mock patch"
                }
            ]
        }
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('app.services.analysis_service.LLMService') as mock_llm:
                mock_service = Mock()
                mock_service.analyze_code_with_ai.return_value = mock_ai_result
                mock_llm.return_value = mock_service
                
                result = analyze_code(pr_data)
                
                assert result == mock_ai_result
                mock_service.analyze_code_with_ai.assert_called_once_with(pr_data)
    
    def test_analyze_code_without_openai_key(self):
        """Test that analysis falls back to rule-based when no OpenAI key"""
        pr_data = {
            "title": "Test PR", 
            "files": [
                {
                    "filename": "test.py",
                    "status": "modified",
                    "additions": 5,
                    "deletions": 2,
                    "patch": "+print('hello')"  # Should trigger rule-based detection
                }
            ]
        }
        
        with patch.dict('os.environ', {}, clear=True):
            result = analyze_code(pr_data)
            
            # Should use rule-based analysis
            assert result["files"][0]["name"] == "test.py"
            assert len(result["files"][0]["issues"]) > 0  # Should detect print statement
            assert result["summary"]["total_files"] == 1
    
    def test_analyze_code_ai_fallback(self):
        """Test that analysis falls back to rule-based when AI fails"""
        pr_data = {
            "title": "Test PR",
            "files": [
                {
                    "filename": "test.py", 
                    "status": "modified",
                    "additions": 5,
                    "deletions": 2,
                    "patch": "+print('hello')"
                }
            ]
        }
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('app.services.analysis_service.LLMService') as mock_llm:
                mock_service = Mock()
                mock_service.analyze_code_with_ai.side_effect = Exception("AI failed")
                mock_llm.return_value = mock_service
                
                with patch('builtins.print') as mock_print:
                    result = analyze_code(pr_data)
                    
                    # Should fall back to rule-based
                    assert result["files"][0]["name"] == "test.py"
                    assert len(result["files"][0]["issues"]) > 0
                    mock_print.assert_called_once()
                    assert "AI analysis failed" in mock_print.call_args[0][0]
    
    def test_rule_based_analysis_functionality(self):
        """Test that rule-based analysis works correctly"""
        pr_data = {
            "files": [
                {
                    "filename": "test.py",
                    "status": "modified", 
                    "additions": 3,
                    "deletions": 1,
                    "patch": "+print('debug')\n+# TODO: fix this\n+x = [i for i in range(len(items))]"
                }
            ]
        }
        
        result = _analyze_code_rule_based(pr_data)
        
        # Should detect multiple issues
        issues = result["files"][0]["issues"]
        issue_types = [issue["type"] for issue in issues]
        
        assert "bug" in issue_types  # print statement
        assert "best_practice" in issue_types  # TODO comment
        assert "performance" in issue_types  # range(len()) pattern
        assert result["summary"]["total_issues"] >= 3
    
    def test_analysis_service_maintains_compatibility(self):
        """Test that the updated service maintains API compatibility"""
        pr_data = {
            "files": [
                {
                    "filename": "empty.py",
                    "status": "added",
                    "additions": 0,
                    "deletions": 0,
                    "patch": ""
                }
            ]
        }
        
        with patch.dict('os.environ', {}, clear=True):
            result = analyze_code(pr_data)
            
            # Should return expected structure
            assert "files" in result
            assert "summary" in result
            assert result["files"][0]["name"] == "empty.py"
            assert result["files"][0]["issues"] == []
            assert result["summary"]["total_files"] == 1
            assert result["summary"]["total_issues"] == 0