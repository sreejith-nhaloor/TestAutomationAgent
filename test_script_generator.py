from utils import fetch_llm_response, get_apk_path, get_prompt_rules
from constants import TEST_STEPS
import xml.etree.ElementTree as ET
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

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
                "bounds": el.get_attribute("bounds")
            })
        except Exception as e:
            print(f"Error reading element: {e}")
    return ui_info


def clean_generated_code(raw):
    print("removing reasoning tag")
    raw = re.sub(r'<reasoning>.*?</reasoning>', '', raw, flags=re.DOTALL | re.IGNORECASE)

    """Remove markdown code blocks and keep only Python code."""    
    code_match = re.search(r"```(?:python)?\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    
    if code_match:
        return code_match.group(1).strip()
    return raw.strip()


def resolve_actions_with_ui(nl_step, ui_elements):
    """Ask the LLM to turn NL into valid Appium code using only known selectors."""
    context = "\n".join([
        f"Text: {e['text']}, Resource-ID: {e['resource_id']}, Content-Desc: {e['content_desc']}"
        for e in ui_elements if e["text"] or e["content_desc"] or e["resource_id"]
    ])

    rules = get_prompt_rules()
    prompt = f"""
You are a UI automation assistant. Create Appium Python code to perform the following step in a mobile app using only the Available UI elements mentioned here.

Available UI elements:
{context}

{rules}

Step: "{nl_step}"
"""
    return fetch_llm_response(prompt)

    


def run_test():
    print("🚀 Running: Multi-step test")

    steps = TEST_STEPS

    # Appium driver setup
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.device_name = "Android Emulator"
    # Load APK path from utility function
    options.app = get_apk_path()
    options.app_package = "com.expedia.bookings"
    options.app_activity = "com.expedia.bookings.activity.SearchActivity"

    driver = webdriver.Remote("http://localhost:4723", options=options)
    time.sleep(5)
    # Helper: remove elements with null/empty/"None" resource_id
    def remove_null_resource_id(ui_elements):
        filtered = []
        for e in ui_elements:
            rid = e.get("resource_id")
            if rid and str(rid).strip().lower() != "null":
                filtered.append(e)
        return filtered

    # Execute each step
    for idx, step in enumerate(steps, start=1):
        print(f"\n🔹 Step {idx}: {step}")

        # Refresh UI elements for the current screen
        ui_elements = extract_ui_elements(driver)

        # Remove elements with null/empty resource_id
        #ui_elements = remove_null_resource_id(ui_elements)

        # Print extracted UI elements for debugging
        print("\n📍 Available selectors on this page:")
        for e in ui_elements:
            print(f"  Text: {e['text']}, Resource-ID: {e['resource_id']}, Content-Desc: {e['content_desc']}")

        # Generate step-specific code
        generated_code_raw = resolve_actions_with_ui(step, ui_elements)
        #generated_code = clean_generated_code(generated_code_raw)

        print(f"\n💡 Generated code:\n{generated_code_raw}")
        #print(f"\n💡 Formatted code:\n{generated_code}")

        try:
            exec(generated_code_raw, {
                "driver": driver,
                "time": time,
                "By": By,
                "AppiumBy": AppiumBy,
                "WebDriverWait": WebDriverWait,
                "EC": EC
            })
        except Exception as e:
            print(f"❌ Error in step {idx}: {e}")
            break

        time.sleep(2)  # Small wait between steps

    driver.quit()


if __name__ == "__main__":
    run_test()
    
