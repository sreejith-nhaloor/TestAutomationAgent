from fastapi import FastAPI
from constants import TEST_STEPS_IN_NATURAL_LANGUAGE
from test_script_generator import run_test
from models import TestCase
from utils import parse_natural_language_steps_to_testcase

app = FastAPI()

PORT = 8000


@app.post("/run-test/")
def run_test_api(test_case:TestCase):
    return run_test(test_case)


@app.post("/text-to-json/")
def run_nlp_to_json_api():
    test_case_json = parse_natural_language_steps_to_testcase(TEST_STEPS_IN_NATURAL_LANGUAGE)
    return test_case_json[0]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=PORT, reload=True)