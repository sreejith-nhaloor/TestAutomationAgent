MAX_RETRY_ATTEMPTS = 3

TEST_STEPS = [
	    "Close the popup by clicking the 'X' button.",
        "If prompted, close the popup by clicking the 'Allow' button.",
        "Close the popup by clicking the 'X' button.",
        "Click on the 'Flights' text or button",
        "Click on the 'One-Way' tab ",
        "Click on the 'Leaving From Button' input field.",
        "Tap on the 'Leaving From' field to activate the location input field.",        
        "Clear any existing data from the 'Leaving From' location input. And type 'Cochin' into 'Leaving From' input field",                
        "Click on the non-focusable but clickable 'Cochin' element from the list",
        "Tap on the 'Going To' field to activate the location input field.",        
        "Tap on the area labeled 'Going to' to activate the location input field.",
        "Clear any existing data from the 'Going to' location input. And type 'Bengaluru' into 'Going to' location input field",
        "Click on the non-focusable but clickable 'Bengaluru' element from the list",
        "Click on the search button",
        "Click on first flight from the list which matches like 'Air India'",
        "Click on the first 'select' button ",
        "Click on the 'Checkout' button"
]
PROMPT_RULES = """
Rules:
1. To interact with an input field using only XPath for element identification—do not use resource-id, accessibility ID, class name, or text attributes.
1. Use ONLY selectors from the provided list. Do NOT invent or use unlisted selectors or methods.
3. For waiting, always use:
   WebDriverWait(driver, 10).until(EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, "<value>")))
4. Return executable Python code inside a <PythonDetails> tag:
   - Each line must be a single line ending with a semicolon.
   - No markdown formatting.
   - No explanations or comments.
5. Return React Native Cucumber test cases inside a <FeatureDetails> tag.
6. Return React Native Javascript Page Object Model and its test code inside a <POMDetails> tag.
7. Do NOT import anything. Assume the following are already imported:
   - driver
   - time
   - By
   - AppiumBy
   - WebDriverWait
   - EC
8. Do NOT reinitialize the driver. Do NOT use "from appium import Appium".
9. Each Python code line must be a single executable statement ending with a semicolon.
10. All outputs must strictly follow the tag format:
   - <PythonDetails> for Python code
   - <FeatureDetails> for Cucumber test cases
   - <POMDetails> for React Native Javascript Page Object Model and test code
11. Do NOT include any reasoning, explanation, or commentary in the output. Only return the final result in the required format. Omit any <reasoning> or descriptive content.
12. If an element is having only Text, always use:
    driver.find_element(By.XPATH, "//*[@text='<Text>']")
13. If an element data is to be cleared Text, always use:
   driver.find_element(By.XPATH, "//*[@text='<Text>']").clear()
15. If an element is having only Content-Desc, always use:
   driver.find_element(AppiumBy.ACCESSIBILITY_ID, "<content-desc>")
16. Do not consider suggestion text like 'Search by city or airport'
17. For a non-focusable element always add inside the find_element:
     @focusable='false'  
18. Remove all semicolons (;) that are:
    At the end of a line.
    Immediately before or after a method call (e.g., .click(); .click()).
19. Fix misplaced dots (.):
    If a dot (.) appears after a semicolon, move it to the correct position before the method (e.g., ;.click() → .click()).
20. Preserve valid method chaining:
    Ensure that method calls like .click() remain intact and attached to the correct object. 
21. Ensure click() is prefixed with a dot (.) always    
22. For every single user interaction or step, Qwen must always generate all 3 output blocks:
        <PythonDetails>
        ...Python code here...
        </PythonDetails>
        <FeatureDetails>
        ...Cucumber scenario here...
        </FeatureDetails>
        <POMDetails>
        ...Page Object class and test method here...
        </POMDetails>
    This applies even to basic actions like input, clear, or tap.
24. When performing a SUBMIT action on a BUTTON, follow these strict guidelines:
    1. Use exact text match only. Do not infer, modify, abbreviate, or hallucinate the element text.
    2. If 'Your Element Text' has commas, then split by commas and use contains for each part.
        Example: For 'Submit, Now', use:
        driver.find_element(AppiumBy.XPATH,"//android.widget.Button[contains(@content-desc, 'Submit') and contains(@content-desc, 'Now')]").click()
    3. If 'Your Element Text' has no commas, use:
        driver.find_element(AppiumBy.XPATH,"//android.widget.Button[contains(@content-desc, 'Your Partial Text')]").click()
    4. This rule applies to all clickable elements, including:
        - Buttons
        - Links
        - Labels
    5. Do not use partial matches, synonyms, or alternate phrasing.
    6. Do not change the locator strategy unless explicitly instructed.
    7. Always preserve the integrity of the specified text.    
25. If an element is to be verified for existence, use below code snippet:
    - For exact text match and existence verification, use:
        element = driver.find_element(By.XPATH, "//*[@text='Your Element Text']");
        assert element is not None;
    - Replace "Your Element Text" with the actual text of the target element.
    - Do not infer, modify, or hallucinate any other name
    - Use only the exact text as specified.
    - This applies to all clickable elements including buttons, links, and labels.
"""

PROMPT_RULES_CUCUMBER="""
Rules:
1. Create the features as a single feature with multiple steps
2. Give the feature with in a tag <FeatureTag>
"""

