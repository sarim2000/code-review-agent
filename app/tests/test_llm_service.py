import pytest
from unittest.mock import Mock, patch
from app.services.llm_service import LLMService
from app.models.schemas import IssueType


class TestLLMService:
    """Test LLM service functionality"""
    
    def test_llm_service_initialization(self):
        """Test LLM service initializes correctly"""
        service = LLMService()
        assert service.model == "gpt-4o-mini"
    
    def test_llm_service_with_openai_key(self):
        """Test LLM service initializes with OpenAI key"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            service = LLMService()
            assert service.client is not None
    
    def test_llm_service_without_openai_key(self):
        """Test LLM service without OpenAI key"""
        with patch.dict('os.environ', {}, clear=True):
            service = LLMService()
            assert service.client is None
    
    def test_analyze_code_with_ai_success(self):
        """Test successful AI code analysis"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
          "files": [
            {
              "name": "test.py",
              "issues": [
                {
                  "type": "style",
                  "line": 10,
                  "description": "Line too long",
                  "suggestion": "Break line into multiple lines"
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
        '''
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('app.services.llm_service.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_client.chat.completions.create.return_value = mock_response
                mock_openai.return_value = mock_client
                
                service = LLMService()
                pr_data = {
                    "title": "Test PR",
                    "description": "Test description",
                    "files": [
                        {
                            "filename": "test.py",
                            "status": "modified",
                            "additions": 5,
                            "deletions": 2,
                            "patch": "mock patch content"
                        }
                    ]
                }
                
                result = service.analyze_code_with_ai(pr_data)
                
                assert result["files"][0]["name"] == "test.py"
                assert len(result["files"][0]["issues"]) == 1
                assert result["files"][0]["issues"][0]["type"] == "style"
                assert result["summary"]["total_issues"] == 1
    
    def test_analyze_code_with_ai_no_client(self):
        """Test AI analysis without OpenAI client"""
        service = LLMService()
        service.client = None
        
        pr_data = {"title": "Test", "files": []}
        
        with pytest.raises(ValueError, match="OpenAI API key not configured"):
            service.analyze_code_with_ai(pr_data)
    
    def test_analyze_code_with_ai_openai_error(self):
        """Test AI analysis with OpenAI error"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('app.services.llm_service.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_client.chat.completions.create.side_effect = Exception("API Error")
                mock_openai.return_value = mock_client
                
                service = LLMService()
                pr_data = {"title": "Test", "files": []}
                
                with pytest.raises(Exception, match="AI analysis failed"):
                    service.analyze_code_with_ai(pr_data)
    
    def test_build_analysis_prompt(self):
        """Test analysis prompt building"""
        service = LLMService()
        pr_data = {
            "title": "Test PR",
            "description": "Test description",
            "files": [
                {
                    "filename": "test.py",
                    "status": "modified",
                    "additions": 5,
                    "deletions": 2,
                    "patch": "mock patch content"
                }
            ]
        }
        
        prompt = service._build_analysis_prompt(pr_data)
        
        assert "Test PR" in prompt
        assert "test.py" in prompt
        assert "mock patch content" in prompt
        assert "JSON format" in prompt
    
    def test_parse_ai_response_valid_json(self):
        """Test parsing valid AI response"""
        service = LLMService()
        response_text = '''
        Here is the analysis:
        {
          "files": [{"name": "test.py", "issues": []}],
          "summary": {"total_files": 1, "total_issues": 0, "critical_issues": 0}
        }
        '''
        
        pr_data = {"files": [{"filename": "test.py"}]}
        result = service._parse_ai_response(response_text, pr_data)
        
        assert result["files"][0]["name"] == "test.py"
        assert result["summary"]["total_files"] == 1
    
    def test_parse_ai_response_invalid_json(self):
        """Test parsing invalid AI response"""
        service = LLMService()
        response_text = "This is not valid JSON"
        
        pr_data = {"files": [{"filename": "test.py"}]}
        result = service._parse_ai_response(response_text, pr_data)
        
        # Should return fallback response
        assert result["files"][0]["name"] == "AI Analysis"
        assert len(result["files"][0]["issues"]) == 1
        assert result["summary"]["total_issues"] == 1
    
    def test_validate_ai_response(self):
        """Test AI response validation"""
        service = LLMService()
        
        # Test with invalid issue type
        analysis = {
            "files": [
                {
                    "name": "test.py",
                    "issues": [
                        {
                            "type": "invalid_type",
                            "line": "not_a_number",
                            "description": "Test issue",
                            "suggestion": "Fix it"
                        }
                    ]
                }
            ]
        }
        
        pr_data = {"files": []}
        result = service._validate_ai_response(analysis, pr_data)
        
        # Should correct invalid type and line number
        assert result["files"][0]["issues"][0]["type"] == "best_practice"
        assert result["files"][0]["issues"][0]["line"] == 1
        assert "summary" in result
    
    def test_create_fallback_response(self):
        """Test fallback response creation"""
        service = LLMService()
        pr_data = {"files": [{"filename": "test.py"}]}
        
        result = service._create_fallback_response(pr_data, "Test error")
        
        assert result["files"][0]["name"] == "AI Analysis"
        assert "Test error" in result["files"][0]["issues"][0]["description"]
        assert result["summary"]["total_files"] == 1