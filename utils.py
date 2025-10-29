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
from constants import PROMPT_RULES_CUCUMBER,PROMPT_RULES_POM,PROMPT_RULES_TEST_CODE, PROMPT_RULES_CLASS_CREATE, PROMPT_RULES_CONTENT_CORELATION, MAX_RETRY_ATTEMPTS, EXTRACT_CLASS_NAME_RULES

model_id = "qwen.qwen3-coder-480b-a35b-v1:0"
# Create an Amazon Bedrock Runtime client.

output_file_name = "generated_code.txt"
file_name_cucumber = "generated_script_cucumber.txt"
file_name_pom = "generated_script_pom.txt"
file_name = "generated_script.txt"
file_name_consolidated_cucumber = ".feature"
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
    "max_tokens": 8192,
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

        #print("Response from Bedrock:", response_text)
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

def delete_output_folder(test_case_id):    
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

def is_stale_element_error(error_msg):
    """Check if the error is related to stale elements."""
    stale_indicators = [
        "stale", 
        "cached elements", 
        "do not exist in dom", 
        "element is no longer attached",
        "element not found",
        "no such element",
        "StaleElementReferenceException",
        "ElementsCache.restore",
        "ElementsCache.get"
    ]
    return any(indicator in error_msg.lower() for indicator in stale_indicators)

def execute_appium_code(driver, code):
    """Execute Appium code with proper exception handling for stale elements."""
    max_retries = MAX_RETRY_ATTEMPTS
    for attempt in range(max_retries):
        try:
            exec(code, {
                        "driver": driver,
                        "time": time,
                        "By": By,
                        "AppiumBy": AppiumBy,
                        "WebDriverWait": WebDriverWait,
                        "EC": EC
                    }
                )
            return  # Success, exit
        except Exception as e:
            error_msg = str(e)
            if is_stale_element_error(error_msg):
                print(f"⚠️ Detected stale element error (attempt {attempt + 1}/{max_retries}): {error_msg}")
                if attempt < max_retries - 1:
                    print("🔄 Waiting for DOM to stabilize and retrying...")
                    time.sleep(3)  # Wait longer for DOM to stabilize
                    continue
                else:
                    print(f"❌ Code execution failed after {max_retries} attempts due to persistent stale elements")
                    raise Exception(f"Persistent stale element error: {error_msg}")
            else:
                # Non-stale error, re-raise immediately
                raise e
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

    delete_output_folder(test_case_id)

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
    output_dir = "extracted_files/"+test_case_id+"/files/page-objects"
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

    # Check if all classes were successfully created
    missing_classes = []
    for class_name in class_names:
        class_file_path = os.path.join(output_dir, f"{class_name}.js")
        if not os.path.exists(class_file_path):
            missing_classes.append(class_name)
    
    # If there are missing classes, try to extract them again with retry logic
    if missing_classes:
        print(f"⚠️ Missing class files: {missing_classes}")
        
        max_retries = 3
        still_missing = missing_classes.copy()
        
        for retry_attempt in range(max_retries):
            if not still_missing:
                break
                
            print(f"🔄 Retry attempt {retry_attempt + 1}/{max_retries} for missing classes: {still_missing}")
            newly_created = []
            
            for class_name in still_missing:
                print(f"🔄 Retrying extraction for class: {class_name}")
                class_file_path = os.path.join(output_dir, f"{class_name}.js")
                class_code = extract_refactored_class_code(source_code, class_name)
                
                if class_code and "Class not found" not in class_code and "ERROR" not in class_code:
                    with open(class_file_path, "w") as class_file:
                        class_file.write(class_code)
                    print(f"✅ Successfully created file for class: {class_name} on retry {retry_attempt + 1}")
                    newly_created.append(class_name)
                else:
                    print(f"❌ Failed to extract class: {class_name} on retry {retry_attempt + 1}")                    
            
            # Update still_missing list by removing successfully created classes
            still_missing = [cls for cls in still_missing if cls not in newly_created]
            
            if still_missing and retry_attempt < max_retries - 1:
                print(f"⏳ Waiting before next retry attempt...")
                time.sleep(2)  # Brief delay between retries
        
        # Final check and error logging for any remaining missing classes
        if still_missing:
            print(f"❌ Failed to create files for classes after {max_retries} attempts: {still_missing}")
            for class_name in still_missing:
                error_log = f"Failed to extract class '{class_name}' from source code after {max_retries} retry attempts. Trying with manual intervention."
                print(f"ERROR: {error_log}")

                for class_name in still_missing:
                    class_file_path = os.path.join(output_dir, f"{class_name}.js")
                    extract_single_class(source_code, class_name, class_file_path)
        else:
            print("✅ All missing classes were successfully created after retries.")
    else:
        print("✅ All classes were successfully created on first attempt.")


    # Check if all classes were successfully created
    missing_classes = []
    for class_name in class_names:
        class_file_path = os.path.join(output_dir, f"{class_name}.js")
        if not os.path.exists(class_file_path):
            missing_classes.append(class_name)

    if missing_classes:    
        print(f"⚠️ Missing class files post ALL methods: {missing_classes}")
        

    # Remove the temporary Classes.js file
    remove_classes_file = os.path.join(output_dir, f"Classes.js")
    if os.path.exists(remove_classes_file):
        os.remove(remove_classes_file)
        print(f"Removed temporary Classes.js file at {remove_classes_file}")


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
        #print("invoken AWS bedrock for Class Only start: ")
        #print(response_text)
        response_text = extract_tag_content("ClassFile", response_text)
        #print("invoken AWS bedrock for Class Only end: ")
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
        #print(response_text)
        print("invoken AWS bedrock for POM end: ")
        return response_text;
    except (ClientError, Exception) as e:
        return "ERROR: Can't invoke '{model_id}'. Reason: {e}" 

