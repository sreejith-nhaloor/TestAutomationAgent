from utils import *
from constants import PROMPT_RULES, MAX_RETRY_ATTEMPTS, SCROLL_COMMANDS
from github_client import create_pull_request
import time
import re
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy
from models import TestCase
from models import TestResult
max_retry_attempts = MAX_RETRY_ATTEMPTS

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

def safe_driver_operation(operation, max_retries=3, wait_time=2):
    """Safely execute any driver operation with automatic retry on stale element errors."""
    for attempt in range(max_retries):
        try:
            return operation()
        except Exception as e:
            error_msg = str(e)
            if is_stale_element_error(error_msg):
                print(f"⚠️ Stale element error (attempt {attempt + 1}/{max_retries}): {error_msg}")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Operation failed after {max_retries} attempts due to persistent stale elements")
                    raise e
            else:
                # Non-stale error, re-raise immediately
                raise e
    return None

def safe_find_elements(driver, by, value, max_retries=3):
    """Safely find elements with automatic retry on stale element errors."""
    for attempt in range(max_retries):
        try:
            elements = driver.find_elements(by, value)
            return elements
        except Exception as e:
            if is_stale_element_error(str(e)) and attempt < max_retries - 1:
                print(f"⚠️ Stale element error in find_elements (attempt {attempt + 1}), retrying...")
                time.sleep(1)
                continue
            else:
                raise e
    return []

def perform_safe_scroll(driver, max_retries=3):
    """Perform scrolling with retry logic for stale element errors."""
    scroll_methods = [
        # Method 1: Simple UiScrollable scrollForward
        lambda: driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 
            'new UiScrollable(new UiSelector().scrollable(true)).scrollForward()'),
        # Method 2: UiScrollable with flingForward  
        lambda: driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiScrollable(new UiSelector().scrollable(true)).flingForward()'),
        # Method 3: UiScrollable with scrollToEnd
        lambda: driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiScrollable(new UiSelector().scrollable(true)).scrollToEnd(10)'),
        # Method 4: Direct swipe gesture (fallback)
        lambda: driver.swipe(500, 1500, 500, 500, 1000)
    ]
    
    for method_idx, scroll_method in enumerate(scroll_methods):
        for attempt in range(max_retries):
            try:
                scroll_method()
                print(f"✅ Scroll successful using method {method_idx + 1}")
                time.sleep(1)  # Small wait after successful scroll
                return True
            except Exception as e:
                error_msg = str(e)
                if is_stale_element_error(error_msg):
                    print(f"⚠️ Stale element error in scroll method {method_idx + 1} (attempt {attempt + 1}): {error_msg}")
                    if attempt < max_retries - 1:
                        time.sleep(2)  # Wait for DOM to stabilize
                        continue
                    else:
                        print(f"❌ Scroll method {method_idx + 1} failed after {max_retries} attempts")
                        break
                else:
                    print(f"⚠️ Non-stale error in scroll method {method_idx + 1}: {error_msg}")
                    if method_idx < len(scroll_methods) - 1:  # Try next method
                        break
                    else:
                        print(f"❌ Last scroll method failed: {error_msg}")
                        break
    
    print("❌ All scroll methods failed")
    return False

