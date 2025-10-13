# TestAutomationAgent
Project for generating automation scripts using AI

## Do not commit any secrets to this repo

## 📦 Setup
1. Start Appium: `appium`
2. Make sure you have installed requirements: `pip install -r requirements.txt`
3. Replace the APK_PATH in app.properties
4. Start Emulator: `./start_emulator.sh`
5. Add aws credentials and github token to config.yaml
7. Run: `python test_script_generator.py`


Sample Request for /run-test API

```sh
curl --location 'localhost:8000/run-test/' --header 'Content-Type: application/json' --data '{
    "test_case_id": 1,
    "scenario_name": "Verify flight search functionality on the mobile app.",
    "steps": [
        "Close the popup by clicking the '\''X'\'' button.",
        "If prompted, close the popup by clicking the '\''Allow'\'' button.",
        "Close the popup by clicking the '\''X'\'' button.",
        "Click on the '\''Flights'\'' text or tab to begin flight search.",
        "Click on the '\''One-Way'\'' tab ",
        "Click on the '\''Leaving From Button'\'' input field.",
        "Tap on the '\''Leaving From'\'' field to activate the location input field.",
        "Clear any existing data from the '\''Leaving From'\'' location input. And type '\''Cochin'\'' into '\''Leaving From'\'' input field",
        "Click on the non-focusable but clickable '\''Cochin'\'' element from the list",
        "Tap on the '\''Going To'\'' field to activate the location input field.",
        "Tap on the area labeled '\''Going to'\'' to activate the location input field.",
        "Clear any existing data from the '\''Going to'\'' location input. And type '\''Bengaluru'\'' into '\''Going to'\'' location input field",
        "Click on the non-focusable but clickable '\''Bengaluru'\'' element from the list",
        "Click on the search button",
        "Click on first flight from the list which matches like '\''Air India'\''",
        "Click on the first '\''select'\'' button ",
        "Click on the '\''Checkout'\'' button"
    ]
}'
```
