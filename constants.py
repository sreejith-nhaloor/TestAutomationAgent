TEST_STEPS = [
	"Close the sign in page.",
	"In the allow notification pop-up, click on Don't Allow.",
	"Close the location access pop-up.",
	"Click on Flights.",
	"Search for flights from COK to BLR on dates Oct 8 to Oct 9."
]
PROMPT_RULES = """
Rules:
1. Use ONLY selectors from the given list.
2. Return ONLY executable Python code, no extra explanations, no markdown formatting.
3. If an element has a Content-Desc, always use: driver.find_element(AppiumBy.ACCESSIBILITY_ID, "<content-desc>")
4. For waiting, always use: WebDriverWait(driver, 10).until(EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, "<value>")))
5. Assume driver, time, By, AppiumBy, WebDriverWait, and EC are already imported.
6. Never import anything in your code. Do not re-initialize driver. Do not use from appium import Appium.
7. If an element is having only Text, always use: driver.find_element(By.XPATH, "//*[@text='<Text>']")
"""
