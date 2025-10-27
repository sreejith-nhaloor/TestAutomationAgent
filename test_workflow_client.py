#!/usr/bin/env python3
"""
Test script for the new workflow API endpoint.
"""

import requests
import json

def test_workflow_api():
    """Test the new workflow API endpoint."""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Workflow API...")
    
    # Test 1: Execute workflow without PR creation
    print("\n📋 Test 1: Execute workflow without PR creation")
    payload = {
        "auto_create_pr": False
    }
    
    try:
        response = requests.post(f"{base_url}/execute-workflow/", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Please start the server with: python api.py")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 2: Execute workflow with PR creation
    print("\n📋 Test 2: Execute workflow with PR creation")
    payload = {
        "auto_create_pr": True
    }
    
    try:
        response = requests.post(f"{base_url}/execute-workflow/", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Health check
    print("\n📋 Test 3: Health check")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_workflow_api()