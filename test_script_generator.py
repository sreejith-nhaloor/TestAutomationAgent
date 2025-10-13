from utils import *
from constants import PROMPT_RULES, MAX_RETRY_ATTEMPTS
from github_client import create_pull_request
import time
import re
from selenium.webdriver.common.by import By
from models import TestCase
from models import TestResult
max_retry_attempts = MAX_RETRY_ATTEMPTS

def extract_ui_elements(driver):
    """Grab all UI elements with their key attributes."""
    elements = driver.find_elements(By.XPATH, "//*")
    print("Total elements found:", len(elements))
    # for el in elements:
    #     print("...."+el.get_attribute("className")+"..."+el.text+"...."+el.get_attribute("contentDescription"))

    # Define interactable Android UI classes
    interactable_classes = [
        'android.widget.Button',
        'android.widget.EditText',
        'android.widget.CheckBox',
        'android.widget.RadioButton',
        'android.widget.Switch',
        'android.widget.Spinner',
        'android.widget.ImageButton',
        'android.widget.TextView',
        'android.widget.ImageButton',
        'android.view.View',  # Sometimes clickable
    ]

    # Filter interactable elements
    interactable_elements = [
        el for el in elements
        if el.is_displayed()         
        and el.get_attribute("className") in interactable_classes
    ]

    print("Interactable elements found:", len(elements))
    ui_info = []
    for el in elements:
        try:
            ui_info.append({
                "text": el.text,
                "resource_id": el.get_attribute("resource-id"),
                "class": el.get_attribute("className"),
                "content_desc": el.get_attribute("contentDescription"),
                "bounds": el.get_attribute("bounds"),
                "focusable" : el.get_attribute("focusable"),
                "enabled": el.get_attribute("enabled"),                
                "focused": el.get_attribute("focused"),
                "selected": el.get_attribute("selected")
            })
        except Exception as e:
            print(f"Error reading element: {e}")
    return ui_info


def clean_generated_code(raw):
    raw = re.sub(r'<reasoning>.*?</reasoning>', '', raw, flags=re.DOTALL | re.IGNORECASE)

    raw = raw.replace(";;", ";")
    raw = raw.replace("..", ".")
    raw = raw.replace("?.", ".")
    match = re.search(r'<PythonDetails>(.*?)</PythonDetails>', raw, re.DOTALL | re.IGNORECASE)
    if match:
        raw = match.group(1).strip()
    else:
        raw = ""

    """Remove markdown code blocks and keep only Python code."""    
    code_match = re.search(r"```(?:python)?\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    
    if code_match:
        return code_match.group(1).strip()
    return raw.strip()





def resolve_actions_with_ui(nl_step, ui_elements, exception=None):
    context = "\n".join([
        f"Text: {e['text']}, Resource-ID: {e['resource_id']}, Content-Desc: {e['content_desc']}, Focusable: {e['focusable']}, Enabled: {e['enabled']}, Focused: {e['focused']}, Selected: {e['selected']}, Class: {e['class']} "
        for e in ui_elements if e["text"] or e["content_desc"] or e["resource_id"] or e["focusable"] or e['enabled'] or e['focused'] or e['selected'] or e['class']
    ])

    prompt = f"""
You are a UI automation assistant.

Available UI elements:
{context}

{PROMPT_RULES}
Current Exception (if any): {exception}
Step: "{nl_step}"
"""
    return fetch_llm_response(prompt)

# Helper: remove elements with null/empty/"None" resource_id
def remove_unwanted_elements(ui_elements):
    return [e for e in ui_elements if e.get("resource_id") != "null" or e.get("content_desc") != "null" or e.get("text")]

def run_test(test_case: TestCase) -> TestResult:
    print("🚀 Running: Multi-step test")
    driver = initiate_appium_driver()
    time.sleep(5)


    # steps = TEST_STEPS
    steps = test_case.steps
    test_case_id = str(test_case.test_case_id)
    
    print(f"Test Case ID: {str(test_case_id)}")
    return_exception: any = None
    return_status: str = "success"
    
    delete_output_file(test_case_id)  # Clear previous output file
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
        writeTofileCucumber(fetureDetails)
        writeTofileCucumber("\n")

        pomDetails = extract_tag_content("POMDetails", generated_code_raw)
        writeTofilePom(pomDetails)
        writeTofilePom("\n")

    for idx, step in enumerate(steps, start=1):
        print(f"\n🔹 Step {idx}: {step}")
        ui_elements = extract_ui_elements(driver)
        log_ui_elements(ui_elements, "Available selectors on this page")
        ui_elements = remove_unwanted_elements(ui_elements)
        log_ui_elements(ui_elements, "Available selectors after filtering")

        attempt = 0
        last_exception = None        
        while attempt < max_retry_attempts:
            # Generate step-specific code, passing exception if any
            generated_code_raw = resolve_actions_with_ui(step, ui_elements if attempt == 0 else ui_elements, last_exception)
            generated_code = clean_generated_code(generated_code_raw)
            try:
                process_generated_code(driver, generated_code, generated_code_raw)
                break  # Success, exit retry loop
            except Exception as e:
                print(f"❌ Error in step {idx}, attempt {attempt+1}: {e}")
                last_exception = e
                attempt += 1            
                if attempt == 3:
                    return_exception = e
                    return_status = "failed"
                    break
        if return_status == "failed":
            break

        time.sleep(5)  # Small wait between steps

    driver.quit()
    

    if return_status == "success":
        create_files(test_case_id)
        pr_url=create_pull_request()


    return TestResult(status=return_status, errors=str(return_exception),pull_request_url=pr_url)

