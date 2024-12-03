import requests
import pytest
import os
import json

BASE_URL = "http://localhost:8000"

#? 발음 교정 Test Case
TEST_DATA_PRONUNCIATION = [
    {"case": "0", "expected_status": 200},
    {"case": "1", "expected_status": 200},
    {"case": "2", "expected_status": 200},
    {"case": "wrong_sentence", "expected_status": 423},
    {"case": "silence", "expected_status": 422},
]

#? 발음 교정 Test Data
PRONUNCIATION_AUDIO_FOLDER = "/workspace/tests/data/pronunciation"
PRONUNCIATION_SENTENCE_FILE = "/workspace/tests/data/pronunciation.json"
sentence_data = {}
with open(PRONUNCIATION_SENTENCE_FILE, "r") as file:
    sentence_data = json.load(file)

#! 발음 교정 API 테스트
@pytest.mark.parametrize("test_case", TEST_DATA_PRONUNCIATION)
def test_pronunciation_feedback_api(test_case):
    url = f"{BASE_URL}/get-pronunciation-feedback"

    case = test_case["case"]
    expected_status = test_case["expected_status"]
    
    audio_file_path = os.path.join(PRONUNCIATION_AUDIO_FOLDER, f"{case}.3gp")
    text = sentence_data[case]["text"]
    
    with open(audio_file_path, "rb") as audio_file:
        files = {"audio": (audio_file_path, audio_file, "audio/mp3")}
        data = {"text": text}

        #* POST 요청 실행
        response = requests.post(url, files=files, data=data)
        
    #* 상태 코드 검증
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"
    
    
#? 억양 교정 Test Case
TEST_DATA_INTONATION = [
    {"case": "0_0", "expected_status": 200},
    {"case": "1_0", "expected_status": 200},
    {"case": "2_0", "expected_status": 200},
    {"case": "3_0", "expected_status": 200},
    {"case": "silence", "expected_status": 422},
]

#? 억양 교정 Test Data
INTONATION_AUDIO_FOLDER = "/workspace/tests/data/intonation"

#! 억양 교정 API 테스트
@pytest.mark.parametrize("test_case", TEST_DATA_INTONATION)
def test_intonation_feedback_api(test_case):
    url = f"{BASE_URL}/get-intonation-feedback"
    
    case = test_case["case"]
    expected_status = test_case["expected_status"]
    
    audio_file_path = os.path.join(INTONATION_AUDIO_FOLDER, f"{case}.3gp")
        
    with open(audio_file_path, "rb") as audio_file:
        files = {"audio": (audio_file_path, audio_file, "audio/wav")}
        
        if case == "silence":
            data = {"sentence_code": "0_0"}
        else:
            data = {"sentence_code": case}
        
        #* POST 요청 실행
        response = requests.post(url, files=files, data=data)
        
    #* 상태 코드 검증
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"
