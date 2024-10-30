from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

#* working directory: /workspace
from app.hangul2ipa.worker import hangul2ipa
from app.models.model_loader import load_asr_model
from app.feedback import get_asr_inference
from app.util import convert_any_to_wav, encode_image_to_base64

#* Debugging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#! 모델 버전 지정.
MODEL_VERSION = "v2"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global IPA_ASR_MODEL #! 전역 IPA-ASR 모델
    
    logger.info("Service is starting...")
    IPA_ASR_MODEL = load_asr_model(MODEL_VERSION)
    logger.info("Model loaded successfully.")
    
    yield
    
    logger.info("Service is stopping...")

app = FastAPI(lifespan=lifespan)


@app.get("/")
def index():
    return {"message": "This is the index page of the ML Server."}


@app.post("/get-feedback")
async def give_feedback(
    audio: UploadFile = File(...),
    text: str = Form(...)
):        
    #! 먼저 audio 파일을 BytesIO 형태로 변환    
    audio_data = BytesIO(audio.file.read())
    
    #! audio 파일 format을 wav로 변환
    wav_audio_data = convert_any_to_wav(audio_data, audio.filename)
    
    #* Convert Audio and Text to IPA in parallel
    with ThreadPoolExecutor() as executor:
        ipa_sample = executor.submit(get_asr_inference, IPA_ASR_MODEL, wav_audio_data)
        ipa_correct = executor.submit(hangul2ipa, text)                                                         
    ipa_sample = ipa_sample.result()
    ipa_correct = ipa_correct.result()
    
    
    """
    TODO: 피드백 알고리즘 구현
    ! LLM 사용하여 ipa_sample 의 노이즈를 제거하고,
    ! LLM 에 ipa를 비교하여 피드백하는 방법을 알려주고
    ! ipa_sample 과 ipa_correct를 비교하여 피드백을 반환하게 한다.
    """
    # ipa_sample_clean, feedback_img, feedback = get_llm_feedback(ipa_sample, ipa_correct).split(',')
    
    """
    TODO: 정확도 계산
    ! 노이즈가 제거된 ipa_sample_clean 과 ipa_sample을 비교하여 정확도 계산.
    ! 정확도 계산에 CER을 사용하고, 100점 만점으로 변환.
    """
    
    """
    TODO: 반환값
    1. 문장에서 틀린 부분 표시  : [0, 3] (list) - 1번째 단어와 4번쨰 단어가 틀림
    2. 발화의 정확도           : 93.2 (float) - 100점 만점
    3. 문자 피드백             : 'ㅏ'를 발음할 때, 입모양을 더 크게 하세요. (string)
    4. 구강구조 이미지         : 이미지 1개
    5. 주파수 영역 분석 이미지  : 이미지 1개
    6. 주파수 영역 피드백       : (string)
    """
    
    incorrect_word_indices = [0, 3] 
    accuracy_score = 93.2
    speech_feedback = "'ㅏ'를 발음할 때, 입모양을 더 크게 하세요."
    oral_structure_image_path = "/workspace/app/images/oral_feedback.png"
    frequency_analysis_image_path = "/workspace/app/images/frequency_feedback.png"
    frequency_feedback = "질문하는 상황에서는 마지막 부분을 올리세요."
    
    #! 이미지를 Base64로 Encoding
    oral_structure_image_base64 = encode_image_to_base64(oral_structure_image_path)
    frequency_analysis_image_base64 = encode_image_to_base64(frequency_analysis_image_path)

    response_data = {
        "incorrect_word_indices": incorrect_word_indices,
        "accuracy": accuracy_score,
        "speech_feedback": speech_feedback,
        "frequency_feedback": frequency_feedback
    }

    return {
        "oral_structure_image": oral_structure_image_base64,
        "frequency_analysis_image": frequency_analysis_image_base64,
        "feedback_data": response_data
    }
    

@app.post("/model-inference")
def model_inference(
    audio: UploadFile = File(...),
    text: str = Form(...)
):
    #! 먼저 audio 파일을 BytesIO 형태로 변환    
    audio_data = BytesIO(audio.file.read())
    
    #! audio 파일 format을 wav로 변환
    wav_audio_data = convert_any_to_wav(audio_data, audio.filename)
    
    #* Convert Audio and Text to IPA in parallel
    with ThreadPoolExecutor() as executor:
        ipa_sample = executor.submit(get_asr_inference, IPA_ASR_MODEL, wav_audio_data)
        ipa_correct = executor.submit(hangul2ipa, text)
    ipa_sample = ipa_sample.result()
    ipa_correct = ipa_correct.result()
    
    return {"Result": ipa_sample, "Correct": ipa_correct}