def extract_ui_elements_with_retry(driver, max_retries=3):
    """Extract UI elements with enhanced retry logic for stale element errors."""
    for attempt in range(max_retries):
        try:
            ui_elements = extract_ui_elements(driver)
            if ui_elements:  # Only return if we got some elements
                return ui_elements
            else:
                print(f"⚠️ No elements found (attempt {attempt + 1}), retrying...")
                time.sleep(2)
        except Exception as e:
            error_msg = str(e)
            if is_stale_element_error(error_msg):
                print(f"⚠️ Stale element error in extract_ui_elements (attempt {attempt + 1}): {error_msg}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
            else:
                print(f"❌ Non-stale error in extract_ui_elements: {error_msg}")
                break
    
    print("❌ Failed to extract UI elements after all retries")
    return []

def ui_elements_equal(elements1, elements2):
    """Compare two UI element lists to check if they're essentially the same."""
    if len(elements1) != len(elements2):
        return False
    
    # Create simplified representations for comparison
    def simplify_element(element):
        return (
            element.get('text', ''),
            element.get('resource_id', ''),
            element.get('content_desc', ''),
            element.get('class', ''),
            element.get('bounds', '')
        )
    
    simplified1 = [simplify_element(e) for e in elements1]
    simplified2 = [simplify_element(e) for e in elements2]
    
    # Sort both lists to handle order differences
    simplified1.sort()
    simplified2.sort()
    
    return simplified1 == simplified2

def check_if_page_scrollable(driver):
    """Check if the current page/screen is scrollable."""
    try:
        # Method 1: Check for scrollable elements using UiAutomator
        try:
            scrollable_elements = safe_driver_operation(
                lambda: driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, 
                    'new UiSelector().scrollable(true)'))
            
            if scrollable_elements:
                print(f"L105: ✅ Page is scrollable - Found {len(scrollable_elements)} scrollable containers")
                return True
        except Exception as ui_error:
            print(f"L109: ⚠️ UiAutomator scrollable check failed: {ui_error}")
        
        # Method 2: Check for common scrollable view classes
        scrollable_classes = [
            'android.widget.ScrollView',
            'android.widget.ListView', 
            'android.widget.RecyclerView',
            'androidx.recyclerview.widget.RecyclerView',
            'android.support.v7.widget.RecyclerView'
        ]
        
        for class_name in scrollable_classes:
            try:
                elements = safe_driver_operation(
                    lambda: driver.find_elements(By.CLASS_NAME, class_name))
                if elements:
                    print(f"L123: ✅ Page is scrollable - Found {class_name}")
                    return True
            except Exception as class_error:
                print(f"L126: ⚠️ Error checking class {class_name}: {class_error}")
                continue
        
        # Method 3: Check viewport vs content size (if available)
        try:
            screen_size = safe_driver_operation(lambda: driver.get_window_size())
            all_elements = safe_driver_operation(
                lambda: driver.find_elements(By.XPATH, "//*"))
            max_y = 0
            for element in all_elements:
                try:
                    location = safe_driver_operation(lambda: element.location)
                    size = safe_driver_operation(lambda: element.size)
                    element_bottom = location['y'] + size['height']
                    max_y = max(max_y, element_bottom)
                except Exception as element_error:
                    # Skip problematic elements
                    if is_stale_element_error(str(element_error)):
                        continue
                    else:
                        raise element_error
            
            if max_y > screen_size['height']:
                print(f"L147: ✅ Page is scrollable - Content height ({max_y}) > Screen height ({screen_size['height']})")
                return True
        except Exception as size_error:
            print(f"L150: ⚠️ Error checking content size: {size_error}")
            pass
            
        print("L153: ❌ Page does not appear to be scrollable")
        return False
        
    except Exception as e:
        print(f"L157: ⚠️ Error checking scrollability: {e}")
        return False



def extract_ui_elements(driver):
    """Grab all UI elements with their key attributes."""
    try:
        elements = safe_find_elements(driver, By.XPATH, "//*")
        print("L135: Total elements found:", len(elements))
    except Exception as e:
        print(f"L137: ⚠️ Error finding elements, retrying: {e}")
        time.sleep(2)
        try:
            elements = safe_find_elements(driver, By.XPATH, "//*")
            print("L141: Total elements found on retry:", len(elements))
        except Exception as retry_e:
            print(f"L143: ❌ Failed to find elements on retry: {retry_e}")
            return []
    
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

    print("L150: Interactable elements found:", len(elements))
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
            print(f"L146: Error reading element (possibly stale): {e}")
            # Skip stale elements instead of failing completely
            continue
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

