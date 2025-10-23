import json
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import shutil
import subprocess
import time
from typing import Optional

app = FastAPI()

class TestExecutionRequest(BaseModel):
    """Request model for test execution and PR creation workflow"""
    auto_create_pr: Optional[bool] = False  # Set to True to skip user prompt for PR creation

class TestExecutionResponse(BaseModel):
    """Response model for test execution workflow"""
    status: str
    message: str
    error_details: Optional[str] = None

def copy_files_to_android_runner():
    """
    Copy extracted_files to android-testcase-runner/features folder.
    Returns: (success: bool, message: str)
    """
    try:
        # Step 1: Check if parallel projects exist
        current_dir = os.getcwd()
        parent_dir = os.path.dirname(current_dir)
        android_runner_path = os.path.join(parent_dir, "android-testcase-runner")
        
        print(f"🔍 Checking for android-testcase-runner project...")
        print(f"Android runner path: {android_runner_path}")
        
        if not os.path.exists(android_runner_path):
            error_msg = f"❌ android-testcase-runner project not found at {android_runner_path}"
            print(error_msg)
            return False, error_msg
            
        print("✅ android-testcase-runner project found!")
        
        # Step 2: Copy extracted_files content to android-testcase-runner/features folder
        extracted_files_path = os.path.join(current_dir, "extracted_files")
        android_features_path = os.path.join(android_runner_path, "features")
        
        if not os.path.exists(extracted_files_path):
            print(f"⚠️ Creating extracted_files directory: {extracted_files_path}")
            os.makedirs(extracted_files_path, exist_ok=True)
        
        # Ensure features directory exists in android-testcase-runner
        if not os.path.exists(android_features_path):
            print(f"⚠️ Creating features directory: {android_features_path}")
            os.makedirs(android_features_path, exist_ok=True)
        
        print(f"📁 Copying content from {extracted_files_path} to {android_features_path}")
        
        # Copy all contents from extracted_files to android-testcase-runner/features
        if os.path.exists(extracted_files_path) and os.listdir(extracted_files_path):
            for item in os.listdir(extracted_files_path):
                source_item = os.path.join(extracted_files_path, item)
                dest_item = os.path.join(android_features_path, item)
                
                if os.path.isdir(source_item):
                    if os.path.exists(dest_item):
                        shutil.rmtree(dest_item)
                    shutil.copytree(source_item, dest_item)
                    print(f"📂 Copied directory: {item}")
                else:
                    shutil.copy2(source_item, dest_item)
                    print(f"📄 Copied file: {item}")
            
            success_msg = f"✅ Successfully copied files to {android_features_path}"
            print(success_msg)
            return True, success_msg
        else:
            warning_msg = "⚠️ No files found in extracted_files directory or directory is empty"
            print(warning_msg)
            return True, warning_msg  # Not an error, just empty
            
    except Exception as e:
        error_msg = f"❌ Error copying files: {str(e)}"
        print(error_msg)
        return False, error_msg