PROMPT_RULES_POM = """
Rules:
1. Refactor the below poms and write page object model
2. Give the classes with in a single <ClassCode> tag
3. For every single user interaction or step, Qwen must always generate the output blocks:
        <ClassCode>
        ...JsClasses code here...
        </ClassCode> 
4. Only return the final result in the required format. Omit any <reasoning> or descriptive content.
5. 
"""

PROMPT_RULES_TEST_CODE = """
Rules:
    Given the following JavaScript/TypeScript code that implements Page Object Model (POM) classes and associated test functions, please extract **only the testing-related code**, including:
        - All test functions (e.g., functions with names starting with "test")
        - Any inline test execution statements (e.g., calls to page object methods used in tests)
        - Test suites and test cases (e.g., blocks using `describe`, `it`, or similar)
    Exclude all Page Object Model class definitions, helper methods, or any non-test related code.
    Return a single JavaScript file containing all extracted test code with in a tag <TestCode>, preserving async/await syntax, function structure, and test framework constructs.    
"""

PROMPT_RULES_CLASS_CREATE = """
Rules:
1. Ensure the extracted code is properly formatted and syntactically correct.
2. MUST Extract the attributes and behaviours separately
3. MUST Extract element identifiers as separate CONSTANTS within the class
4. Include necessary imports if they are part of the original code.
5. Do not include any other classes or code outside the specified class.
6. Ensure the output is a valid JavaScript class definition.
7. Give the classes with in a single tag <ClassFile>
8. For every single user interaction or step, Qwen must always generate the output blocks:
        <ClassFile>
        ...JsClasses code here...
        </ClassFile> 
9. Always keep constants inside the class definition
"""

# UI Automator Scroll Commands
SCROLL_COMMANDS = {
    "scroll_to_text_exact": lambda text: f'new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView(new UiSelector().text("{text}"))',
    "scroll_to_text_contains": lambda text: f'new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView(new UiSelector().textContains("{text}"))',
    "scroll_down_to_text": lambda text: f'new UiScrollable(new UiSelector().scrollable(true)).scrollForward().scrollIntoView(new UiSelector().textContains("{text}"))',
    "scroll_up_to_text": lambda text: f'new UiScrollable(new UiSelector().scrollable(true)).scrollBackward().scrollIntoView(new UiSelector().textContains("{text}"))',
    "scroll_until_found": lambda text: f'new UiScrollable(new UiSelector().scrollable(true)).setMaxSearchSwipes(10).scrollIntoView(new UiSelector().textContains("{text}"))',
    "scroll_down_until_found": lambda text: f'new UiScrollable(new UiSelector().scrollable(true)).setMaxSearchSwipes(20).flingToEnd(5).scrollIntoView(new UiSelector().textContains("{text}"))',
    "scroll_up_until_found": lambda text: f'new UiScrollable(new UiSelector().scrollable(true)).setMaxSearchSwipes(20).flingToBeginning(5).scrollIntoView(new UiSelector().textContains("{text}"))',
    "scroll_to_resource_id": lambda resource_id: f'new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView(new UiSelector().resourceId("{resource_id}"))',
    "scroll_to_class": lambda class_name: f'new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView(new UiSelector().className("{class_name}"))',
    "scroll_vertical_to_text": lambda text: f'new UiScrollable(new UiSelector().scrollable(true).instance(0)).setAsVerticalList().scrollIntoView(new UiSelector().textContains("{text}"))',
    "scroll_horizontal_to_text": lambda text: f'new UiScrollable(new UiSelector().scrollable(true).instance(0)).setAsHorizontalList().scrollIntoView(new UiSelector().textContains("{text}"))',
    "scroll_down_vertical": lambda text: f'new UiScrollable(new UiSelector().scrollable(true).instance(0)).setAsVerticalList().scrollForward().scrollIntoView(new UiSelector().textContains("{text}"))',
    "scroll_up_vertical": lambda text: f'new UiScrollable(new UiSelector().scrollable(true).instance(0)).setAsVerticalList().scrollBackward().scrollIntoView(new UiSelector().textContains("{text}"))',
    "scroll_aggressively_until_found": lambda text: f'new UiScrollable(new UiSelector().scrollable(true)).setMaxSearchSwipes(50).setSwipeDeadZonePercentage(0.25).scrollIntoView(new UiSelector().textContains("{text}"))'
}





TEST_STEPS_IN_NATURAL_LANGUAGE = """
**TEST CASE:** 
Verify flight search functionality on the mobile app.

**STEPS:**
Close the popup by clicking the 'X' button.
If prompted, close the popup by clicking the 'Allow' button.
Close the popup by clicking the 'X' button.
Click on the 'Flights' text or tab to begin flight search.
Click on the 'Leaving From Button' input field.
**TEST CASE END:**

**TEST CASE:** 
Analyse flight search functionality on the mobile app.

**STEPS:**
- Close the popup by clicking the 'X' button.
- If prompted, close the popup by clicking the 'Allow' button.
- Close the popup by clicking the 'X' button.
- Click on the 'Flights' text or tab to begin flight search.
- Click on the 'Leaving From Button' input field.
**TEST CASE END:**
"""
