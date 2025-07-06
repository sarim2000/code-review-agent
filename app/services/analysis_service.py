"""Analysis service for code review"""
import os
from typing import Dict, Any, List
from app.models.schemas import FileAnalysis, Issue, AnalysisResult, AnalysisSummary, IssueType
from app.services.llm_service import LLMService


def analyze_code(pr_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze code changes in a PR using AI or fallback to rule-based analysis
    
    Args:
        pr_data: PR data from GitHub service
    
    Returns:
        Analysis results dictionary
    """
    # Try AI analysis first if OpenAI key is available
    if os.getenv("OPENAI_API_KEY"):
        try:
            llm_service = LLMService()
            return llm_service.analyze_code_with_ai(pr_data)
        except Exception as e:
            # Fall back to rule-based analysis if AI fails
            print(f"AI analysis failed, falling back to rule-based: {e}")
            return _analyze_code_rule_based(pr_data)
    else:
        # Use rule-based analysis if no AI key available
        return _analyze_code_rule_based(pr_data)


def _analyze_code_rule_based(pr_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rule-based code analysis (fallback method)
    
    Args:
        pr_data: PR data from GitHub service
    
    Returns:
        Analysis results dictionary
    """
    files_analysis = []
    total_issues = 0
    critical_issues = 0
    
    for file_data in pr_data["files"]:
        file_analysis = _analyze_file(file_data)
        files_analysis.append(file_analysis)
        
        total_issues += len(file_analysis["issues"])
        critical_issues += sum(1 for issue in file_analysis["issues"] 
                              if issue["type"] == IssueType.BUG)
    
    summary = {
        "total_files": len(files_analysis),
        "total_issues": total_issues,
        "critical_issues": critical_issues
    }
    
    return {
        "files": files_analysis,
        "summary": summary
    }


def _analyze_file(file_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a single file for issues
    
    Args:
        file_data: File data from GitHub
    
    Returns:
        File analysis dictionary
    """
    filename = file_data["filename"]
    patch = file_data.get("patch", "")
    
    issues = []
    
    # Simple rule-based analysis for now
    # In real implementation, this would use AI/ML models
    
    if patch:
        issues.extend(_analyze_patch(patch, filename))
    
    return {
        "name": filename,
        "issues": issues
    }


def _analyze_patch(patch: str, filename: str) -> List[Dict[str, Any]]:
    """
    Analyze a patch for potential issues
    
    Args:
        patch: Git patch content
        filename: Name of the file
    
    Returns:
        List of issues found
    """
    issues = []
    
    # Split patch into lines
    lines = patch.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        # Skip context lines
        if not line.startswith('+'):
            continue
            
        # Remove the '+' prefix
        code_line = line[1:] if line.startswith('+') else line
        
        # Simple rule-based checks
        issues.extend(_check_line_issues(code_line, line_num, filename))
    
    return issues


def _check_line_issues(line: str, line_num: int, filename: str) -> List[Dict[str, Any]]:
    """
    Check a single line for issues
    
    Args:
        line: Code line to check
        line_num: Line number
        filename: File name
    
    Returns:
        List of issues found
    """
    issues = []
    
    # Style checks
    if len(line) > 100:
        issues.append({
            "type": IssueType.STYLE,
            "line": line_num,
            "description": f"Line too long ({len(line)} characters)",
            "suggestion": "Break line into multiple lines or use shorter variable names"
        })
    
    if line.rstrip() != line:
        issues.append({
            "type": IssueType.STYLE,
            "line": line_num,
            "description": "Trailing whitespace",
            "suggestion": "Remove trailing whitespace"
        })
    
    # Bug checks
    if "print(" in line.lower() and filename.endswith('.py'):
        issues.append({
            "type": IssueType.BUG,
            "line": line_num,
            "description": "Print statement found",
            "suggestion": "Use proper logging instead of print statements"
        })
    
    if "console.log(" in line.lower() and (filename.endswith('.js') or filename.endswith('.ts')):
        issues.append({
            "type": IssueType.BUG,
            "line": line_num,
            "description": "Console.log statement found",
            "suggestion": "Use proper logging instead of console.log"
        })
    
    # Performance checks
    if "for" in line and "in" in line and "range(len(" in line:
        issues.append({
            "type": IssueType.PERFORMANCE,
            "line": line_num,
            "description": "Inefficient loop pattern",
            "suggestion": "Use enumerate() instead of range(len())"
        })
    
    # Best practice checks
    if "TODO" in line.upper() or "FIXME" in line.upper():
        issues.append({
            "type": IssueType.BEST_PRACTICE,
            "line": line_num,
            "description": "TODO/FIXME comment found",
            "suggestion": "Create a proper issue ticket for this task"
        })
    
    return issues