def extract_class_names_from_file(file_path):
    """
    Extract class names from a JavaScript/TypeScript file containing Page Object Model classes.
    Uses both regex-based and LLM-based extraction methods for comprehensive results.
    
    Args:
        file_path (str): Path to the file to analyze
        
    Returns:
        list: List of unique class names found in the file using both methods
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Method 1: Regex-based extraction
        print("🔍 Extracting class names using regex...")
        class_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{'
        regex_matches = re.findall(class_pattern, content)
        print(f"📋 Regex found classes: {regex_matches}")
        
        # Method 2: LLM-based extraction
        llm_classes = extract_class_names_with_llm(content)
        
        # Method 3: Combine and deduplicate results
        print("🔄 Combining results from both methods...")
        all_classes = regex_matches + llm_classes
        
        # Remove duplicates while preserving order
        unique_classes = []
        seen = set()
        for class_name in all_classes:
            if class_name not in seen and class_name:  # Ensure non-empty class names
                unique_classes.append(class_name)
                seen.add(class_name)
        
        print(f"✅ Final unique class list: {unique_classes}")
        print(f"📊 Total classes found: {len(unique_classes)} (Regex: {len(regex_matches)}, LLM: {len(llm_classes)})")
        
        return unique_classes
        
    except Exception as e:
        print(f"❌ Error reading file {file_path}: {e}")
        return []



def extract_and_create_testclass(source_code, test_case_id ):
    output_dir = "extracted_files/"+test_case_id+"/files/step-definitions"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_path = os.path.join(output_dir, f"test-case-{test_case_id}.js")

    with open(file_path, "w") as file:
        file.write(source_code + "\n")  

def writeTofileCucumberFeature(code_to_write,test_case_id):    
    output_dir = "extracted_files/"+test_case_id+"/files"
    os.makedirs(output_dir, exist_ok=True)

    if code_to_write and code_to_write.strip():         
        filename = os.path.join(output_dir, "test-case-"+test_case_id+file_name_consolidated_cucumber)
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
        print("invoken AWS bedrock for BDD start: ")
        #print(response_text)
        print("invoken AWS bedrock for BDD end: ")
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
        #print(response_text)
        print("invoken AWS bedrock for test code end: ")
        return response_text;
    except (ClientError, Exception) as e:
        return "ERROR: Can't invoke '{model_id}'. Reason: {e}"   
    
# Execute each step
def log_ui_elements(ui_elements, title):
    print(f"\n📍 {title}:")
    for e in ui_elements:
        print(f"  Text: {e['text']}, Resource-ID: {e['resource_id']}, Content-Desc: {e['content_desc']}")   

def process_generated_code(driver, generated_code, generated_code_raw):
        execute_appium_code(driver, generated_code)
        print(f"\n💡 Formatted code : \n{generated_code}")
        print(f"\n💡 Formatted code ended: ")

        append_to_file(generated_code)

        fetureDetails = extract_tag_content("FeatureDetails", generated_code_raw)
        pomDetails = extract_tag_content("POMDetails", generated_code_raw)


        corelated_code = clean_and_extract_corelated_code(fetureDetails, pomDetails)

        fetureDetails = extract_tag_content("FeatureDetails", corelated_code)
        pomDetails = extract_tag_content("POMDetails", corelated_code)

        writeTofileCucumber(fetureDetails)
        writeTofileCucumber("\n")

        
        writeTofilePom(pomDetails)
        writeTofilePom("\n") 
        
def check_if_page_scrollable(driver):
    """Check if the current page/screen is scrollable."""
    try:
        # Method 1: Check for scrollable elements using UiAutomator
        scrollable_elements = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, 
            'new UiSelector().scrollable(true)')
        
        if scrollable_elements:
            print(f"✅ Page is scrollable - Found {len(scrollable_elements)} scrollable containers")
            return True
        
        # Method 2: Check for common scrollable view classes
        scrollable_classes = [
            'android.widget.ScrollView',
            'android.widget.ListView', 
            'android.widget.RecyclerView',
            'androidx.recyclerview.widget.RecyclerView',
            'android.support.v7.widget.RecyclerView'
        ]
        
        for class_name in scrollable_classes:
            elements = driver.find_elements(By.CLASS_NAME, class_name)
            if elements:
                print(f"✅ Page is scrollable - Found {class_name}")
                return True
        
        # Method 3: Check viewport vs content size (if available)
        try:
            screen_size = driver.get_window_size()
            # Try to detect if content extends beyond screen
            all_elements = driver.find_elements(By.XPATH, "//*")
            max_y = 0
            for element in all_elements:
                try:
                    location = element.location
                    size = element.size
                    element_bottom = location['y'] + size['height']
                    max_y = max(max_y, element_bottom)
                except:
                    continue
            
            if max_y > screen_size['height']:
                print(f"✅ Page is scrollable - Content height ({max_y}) > Screen height ({screen_size['height']})")
                return True
        except:
            pass
            
        print("❌ Page does not appear to be scrollable")
        return False
        
    except Exception as e:
        print(f"⚠️ Error checking scrollability: {e}")
        return False
    

    

def clean_and_extract_corelated_code(featureFileContent, pomFileContent):
    with open(file_name_pom, "r") as f:
            raw_code = f.read()

    prompt = f"""