def log_ui_elements(ui_elements, title):
    """Log UI elements with their details."""
    print(f"L188: \n📍 {title}:")
    for e in ui_elements:
        if(e['class']=="android.widget.Button"):
            print(f"L190:   Text: {e['text']}, Resource-ID: {e['resource_id']}, Content-Desc: {e['content_desc']}, Class: {e['class']}, Focusable: {e['focusable']}, Enabled: {e['enabled']}, Focused: {e['focused']}, Selected: {e['selected']}")

def process_generated_code(driver, generated_code, generated_code_raw):
    """Process and execute the generated code, then save to files."""
    execute_appium_code(driver, generated_code)
    print(f"L195: \n💡 Formatted code : \n{generated_code}")
    print(f"L196: \n💡 Formatted code ended: ")

    append_to_file(generated_code)
    
    fetureDetails = extract_tag_content("FeatureDetails", generated_code_raw)
    writeTofileCucumber(fetureDetails)
    writeTofileCucumber("\n")

    pomDetails = extract_tag_content("POMDetails", generated_code_raw)
    writeTofilePom(pomDetails)
    writeTofilePom("\n")

def run_test(test_case: TestCase) -> TestResult:
    print("L208: 🚀 Running: Multi-step test")
    
    driver = initiate_appium_driver()
    time.sleep(5)

    # steps = TEST_STEPS
    steps = test_case.steps
    test_case_id = str(test_case.test_case_id)
    
    print(f"L217: Test Case ID: {str(test_case_id)}")
    return_exception: any = None
    return_status: str = "success"
    pr_url = "ERROR"
    
    delete_output_file(test_case_id)  # Clear previous output file
    
    for idx, step in enumerate(steps, start=1):
        print(f"L224: \n🔹 Step {idx}: {step}")
        ui_elements = extract_ui_elements(driver)
        #current_screen = detect_current_screen(driver)
        
        #print(f"L228: \n🖥️ Current Screen Source: {current_screen[:5000]}...")  # Log first 500 chars

        #log_ui_elements(ui_elements, "Available selectors on this page")
        ui_elements = remove_unwanted_elements(ui_elements)
        if(idx>=12):
            log_ui_elements(ui_elements, "Available selectors after filtering")

        return_exception, return_status, ui_elements = execute_test_step(driver, idx, step, ui_elements)        
        
        print(f"L231: ⚠️ Step {idx} status, return_status : {return_status}")
        # If step failed, check if page is scrollable and retry
        if return_status == "failed":
            print(f"L234: ⚠️ Step {idx} status, return_status : {return_status},  going to check for exceptions logic with scroll")
            
            is_scrollable = check_if_page_scrollable(driver)
            
            if is_scrollable:
                return_exception, return_status, ui_elements = attempt_scroll_and_retry(driver, idx, step, ui_elements)
            else:
                print(f"L241: ❌ Page is not scrollable, cannot retry step {idx}")
                
        if return_status == "failed":
            break

        time.sleep(4)  # Small wait between steps

    driver.quit()
        
    if return_status == "success":
        create_files(test_case_id)
        pr_url = create_pull_request()
        elements = "NA"
    else:
        pr_url = "ERROR"
        elements = str(ui_elements)
    
    return TestResult(status=return_status, errors=str(return_exception),pull_request_url=pr_url, elements=elements)

