from fastapi import FastAPI, File, UploadFile, Form
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

#* working directory: /workspace
from app.hangul2ipa.worker import hangul2ipa
# from app.models.model_loader import load_asr_model
# from app.feedback import get_asr_inference
from app.util import convert_any_to_wav, encode_image_to_base64
from app.feedback.speech_feedback import get_speech_feedback

#* Debugging
from datetime import datetime, timedelta, timezone
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# #! 모델 버전 지정.
# MODEL_VERSION = "v2" 

@asynccontextmanager
async def lifespan(app: FastAPI):
    # global IPA_ASR_MODEL #! 전역 IPA-ASR 모델
    KST = timezone(timedelta(hours=9))
    start_time = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

    logger.info("="*50)
    logger.info("||      ML Server has started successfully      ||")
    logger.info(f"||      Started at: {start_time}         ||")
    logger.info("="*50)

    # IPA_ASR_MODEL = load_asr_model(MODEL_VERSION)
    # logger.info("Model loaded successfully.")
    
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
    #* audio 파일 format을 wav로 변환   
    audio_data = BytesIO(audio.file.read())
    wav_audio_data = convert_any_to_wav(audio_data, audio.filename)    


    #* Convert Audio and Text to IPA in parallel
    with ThreadPoolExecutor() as executor:
        # ipa_sample = executor.submit(get_asr_inference, IPA_ASR_MODEL, wav_audio_data) #? Huggingface Model
        speech_feedback = executor.submit(get_speech_feedback, wav_audio_data, text)
        frequency_feedback = None   #! Frequency Feedback 함수 추가 예정.
                                                 
    speech_feedback = speech_feedback.result()
    frequency_feedback = frequency_feedback #.result()


    """
    TODO: 반환값
    1. 문장에서 틀린 부분 표시  : [0, 3] (list) - 1번째 단어와 4번쨰 단어가 틀림
    2. 발화의 정확도           : 93.2 (float) - 100점 만점
    3. 문자 피드백             : 'ㅏ'를 발음할 때, 입모양을 더 크게 하세요. (string)
    4. 구강구조 이미지         : 이미지 1개
    5. 주파수 영역 분석 이미지  : 이미지 1개
    6. 주파수 영역 피드백       : (string)
    """
    
    
    frequency_analysis_image_path = "/workspace/app/images/frequency_feedback.png"
    frequency_feedback = "질문하는 상황에서는 마지막 부분을 올리세요."
    
    #! 이미지를 Base64로 Encoding
    speech_feedback['speech_feedback_image'] = encode_image_to_base64(speech_feedback['image_path'])
    del speech_feedback['image_path']
    
    # frequency_analysis_image_base64 = encode_image_to_base64(frequency_analysis_image_path)

    return {
        "speech_feedback": speech_feedback,
        "frequency_feedback": None
    }
    

# @app.post("/model-inference")
# def model_inference(
#     audio: UploadFile = File(...),
#     text: str = Form(...)
# ):
#     #! 먼저 audio 파일을 BytesIO 형태로 변환    
#     audio_data = BytesIO(audio.file.read())
    
#     #! audio 파일 format을 wav로 변환
#     wav_audio_data = convert_any_to_wav(audio_data, audio.filename)
    
#     #* Convert Audio and Text to IPA in parallel
#     with ThreadPoolExecutor() as executor:
#         ipa_sample = executor.submit(get_asr_inference, IPA_ASR_MODEL, wav_audio_data)
#         ipa_correct = executor.submit(hangul2ipa, text)
#     ipa_sample = ipa_sample.result()
#     ipa_correct = ipa_correct.result()
    
#     return {"Result": ipa_sample, "Correct": ipa_correct}