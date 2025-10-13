from pydantic import BaseModel
from typing import List    

class TestCase(BaseModel):
    scenario_name: str
    steps: List[str]



class TestResult(BaseModel):
    status: str = "Not Started"
    path_page_object_model: str = None
    path_feature_file: str = None
    path_appium_python_script: str = None
    pull_request_url: str = None
    errors: str 