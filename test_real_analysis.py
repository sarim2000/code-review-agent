#!/usr/bin/env python3
"""Test the code review system with a real GitHub repository"""

import json
import requests
import time

def test_pr_analysis():
    """Test PR analysis with the current repository"""
    
    # Use your actual repository for testing
    repo_url = "https://github.com/sarim2000/code-review-agent"
    pr_number = 1  # We can create a PR or use an existing one
    
    # Submit analysis request
    payload = {
        "repo_url": repo_url,
        "pr_number": pr_number
    }
    
    print(f"Testing PR analysis for {repo_url}/pull/{pr_number}")
    
    try:
        # Submit the analysis
        response = requests.post(
            "http://localhost:8000/analyze-pr",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to submit analysis: {response.status_code}")
            print(response.text)
            return False
        
        result = response.json()
        task_id = result["task_id"]
        print(f"✅ Analysis submitted with task ID: {task_id}")
        
        # Poll for results
        print("Waiting for analysis to complete...")
        max_attempts = 30
        
        for attempt in range(max_attempts):
            status_response = requests.get(f"http://localhost:8000/status/{task_id}")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data["status"]
                print(f"Status: {status}")
                
                if status == "completed":
                    # Get results
                    results_response = requests.get(f"http://localhost:8000/results/{task_id}")
                    if results_response.status_code == 200:
                        results = results_response.json()
                        print("✅ Analysis completed successfully!")
                        print(f"Files analyzed: {len(results['results']['files'])}")
                        print(f"Total issues: {results['results']['summary']['total_issues']}")
                        return True
                    else:
                        print(f"❌ Failed to get results: {results_response.status_code}")
                        return False
                
                elif status == "failed":
                    results_response = requests.get(f"http://localhost:8000/results/{task_id}")
                    if results_response.status_code == 200:
                        results = results_response.json()
                        print(f"❌ Analysis failed: {results.get('error', 'Unknown error')}")
                    return False
                
            time.sleep(2)
        
        print("❌ Analysis timed out")
        return False
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Make sure it's running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_webhook_endpoint():
    """Test the webhook endpoint"""
    print("\nTesting webhook endpoint...")
    
    # Simple ping test
    try:
        response = requests.post(
            "http://localhost:8000/webhook/github",
            json={"action": "ping"},
            headers={
                "X-GitHub-Event": "ping",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            print("✅ Webhook endpoint is accessible")
            return True
        else:
            print(f"❌ Webhook endpoint returned: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to webhook endpoint")
        return False

if __name__ == "__main__":
    print("🚀 Testing Code Review Agent")
    print("=" * 50)
    
    # Test webhook first (simpler)
    webhook_success = test_webhook_endpoint()
    
    # Test PR analysis (more complex)
    analysis_success = test_pr_analysis()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Webhook: {'✅ PASS' if webhook_success else '❌ FAIL'}")
    print(f"Analysis: {'✅ PASS' if analysis_success else '❌ FAIL'}")
    
    if webhook_success and analysis_success:
        print("\n🎉 All tests passed! The system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the logs above for details.")