You are a code extraction assistant.

{PROMPT_RULES_CONTENT_CORELATION}
    
Here is feature code:
{featureFileContent}
Here is the pom code:
{pomFileContent}
"""
    try:
        response_text = fetch_llm_response(prompt)
        #print("invoken AWS bedrock for Gherkin start: ")
        #print(response_text)
        #print("invoken AWS bedrock for Gherkin end: ")
        return response_text;
    except (ClientError, Exception) as e:
        return "ERROR: Can't invoke '{model_id}'. Reason: {e}"   


# Regex to extract classes with their full body (handles nested braces roughly)
class_pattern = re.compile(r'class\s+(\w+)\s*{([^}]*(?:}(?!\s*class)[^}]*)*)}', re.DOTALL)

# Regex to extract getters (properties)
getter_pattern = re.compile(r'get\s+(\w+)\s*\([^)]*\)\s*{([^}]*)}', re.DOTALL)

# Regex to extract methods (async or not)
method_pattern = re.compile(r'(async\s+)?(\w+)\s*\([^)]*\)\s*{([^}]*)}', re.DOTALL)

def extract_single_class(source_code, class_name, output_path):
    # Extract the specific class
    class_match = re.search(rf'class\s+{re.escape(class_name)}\s*{{([^}}]*(?:}}(?!\s*class)[^}}]*)*)', source_code, re.DOTALL)
    
    if not class_match:
        print(f"Class {class_name} not found in source code")
        return False
    
    class_body = class_match.group(1)
    
    # Extract getters and methods from the class body
    properties = getter_pattern.findall(class_body)
    methods = method_pattern.findall(class_body)
    
    # Filter out getters from methods (since method_pattern also matches getters)
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

    output = single_class_refactor(output, class_name)
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to file
    with open(output_path, "w") as f:
        f.write(output)
    
    print(f"Extracted class {class_name} to {output_path}")
    return True

def single_class_refactor(raw_code, class_name):
    prompt = f"""
