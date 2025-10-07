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
import shutil
import re
from constants import PROMPT_RULES_CUCUMBER,PROMPT_RULES_POM,PROMPT_RULES_TEST_CODE

model_id = "qwen.qwen3-coder-480b-a35b-v1:0"
# Create an Amazon Bedrock Runtime client.

output_file_name = "generated_code.txt"
file_name_cucumber = "generated_script_cucumber.txt"
file_name_pom = "generated_script_pom.txt"
file_name = "generated_script.txt"
file_name_consolidated_cucumber = "complete_flight_booking.feature"
output_dir="extracted_classes/test-script"

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
    "max_tokens": 2048,
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
    with open(file_name_cucumber, "w") as file:
        file.write("")
    with open(file_name_pom, "w") as file:
        file.write("")   
    
    delete_folder("extracted_classes")    

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

def extract_tag_content(tag_name, content):
    
    
    start_tag = f"<{tag_name}>"
    end_tag = f"</{tag_name}>"
    
    start_index = content.find(start_tag)
    end_index = content.find(end_tag)
    
    if start_index == -1 or end_index == -1:
        return None  # Tag not found
    
    # Extract content inside the tag
    return content[start_index + len(start_tag):end_index].strip()  

def writeTofileCucumber(code_to_write):    
    if code_to_write and code_to_write.strip(): 
        with open(file_name_cucumber, "a") as file:
            file.write(code_to_write)
            file.write("\n\n")

def writeTofilePom(code_to_write):    
    if code_to_write and code_to_write.strip(): 
        with open(file_name_pom, "a") as file:
            file.write(code_to_write)   
            file.write("\n\n")    

def delete_folder(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        print(f"Deleted folder: {folder_path}")
    else:
        print(f"Folder not found: {folder_path}")

def create_files():
    cuccumber_feature = clean_and_extract_cuccumber_code()
    cuccumber_feature = extract_tag_content("FeatureTag", cuccumber_feature)
    writeTofileCucumberFeature(cuccumber_feature)    
    
    pom_details = clean_and_extract_pom_code()
    class_pom_details = clean_code_for_classes(pom_details)
    extract_and_create_classes(class_pom_details);

    pom_test_details = clean_and_extract_pom_test_code()
    test_pom_details = clean_code_for_testcode(pom_test_details)
    extract_and_create_testclass(test_pom_details)

def clean_code_for_classes(pom_details):
    return clen_code_for_python_class_extract(extract_tag_content("ClassCode", pom_details))

def clean_code_for_testcode(test_code):
    return extract_tag_content("TestCode", test_code)

def clen_code_for_python_class_extract(raw):
    code_match = re.search(r"```(?:python)?\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    
    if code_match:
        return code_match.group(1).strip()
    return raw.strip()


# Regex to extract classes with their full body (handles nested braces roughly)
class_pattern = re.compile(r'class\s+(\w+)\s*{([^}]*(?:}(?!\s*class)[^}]*)*)}', re.DOTALL)

# Regex to extract getters (properties)
getter_pattern = re.compile(r'get\s+(\w+)\s*\([^)]*\)\s*{([^}]*)}', re.DOTALL)

# Regex to extract methods (async or not)
method_pattern = re.compile(r'(async\s+)?(\w+)\s*\([^)]*\)\s*{([^}]*)}', re.DOTALL)

def extract_and_create_classes(source_code):

    # Extract classes
    classes = class_pattern.findall(source_code)

    output_dir = "extracted_classes/poms"
    os.makedirs(output_dir, exist_ok=True)

    for class_name, class_body in classes:
        properties = getter_pattern.findall(class_body)
        methods = method_pattern.findall(class_body)

        # Filter out getters from methods (since method_pattern also matches getters)
        # We'll exclude methods whose name appears as getter
        method_names = [m[1] for m in methods]
        getter_names = [p[0] for p in properties]
        
        filtered_methods = [m for m in methods if m[1] not in getter_names]

        # Prepare output text
        output = f"class {class_name} {{\n\n"

        # Add getters
        for prop_name, prop_body in properties:
            output += f"  // getter: {prop_name}\n"
            output += f"  get {prop_name}() {{{prop_body.strip()}}}\n\n"

        # Add methods
        for async_kw, method_name, method_body in filtered_methods:
            async_str = async_kw.strip() + " " if async_kw else ""
            output += f"  // method: {method_name}\n"
            output += f"  {async_str}{method_name}() {{{method_body.strip()}}}\n\n"

        output += "}\n"

        # Save to file
        filename = os.path.join(output_dir, f"{class_name}.js")
        with open(filename, "w") as f:
            f.write(output)

        print(f"Extracted class {class_name} to {filename}")


def extract_and_create_testclass(source_code):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_path = os.path.join(output_dir, f"TestRun.js")

    with open(file_path, "w") as file:
        file.write(source_code + "\n")  

def writeTofileCucumberFeature(code_to_write):    
    output_dir = "extracted_classes/feature"
    os.makedirs(output_dir, exist_ok=True)

    if code_to_write and code_to_write.strip():         
        filename = os.path.join(output_dir, file_name_consolidated_cucumber)
        with open(filename, "w") as f:
            f.write(code_to_write)
            f.write("\n\n")    

def clean_and_extract_cuccumber_code():
    with open(file_name_cucumber, "r") as f:
            raw_code = f.read()

    prompt = f"""
You are a UI automation assistant.

Available UI elements:
{raw_code}

{PROMPT_RULES_CUCUMBER}
"""

    try:
        response_text = fetch_llm_response(prompt)
        print("invoken AWS bedrock for Cucumber start: ")
        print(response_text)
        print("invoken AWS bedrock for Cucumber end: ")
        return response_text;
    except (ClientError, Exception) as e:
        return "ERROR: Can't invoke '{model_id}'. Reason: {e}"
    

def clean_and_extract_pom_code():
    with open(file_name_pom, "r") as f:
            raw_code = f.read()

    prompt = f"""
You are a code rewriting assistant.

{PROMPT_RULES_POM}
       
Here is the code:
{raw_code}
"""

    try:
        response_text = fetch_llm_response(prompt)
        print("invoken AWS bedrock for POM start: ")
        print(response_text)
        print("invoken AWS bedrock for POM end: ")
        return response_text;
    except (ClientError, Exception) as e:
        return "ERROR: Can't invoke '{model_id}'. Reason: {e}"    
    
def clean_and_extract_pom_test_code():
    with open(file_name_pom, "r") as f:
            raw_code = f.read()

    prompt = f"""
You are a code extraction assistant.

{PROMPT_RULES_TEST_CODE}
    
Here is the code:
{raw_code}
"""
    try:
        response_text = fetch_llm_response(prompt)
        print("invoken AWS bedrock for test code start: ")
        print(response_text)
        print("invoken AWS bedrock for test code end: ")
        return response_text;
    except (ClientError, Exception) as e:
        return "ERROR: Can't invoke '{model_id}'. Reason: {e}"   