def run_mcp_tests():
    """
    Run node test-mcp-enhanced.js ../android-testcase-runner
    Returns: (success: bool, message: str)
    """
    try:
        # Check if github-mcp-code-reviewer project exists
        current_dir = os.getcwd()
        parent_dir = os.path.dirname(current_dir)
        mcp_reviewer_path = os.path.join(parent_dir, "github-mcp-code-reviewer")
        
        if not os.path.exists(mcp_reviewer_path):
            error_msg = f"❌ github-mcp-code-reviewer project not found at {mcp_reviewer_path}"
            print(error_msg)
            return False, error_msg
        
        print(f"🚀 Running MCP tests...")
        
        # Change to mcp reviewer directory and run the test
        original_cwd = os.getcwd()
        try:
            os.chdir(mcp_reviewer_path)
            print(f"📍 Changed directory to: {mcp_reviewer_path}")
            
            # Run the node command with android-testcase-runner as relative path argument
            result = subprocess.run(
                ["node", "test-mcp-enhanced.js", "../android-testcase-runner"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            output = f"Return code: {result.returncode}\nSTDOUT:\n{result.stdout}"
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
            
            print(f"🔧 MCP Test output:\n{output}")
            
            if result.returncode == 0:
                success_msg = "✅ MCP tests executed successfully"
                print(success_msg)
                return True, success_msg
            else:
                error_msg = f"❌ MCP test execution failed with return code {result.returncode}"
                print(error_msg)
                return False, error_msg
                
        finally:
            # Always return to original directory
            os.chdir(original_cwd)
            print(f"📍 Returned to original directory: {original_cwd}")
            
    except subprocess.TimeoutExpired:
        error_msg = "⏰ MCP test execution timed out after 5 minutes"
        print(error_msg)
        return False, error_msg, "Timeout occurred"
    except Exception as e:
        error_msg = f"❌ Error running MCP tests: {str(e)}"
        print(error_msg)
        return False, error_msg, ""

def run_pr_creation():
    """
    Run node test-pr-creation.js ../android-testcase-runner
    Returns: (success: bool, message: str, output: str)
    """
    try:
        # Use the same mcp_reviewer_path
        current_dir = os.getcwd()
        parent_dir = os.path.dirname(current_dir)
        mcp_reviewer_path = os.path.join(parent_dir, "github-mcp-code-reviewer")
        
        print(f"🚀 Creating Pull Request...")
        
        # Change to mcp reviewer directory and run PR creation
        original_cwd = os.getcwd()
        try:
            os.chdir(mcp_reviewer_path)
            print(f"📍 Changed directory to: {mcp_reviewer_path}")
            
            # Run PR creation script
            result = subprocess.run(
                ["node", "test-pr-creation.js", "../android-testcase-runner"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            output = f"Return code: {result.returncode}\nSTDOUT:\n{result.stdout}"
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
            
            print(f"🔧 PR Creation output:\n{output}")
            
            if result.returncode == 0:
                success_msg = "✅ Pull Request created successfully"
                print(success_msg)
                return True, success_msg, output
            else:
                error_msg = f"❌ PR creation failed with return code {result.returncode}"
                print(error_msg)
                return False, error_msg, output
                
        finally:
            # Always return to original directory
            os.chdir(original_cwd)
            print(f"📍 Returned to original directory: {original_cwd}")
            
    except subprocess.TimeoutExpired:
        error_msg = "⏰ PR creation timed out after 5 minutes"
        print(error_msg)
        return False, error_msg, "Timeout occurred"
    except Exception as e:
        error_msg = f"❌ Error creating PR: {str(e)}"
        print(error_msg)
        return False, error_msg, ""

def extract_pr_url_from_output(pr_output: str) -> str:
    """
    Extract PR URL from the node script output.
    Looks for JSON with structure like:
    {
      "success": true,
      "pullRequest": {
        "url": "https://github.com/...",
        "number": 2
      }
    }
    """
    try:
        # Try to find JSON in the output
        lines = pr_output.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('{') and 'pullRequest' in line:
                data = json.loads(line)
                if data.get('success') and data.get('pullRequest', {}).get('url'):
                    return data['pullRequest']['url']
        
        # Fallback: Try to extract URL using regex
        url_pattern = r'https://github\.com/[^/\s]+/[^/\s]+/pull/\d+'
        match = re.search(url_pattern, pr_output)
        if match:
            return match.group(0)
            
        # If no URL found, return a default message
        return "✅ Pull Request created successfully (URL not found in output)"
        
    except Exception as e:
        print(f"⚠️ Error parsing PR output: {e}")
        return "✅ Pull Request created successfully (URL parsing failed)"

@app.post("/execute-full-workflow/", response_model=TestExecutionResponse)
async def execute_full_workflow(request: TestExecutionRequest):
    """
    Execute the complete test workflow:
    1. Copy extracted_files to android-testcase-runner/features
    2. Run node test-mcp-enhanced.js
    3. Optionally run node test-pr-creation.js (based on auto_create_pr flag)
    """
    
    print("🚀 Starting full test execution workflow...")
    
    # Step 1: Copy files
    copy_success, copy_message = copy_files_to_android_runner()
    if not copy_success:
        return TestExecutionResponse(
            status="failed",
            message="File copying failed",
            error_details=copy_message
        )
    
    # Step 2: Run MCP tests
    test_success, test_message = run_mcp_tests()
    if not test_success:
        return TestExecutionResponse(
            status="failed", 
            message="MCP test execution failed",
            error_details=test_message
        )
    
    # Step 3: Conditionally run PR creation
    pr_output = None
    if request.auto_create_pr:
        pr_success, pr_message, pr_output = run_pr_creation()
        if pr_success:
            # Extract PR URL from output
            pr_url = extract_pr_url_from_output(pr_output)
            return TestExecutionResponse(
                status="success",
                message=pr_url,  # Return the PR URL instead of success message
            )
        else:
            return TestExecutionResponse(
                status="partial_success",
                message=f"✅ Tests executed successfully but PR creation failed: {pr_message}",
                error_details=pr_message
            )
    else:
        return TestExecutionResponse(
            status="success",
            message="✅ Tests executed successfully (PR creation skipped)",
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Test Automation Workflow API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("test_workflow_api:app", host="0.0.0.0", port=8001, reload=True)