def attempt_scroll_and_retry(driver, idx, step, ui_elements):
    print(f"L255: 📜 Page is scrollable, attempting scroll and retry...")
    original_ui_elements = ui_elements.copy()
    return_exception, return_status = None, "failed"
    max_scroll_attempts = 20
    scroll_attempt = 0

    # Keep scrolling until the set of UI elements stabilizes (no new elements found)
    previous_ui_elements = original_ui_elements
    while scroll_attempt < max_scroll_attempts:
        try:
            # Try scrolling down to reveal more elements with better error handling
            scroll_success = perform_safe_scroll(driver)
            if not scroll_success:
                print(f"L266: ⚠️ Scroll operation failed, stopping scroll attempts for step {idx}")
                break

            # Wait for DOM to stabilize after scrolling
            time.sleep(2)
            
            # Extract new UI elements after scrolling with retry logic
            ui_elements_after_scroll = extract_ui_elements_with_retry(driver)
            ui_elements_after_scroll = remove_unwanted_elements(ui_elements_after_scroll)

            if(idx>=12):
                log_ui_elements(ui_elements_after_scroll, "Available selectors after filtering")

            # If the UI elements after scroll are the same as previous, stop scrolling
            if ui_elements_equal(previous_ui_elements, ui_elements_after_scroll):
                print(f"L280: ⚠️ Scrolling did not reveal new elements, stopping scroll attempts for step {idx}, step {step},")
                break
            else:
                print(f"L283: 🔄 Retrying step {idx},  step {step}, with new UI elements after scrolling (attempt {scroll_attempt+1})...")
                return_exception, return_status, ui_elements = execute_test_step(driver, idx, step, ui_elements_after_scroll)

                if return_status == "success":
                    print(f"L287: ✅ Step {idx},  step {step}, succeeded after scrolling!")
                    break
                else:
                    print(f"L290: ❌ Step {idx},  step {step}, still failed after scrolling, will try to scroll again.")
                    previous_ui_elements = ui_elements_after_scroll
                    scroll_attempt += 1
        except Exception as scroll_error:
            print(f"L294: ⚠️ Error during scrolling: {scroll_error}")
            if is_stale_element_error(str(scroll_error)):
                print(f"L296: 🔄 Stale element error detected, waiting and retrying scroll...")
                time.sleep(3)  # Wait longer for DOM to stabilize
                scroll_attempt += 1
                continue
            else:
                print(f"L300: ❌ Non-stale error during scrolling, stopping attempts")
                break        

    return return_exception, return_status, ui_elements

def execute_test_step(driver, idx, step, ui_elements):
    attempt = 0
    last_exception = None
    return_exception = None
    return_status = "success"
    print(f"L298: ⚠️  execute_test_step in step {idx}, attempt {attempt+1} ")
    while attempt < max_retry_attempts:
        # Generate step-specific code, passing exception if any
        generated_code_raw = resolve_actions_with_ui(step, ui_elements if attempt == 0 else ui_elements, last_exception)
        generated_code = clean_generated_code(generated_code_raw)
        if generated_code.strip():
            try:
                process_generated_code(driver, generated_code, generated_code_raw)
                return_status = "success"
                break  # Success, exit retry loop
            except Exception as e:
                error_msg = str(e)
                print(f"L320: ❌ Error in step {idx},  step {step}, attempt {attempt+1} generated code: {generated_code}: {e}")
                last_exception = e
                
                # Check if it's a stale element error
                if is_stale_element_error(error_msg):
                    print(f"L325: 🔄 Detected stale element error, refreshing UI elements...")
                    # Refresh UI elements immediately for stale element errors
                    ui_elements = extract_ui_elements(driver)
                    ui_elements = remove_unwanted_elements(ui_elements)
                    
                attempt += 1       

                # Only refresh UI elements if not already refreshed due to stale element error
                if not is_stale_element_error(error_msg):
                    ui_elements = extract_ui_elements(driver)     
                if attempt == 3:
                    return_exception = e
                    return_status = "failed"
                    break
        else:
            print(f"L340: ❌ No valid code generated for step {idx},  step {step}, retrying... attempt {attempt+1}")
            last_exception = "No valid code generated"
            attempt += 1            
            if attempt == 3:
                return_exception = "No valid code generated"
                return_status = "failed"
                break

        time.sleep(4)  # Small wait between steps
        
    return return_exception, return_status, ui_elements

