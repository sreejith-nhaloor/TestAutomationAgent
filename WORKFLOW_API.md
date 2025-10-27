# Test Workflow API

This document describes the new workflow API endpoint that automates the complete test execution and PR creation process.

## New API Endpoint

### `POST /execute-workflow/`

Executes the complete test workflow including file copying, test execution, and optional PR creation.

#### Request Body

```json
{
  "auto_create_pr": false  // Optional: Set to true to automatically create PR
}
```

#### Response

```json
{
  "status": "success",           // "success", "failed", or "partial_success"
  "message": "Success message", 
  "test_output": "...",         // Optional: Output from test execution
  "pr_output": "...",           // Optional: Output from PR creation
  "error_details": "..."        // Optional: Error details if applicable
}
```

## Workflow Steps

1. **File Copying**: Copies content from `extracted_files/` to `android-testcase-runner/features/`
2. **Test Execution**: Runs `node test-mcp-enhanced.js ../android-testcase-runner`
3. **PR Creation** (optional): Runs `node test-pr-creation.js ../android-testcase-runner`

## Usage Examples

### 1. Execute Tests Only (No PR)

```bash
curl -X POST "http://localhost:8000/execute-workflow/" \
  -H "Content-Type: application/json" \
  -d '{"auto_create_pr": false}'
```

### 2. Execute Tests and Create PR

```bash
curl -X POST "http://localhost:8000/execute-workflow/" \
  -H "Content-Type: application/json" \
  -d '{"auto_create_pr": true}'
```

### 3. Using Python Client

```python
import requests

# Test execution only
response = requests.post(
    "http://localhost:8000/execute-workflow/",
    json={"auto_create_pr": False}
)

# Test execution + PR creation
response = requests.post(
    "http://localhost:8000/execute-workflow/",
    json={"auto_create_pr": True}
)
```

## Response Status Types

- **`success`**: All requested operations completed successfully
- **`failed`**: Critical failure (file copying or test execution failed)
- **`partial_success`**: Tests passed but PR creation failed

## Prerequisites

1. **Directory Structure**: Parallel projects must exist:
   ```
   /Users/A-10710/Documents/IBS/AI/
   ├── TestAutomationAgent/           # Current project
   ├── android-testcase-runner/       # Target project
   └── github-mcp-code-reviewer/      # Test executor
   ```

2. **Node.js Scripts**: Required scripts in `github-mcp-code-reviewer`:
   - `test-mcp-enhanced.js`
   - `test-pr-creation.js`

3. **Files to Copy**: Content in `TestAutomationAgent/extracted_files/`

## Testing

1. **Start the API Server**:
   ```bash
   python api.py
   ```

2. **Run Test Client**:
   ```bash
   python test_workflow_client.py
   ```

3. **Check Health**:
   ```bash
   curl http://localhost:8000/health
   ```

## Error Handling

The API provides comprehensive error handling:

- **Project Validation**: Checks if parallel projects exist
- **File Operations**: Handles file copying errors gracefully
- **Subprocess Management**: Manages Node.js script execution with timeouts
- **Directory Safety**: Always returns to original directory

## Integration with Existing API

The workflow endpoint is integrated into the main API (`api.py`) alongside existing endpoints:

- `/run-test/`: Original test execution
- `/text-to-json/`: NLP to JSON conversion
- `/execute-workflow/`: **New workflow endpoint**
- `/health`: Health check

## Standalone Usage

The workflow API can also run independently:

```bash
python test_workflow_api.py  # Runs on port 8001
```