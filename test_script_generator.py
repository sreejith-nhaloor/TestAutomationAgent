from utils import *
from constants import TEST_STEPS, PROMPT_RULES
import time
import re
from selenium.webdriver.common.by import By

def extract_ui_elements(driver):
    """Grab all UI elements with their key attributes."""
    elements = driver.find_elements(By.XPATH, "//*")
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


def resolve_actions_with_ui(nl_step, ui_elements):
    context = "\n".join([
        f"Text: {e['text']}, Resource-ID: {e['resource_id']}, Content-Desc: {e['content_desc']}, Focusable: {e['focusable']}, Enabled: {e['enabled']}, Focused: {e['focused']}, Selected: {e['selected']}, Class: {e['class']} "
        for e in ui_elements if e["text"] or e["content_desc"] or e["resource_id"] or e["focusable"] or e['enabled'] or e['focused'] or e['selected'] or e['class']
    ])

    prompt = f"""
You are a UI automation assistant.

Available UI elements:
{context}

{PROMPT_RULES}

Step: "{nl_step}"
"""
    return fetch_llm_response(prompt)

# Helper: remove elements with null/empty/"None" resource_id
def remove_unwanted_elements(ui_elements):
    return [e for e in ui_elements if e.get("resource_id") != "null" or e.get("content_desc") != "null" or e.get("text")]

def run_test():
    print("🚀 Running: Multi-step test")
    driver = initiate_appium_driver()
    time.sleep(5)

    delete_output_file()  # Clear previous output file
    # Execute each step
    for idx, step in enumerate(TEST_STEPS, start=1):
        print(f"\n🔹 Step {idx}: {step}")
        ui_elements = extract_ui_elements(driver)
        print("\n📍 Available selectors on this page:")
        for e in ui_elements:
            print(f"  Text: {e['text']}, Resource-ID: {e['resource_id']}, Content-Desc: {e['content_desc']}")
        ui_elements = remove_unwanted_elements(ui_elements)
        print("\n📍 Available selectors after filtering:")
        for e in ui_elements:
            print(f"  Text: {e['text']}, Resource-ID: {e['resource_id']}, Content-Desc: {e['content_desc']}")

        # Generate step-specific code
        generated_code_raw = resolve_actions_with_ui(step, ui_elements)
        generated_code = clean_generated_code(generated_code_raw)
        print(f"\n💡 Generated code:\n{generated_code}")

        try:
            execute_appium_code(driver, generated_code)
            append_to_file(generated_code)
        except Exception as e:
            print(f"❌ Error in step {idx}: {e}")
            break

        time.sleep(2)  # Small wait between steps

    driver.quit()


if __name__ == "__main__":
    run_test()
    
