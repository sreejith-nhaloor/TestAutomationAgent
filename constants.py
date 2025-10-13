PROMPT_RULES = """
Rules:
1. To interact with an input field using only XPath for element identification—do not use resource-id, accessibility ID, class name, or text attributes.
2. Use ONLY selectors from the provided list. Do NOT invent or use unlisted selectors or methods.
3. For waiting, always use:
   WebDriverWait(driver, 10).until(EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, "<value>")))
4. Return executable Python code inside a <PythonDetails> tag:
   - Each line must be a single line ending with a semicolon.
   - No markdown formatting.
   - No explanations or comments.
5. Do NOT import anything. Assume the following are already imported:
   - driver
   - time
   - By
   - AppiumBy
   - WebDriverWait
   - EC
6. Do NOT reinitialize the driver. Do NOT use "from appium import Appium".
7. Each Python code line must be a single executable statement ending with a semicolon.
8. Do NOT include any reasoning, explanation, or commentary in the output. Only return the final result in the required format. Omit any <reasoning> or descriptive content.
9. If an element is having only Text, always use:
    driver.find_element(By.XPATH, "//*[@text='<Text>']")
10. If an element data is to be cleared Text, always use:
   driver.find_element(By.XPATH, "//*[@text='<Text>']").clear()
11. If an element is having only Content-Desc, always use:
   driver.find_element(AppiumBy.ACCESSIBILITY_ID, "<content-desc>")
12. Do not consider suggestion text like 'Search by city or airport'
13. For a non-focusable element always add inside the find_element:
     @focusable='false'  
14. Remove all semicolons (;) that are:
    At the end of a line.
    Immediately before or after a method call (e.g., .click(); .click()).
15. Fix misplaced dots (.):
    If a dot (.) appears after a semicolon, move it to the correct position before the method (e.g., ;.click() → .click()).
16. Preserve valid method chaining:
    Ensure that method calls like .click() remain intact and attached to the correct object.
"""





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