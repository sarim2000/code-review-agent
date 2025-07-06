"""LLM service for AI-powered code analysis"""
import os
from typing import Dict, Any, List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMService:
    """Service for interacting with Language Learning Models"""
    
    def __init__(self):
        self.client = None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # Initialize OpenAI client if API key is available
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.client = OpenAI(api_key=openai_key)
    
    def analyze_code_with_ai(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze code using AI/LLM
        
        Args:
            pr_data: PR data from GitHub service
            
        Returns:
            Analysis results dictionary
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        # Prepare the prompt
        prompt = self._build_analysis_prompt(pr_data)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert code reviewer. Analyze the provided code changes and identify issues related to style, bugs, performance, and best practices. Return your analysis in the specified JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            # Parse the response
            analysis_text = response.choices[0].message.content
            return self._parse_ai_response(analysis_text, pr_data)
            
        except Exception as e:
            raise Exception(f"AI analysis failed: {str(e)}")
    
    def _build_analysis_prompt(self, pr_data: Dict[str, Any]) -> str:
        """Build the analysis prompt for the AI"""
        
        # Get the first few files for analysis (to stay within token limits)
        files_to_analyze = pr_data["files"][:5]  # Limit to 5 files
        
        prompt_parts = [
            f"Analyze this GitHub Pull Request:",
            f"Title: {pr_data['title']}",
            f"Description: {pr_data.get('description', 'No description')}",
            f"",
            f"Files changed ({len(files_to_analyze)} of {len(pr_data['files'])}):",
            ""
        ]
        
        for file_data in files_to_analyze:
            prompt_parts.extend([
                f"File: {file_data['filename']}",
                f"Status: {file_data['status']}",
                f"Changes: +{file_data['additions']} -{file_data['deletions']}",
                f"Patch:",
                f"```diff",
                file_data.get('patch', '')[:2000],  # Limit patch size
                f"```",
                ""
            ])
        
        prompt_parts.extend([
            "Please analyze the code changes and identify issues in these categories:",
            "1. Style issues (formatting, naming, etc.)",
            "2. Potential bugs or errors",
            "3. Performance improvements",
            "4. Best practices violations",
            "",
            "Return your analysis in this JSON format:",
            "{",
            '  "files": [',
            '    {',
            '      "name": "filename",',
            '      "issues": [',
            '        {',
            '          "type": "style|bug|performance|best_practice",',
            '          "line": line_number,',
            '          "description": "Issue description",',
            '          "suggestion": "How to fix it"',
            '        }',
            '      ]',
            '    }',
            '  ],',
            '  "summary": {',
            '    "total_files": number,',
            '    "total_issues": number,',
            '    "critical_issues": number',
            '  }',
            "}"
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_ai_response(self, response_text: str, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI response and return structured data"""
        try:
            import json
            
            # Try to extract JSON from the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                analysis = json.loads(json_str)
                
                # Validate and clean the response
                return self._validate_ai_response(analysis, pr_data)
            else:
                # If no valid JSON found, create a fallback response
                return self._create_fallback_response(pr_data, response_text)
                
        except json.JSONDecodeError:
            # If JSON parsing fails, create a fallback response
            return self._create_fallback_response(pr_data, response_text)
    
    def _validate_ai_response(self, analysis: Dict[str, Any], pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean AI response"""
        if not isinstance(analysis, dict):
            return self._create_fallback_response(pr_data, "Invalid response format")
        
        # Ensure required fields exist
        if "files" not in analysis:
            analysis["files"] = []
        
        if "summary" not in analysis:
            analysis["summary"] = {
                "total_files": len(pr_data["files"]),
                "total_issues": 0,
                "critical_issues": 0
            }
        
        # Validate issue types
        valid_types = ["style", "bug", "performance", "best_practice"]
        for file_analysis in analysis["files"]:
            if "issues" in file_analysis:
                for issue in file_analysis["issues"]:
                    if issue.get("type") not in valid_types:
                        issue["type"] = "best_practice"
                    
                    # Ensure line number is valid
                    if not isinstance(issue.get("line"), int):
                        issue["line"] = 1
        
        return analysis
    
    def _create_fallback_response(self, pr_data: Dict[str, Any], error_text: str) -> Dict[str, Any]:
        """Create a fallback response when AI analysis fails"""
        return {
            "files": [
                {
                    "name": "AI Analysis",
                    "issues": [
                        {
                            "type": "best_practice",
                            "line": 1,
                            "description": f"AI analysis encountered an issue: {error_text[:100]}",
                            "suggestion": "Please review the code manually or try again"
                        }
                    ]
                }
            ],
            "summary": {
                "total_files": len(pr_data["files"]),
                "total_issues": 1,
                "critical_issues": 0
            }
        }