import configparser
import os
import time
import boto3
import json
import importlib.util
import sys
from botocore.exceptions import ClientError
from aws_config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN, region_name
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import tiktoken


model_id = "qwen.qwen3-coder-480b-a35b-v1:0"
# Create an Amazon Bedrock Runtime client.

output_file_name = "generated_code.txt"

# Initialize Bedrock client with credentials
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name=region_name,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN
)

request_payload = {
    "messages": [
        {
            "role": "user",
            "content": ""
        }
    ],
    "temperature": 0.5,
    "max_tokens": 512,
    "top_p": 0.9
    }

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
    countToken(prompt)
    request_payload["messages"][0]["content"] = prompt

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
        return response_text

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        exit(1)


def append_to_file(text):
    with open(output_file_name, "a") as file:
        file.write(text + "\n")

def delete_output_file():
    if os.path.exists(output_file_name):
        os.remove(output_file_name)
        print(f"{output_file_name} has been deleted.")

def initiate_appium_driver():
    # Appium driver setup
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.device_name = "Android Emulator"
    # Load APK path from utility function
    options.app = get_apk_path()
    options.app_package = "com.expedia.bookings"
    options.app_activity = "com.expedia.bookings.activity.SearchActivity"
    #options.new_command_timeout = 3000  # <-- Increase timeout here

    return webdriver.Remote("http://localhost:4723", options=options)

def execute_appium_code(driver, code):
    exec(code, {
                "driver": driver,
                "time": time,
                "By": By,
                "AppiumBy": AppiumBy,
                "WebDriverWait": WebDriverWait,
                "EC": EC
            }
        )
def countToken(text): 
    enc = tiktoken.encoding_for_model("gpt-4")
    tokens = enc.encode(text)
    print("Token count:", len(tokens))