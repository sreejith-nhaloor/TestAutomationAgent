# TestAutomationAgent

Project for generating automation scripts using AI
## 📦 Setup
1. Start Appium: `appium`
2. Make sure you have installed requirements: `pip install -r requirements.txt`
3. Replace the APK_PATH in app.properties
4. Start Emulator: `./start_emulator.sh`
5. Login to AWS and copy the credentials to aws_config.py
6. Run: `python test_script_generator.py`


Sample Request for /run-test API

curl --location 'localhost:8000/run-test/' --header 'Content-Type: application/json' --data '{"test_case_id":1,"scenario_name":"Verify flight search functionality on the mobile app.","steps":[{"step_id":1,"description":"Close the popup by clicking the '\''X'\'' button."},{"step_id":2,"description":"If prompted, close the popup by clicking the '\''Allow'\'' button."},{"step_id":3,"description":"Close the popup by clicking the '\''X'\'' button."},{"step_id":4,"description":"Click on the '\''Flights'\'' text or tab to begin flight search."},{"step_id":5,"description":"Click on the '\''Leaving From Button'\'' input field."}]}'
