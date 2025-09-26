
import configparser
import os
import boto3
import json
import importlib.util
import sys
from botocore.exceptions import ClientError
from aws_config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN, region_name

def get_prompt_rules():
    spec = importlib.util.spec_from_file_location("constants", os.path.join(os.path.dirname(__file__), "constants.py"))
    constants = importlib.util.module_from_spec(spec)
    sys.modules["constants"] = constants
    spec.loader.exec_module(constants)
    PROMPT_RULES = constants.PROMPT_RULES
    return PROMPT_RULES.strip()

model_id = "qwen.qwen3-coder-480b-a35b-v1:0"
# Create an Amazon Bedrock Runtime client.

# Initialize Bedrock client with credentials
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name=region_name,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN
)

def get_apk_path():
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'app.properties'))
    apk_path = config['DEFAULT'].get('APK_PATH') if 'DEFAULT' in config and 'APK_PATH' in config['DEFAULT'] else None
    if not apk_path:
        raise ValueError("APK_PATH not found in app.properties")
    return apk_path

def fetch_llm_response(prompt):
    # Placeholder for LLM integration
    # In a real implementation, this would call an LLM API like OpenAI's GPT
    request_payload = {
    "messages": [
        {
            "role": "user",
            "content": prompt
        }
    ],
    "temperature": 0.5,
    "max_tokens": 512,
    "top_p": 0.9
    }

    try:
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(request_payload),
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response["body"].read())

        # Extract content
        response_text = response_body["choices"][0]["message"]["content"]
        print(response_text)
        return response_text

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        exit(1)