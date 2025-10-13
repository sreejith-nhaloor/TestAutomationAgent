import configparser
import os
import time
import boto3
import json
from botocore.exceptions import ClientError
from models import TestCase
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from typing import List
import tiktoken
import yaml
import re
import shutil
from constants import PROMPT_RULES_CUCUMBER,PROMPT_RULES_POM,PROMPT_RULES_TEST_CODE, PROMPT_RULES_CLASS_CREATE

model_id = "qwen.qwen3-coder-480b-a35b-v1:0"
# Create an Amazon Bedrock Runtime client.

output_file_name = "generated_code.txt"
file_name_cucumber = "generated_script_cucumber.txt"
file_name_pom = "generated_script_pom.txt"
file_name = "generated_script.txt"
file_name_consolidated_cucumber = "complete_flight_booking.feature"
output_dir="extracted_files"

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Initialize Bedrock client with credentials
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name=config.get('aws', {}).get('region_name'),
    aws_access_key_id=config.get('aws', {}).get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=config.get('aws', {}).get('AWS_SECRET_ACCESS_KEY'),
    aws_session_token=config.get('aws', {}).get('AWS_SESSION_TOKEN')
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

def delete_output_file(test_case_id):
    if os.path.exists(output_file_name):
        os.remove(output_file_name)
        print(f"{output_file_name} has been deleted.")
    with open(file_name_cucumber, "w") as file:
        file.write("")
    with open(file_name_pom, "w") as file:
        file.write("")   
    
    delete_folder("extracted_files/"+test_case_id)

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


def parse_natural_language_steps_to_testcase(nl_text: str) -> List[TestCase]:
    """
    Parses a natural language test case string and returns a TestCase object.
    Extracts steps from lines under **STEPS:**.
    """
    testCaseArray = []
    steps = list()
    in_steps = False
    in_test_case = False
    in_test_case_end = False
    test_case_name = ""
    testCase: TestCase = None
    for line in nl_text.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith('**STEPS:**'):
            in_steps = True
            continue

        if line.startswith('**TEST CASE:**'):
            in_test_case = True
            continue

        if line.startswith('**TEST CASE END:**'):
            in_steps = False
            testCase = TestCase(scenario_name=test_case_name, steps=steps, test_case_id=len(testCaseArray)+1)
            testCaseArray.append(testCase)
            test_case_name = ""
            steps = list()
            continue

        if in_test_case:
            test_case_name = line
            in_test_case = False
            continue

        if in_steps:
            step: Step = Step(description=line, step_id=len(steps)+1)
            steps.append(step)
            continue

    return testCaseArray


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

def create_files(test_case_id):
    cuccumber_feature = clean_and_extract_cuccumber_code()
    cuccumber_feature = extract_tag_content("FeatureTag", cuccumber_feature)
    writeTofileCucumberFeature(cuccumber_feature,test_case_id)    
    
    pom_details = clean_and_extract_pom_code()
    class_pom_details = clean_code_for_classes(pom_details)
    extract_and_create_classes(class_pom_details,test_case_id);

    pom_test_details = clean_and_extract_pom_test_code()
    test_pom_details = clean_code_for_testcode(pom_test_details)
    extract_and_create_testclass(test_pom_details,test_case_id)

def clean_code_for_classes(pom_details):
    return clen_code_for_python_class_extract(extract_tag_content("ClassCode", pom_details))

def clean_code_for_testcode(test_code):
    return extract_tag_content("TestCode", test_code)

def clen_code_for_python_class_extract(raw):
    code_match = re.search(r"```(?:python)?\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    
    if code_match:
        return code_match.group(1).strip()
    return raw.strip()


def extract_and_create_classes(source_code, test_case_id):
    output_dir = "extracted_files/"+test_case_id+"/files/pom"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_path = os.path.join(output_dir, f"Classes.js")

    with open(file_path, "w") as file:
        file.write(source_code + "\n")  

    class_names = extract_class_names_from_file(file_path)
    print(f"Extracted class names: {class_names}")

    for class_name in class_names:
        class_file_path = os.path.join(output_dir, f"{class_name}.js")
        class_code = extract_refactored_class_code(source_code, class_name)
        if class_code and "Class not found" not in class_code and "ERROR" not in class_code:
            with open(class_file_path, "w") as class_file:
                class_file.write(class_code)
            print(f"Created file for class: {class_name} at {class_file_path}")
        else:
            print(f"Skipping file creation for class: {class_name} due to extraction error.")


def extract_refactored_class_code(raw_code, class_name):
    prompt = f"""
You are a code formatting and extraction assistant.

Code:
{raw_code}

1. extract the complete code for the class named '{class_name}'.
2. Provide only the code for the class '{class_name}'.
3. If the class '{class_name}' is not found, respond with 'Class not found'.
{PROMPT_RULES_CLASS_CREATE}
"""

    try:
        response_text = fetch_llm_response(prompt)
        print("invoken AWS bedrock for Class Only start: ")
        print(response_text)
        response_text = extract_tag_content("ClassFile", response_text)
        print("invoken AWS bedrock for Class Only end: ")
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

def extract_class_names_from_file(file_path):
    """
    Extract class names from a JavaScript/TypeScript file containing Page Object Model classes.
    
    Args:
        file_path (str): Path to the file to analyze
        
    Returns:
        list: List of unique class names found in the file
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Regular expression to match class declarations
        # Matches: class ClassName { or class ClassName{
        class_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{'
        
        # Find all class names
        class_matches = re.findall(class_pattern, content)
        
        # Remove duplicates while preserving order
        unique_classes = []
        seen = set()
        for class_name in class_matches:
            if class_name not in seen:
                unique_classes.append(class_name)
                seen.add(class_name)
        
        return unique_classes
        
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []



def extract_and_create_testclass(source_code, test_case_id ):
    output_dir = "extracted_files/"+test_case_id+"/files/test-script"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_path = os.path.join(output_dir, f"TestRun.js")

    with open(file_path, "w") as file:
        file.write(source_code + "\n")  

def writeTofileCucumberFeature(code_to_write,test_case_id):    
    output_dir = "extracted_files/"+test_case_id+"/files/feature"
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
