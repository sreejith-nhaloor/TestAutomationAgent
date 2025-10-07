from pydantic import BaseModel
from typing import List
from typing import Any

class Step(BaseModel):
    step_id: int
    description: str

    

class TestCase(BaseModel):
    test_case_id: int
    scenario_name: str
    steps: List[Step]



class TestResult(BaseModel):
    status: str = "Not Started"
    test_case_details: TestCase
    path_page_object_model: str = None
    path_feature_file: str = None
    path_appium_python_script: str = None
    errors: str 