You are a code formatting and extraction assistant.

Code:
{raw_code}

1. Refactor the complete code for the class named '{class_name}'.
2. Provide only the code for the class '{class_name}'.
3. If the class '{class_name}' is not found, respond with 'Class not found'.
{PROMPT_RULES_CLASS_CREATE}
"""

    try:
        response_text = fetch_llm_response(prompt)
        #print("invoken AWS bedrock for Class Only start: ")
        #print(response_text)
        response_text = extract_tag_content("ClassFile", response_text)
        #print("invoken AWS bedrock for Class Only end: ")
        return response_text;
    except (ClientError, Exception) as e:
        return "ERROR: Can't invoke '{model_id}'. Reason: {e}"


def extract_class_names_with_llm(content):
    """
    Extract class names from JavaScript/TypeScript code using LLM.
    
    Args:
        content (str): The code content to analyze

    Returns:
        list: List of class names found by the LLM
    """
    print("🤖 Extracting class names using LLM...")
    llm_classes = []
    try:
        prompt = f"""
        You are a code analysis assistant. Extract all class names from the following JavaScript/TypeScript code.

        Code:
        {content}

        Instructions:
        {EXTRACT_CLASS_NAME_RULES}

        Example format: ClassName1, ClassName2, ClassName3
        """

        llm_response = fetch_llm_response(prompt)

        if llm_response and "NO_CLASSES_FOUND" not in llm_response.upper():
            # Parse LLM response to extract class names
            llm_class_text = llm_response.strip()
            # Split by comma and clean up whitespace
            llm_classes = [name.strip() for name in llm_class_text.split(',') if name.strip()]
            # Filter out any non-class-like names (basic validation)
            llm_classes = [name for name in llm_classes if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name)]
            print(f"🤖 LLM found classes: {llm_classes}")
        else:
            print("🤖 LLM found no classes")

    except Exception as llm_error:
        print(f"⚠️ LLM extraction failed: {llm_error}")
        llm_classes = []

    return llm_classes


def detect_current_screen(driver):
            # Use UIAutomator or other means to get the current screen's activity name
            current_activity = driver.current_activity
            return current_activity

def clean_refactored_code(raw):
    raw = re.sub(r'<reasoning>.*?</reasoning>', '', raw, flags=re.DOTALL | re.IGNORECASE)

    raw = raw.replace(";;", ";")
    raw = raw.replace("..", ".")
    raw = raw.replace("?.", ".")
    
    """Remove markdown code blocks and keep only Python code."""    
    code_match = re.search(r"```(?:python)?\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    
    if code_match:
        return code_match.group(1).strip()
    return raw.strip()

def log_ui_elements(ui_elements, title):
    """Log UI elements with their details."""
    print(f"L188: \n📍 {title}:")
    for e in ui_elements:
        if(e['class']=="android.widget.Button"):
            print(f"L190:   Text: {e['text']}, Resource-ID: {e['resource_id']}, Content-Desc: {e['content_desc']}, Class: {e['class']}, Focusable: {e['focusable']}, Enabled: {e['enabled']}, Focused: {e['focused']}, Selected: {e['selected']}")

# Helper: remove elements with null/empty/"None" resource_id
def remove_unwanted_elements(ui_elements):
    return [e for e in ui_elements if e.get("resource_id") != "null" or e.get("content_desc") != "null" or e.get("text")]
