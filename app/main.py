from fastapi import FastAPI, File, UploadFile, Form, Response, HTTPException
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

#* working directory: /workspace
from app.util import convert_any_to_wav, is_not_speaking, FeedbackStatus
from app.feedback.pronunciation_feedback import get_pronunciation_feedback
from app.feedback.intonation_feedback import get_intonation_feedback
from app.feedback.openai_api import get_asr_gpt

#* Debugging
from datetime import datetime, timedelta, timezone
import time
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    KST = timezone(timedelta(hours=9))
    start_time = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

    logger.info("="*50)
    logger.info("||      ML Server has started successfully      ||")
    logger.info(f"||      Started at: {start_time}         ||")
    logger.info("="*50)

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
    #* 다양한 format의 audio file을 wav format의 BytesIO로 변환
    audio_data = BytesIO(audio.file.read())
    wav_audio_data = convert_any_to_wav(audio_data, audio.filename)
    

    #! <NO_SPEECH>: 아무 말도 하지 않은 경우
    #* Demo 시연할 때, 반드시 아래 주석을 풀어야 함. 목소리도 크게 말해야 함.
    wav_audio_copy = BytesIO(wav_audio_data.getvalue()) #! librosa에서 audio_data를 변형시킴. 따라서 copy 해야 함.
    if is_not_speaking(wav_audio_copy):
        raise HTTPException(status_code=422, detail="목소리를 인식하지 못했습니다.")

    ########################################################################################################
    #! <Pronunciation & Intonation Feedback>
    
    with ThreadPoolExecutor() as executor:
        #! A. pronunciation(발음) 피드백 생성
        pronunciation_feedback = executor.submit(get_pronunciation_feedback, wav_audio_data, text)
        #! B. intonation(억양) 피드백 생성
        intonation_feedback = executor.submit(get_intonation_feedback, wav_audio_data)

    pronunciation_feedback = pronunciation_feedback.result()
    intonation_feedback = intonation_feedback.result()
    
    status = pronunciation_feedback['status']
    
    #! <WRONG_SENTENCE>: 사용자가 다른 문장을 발화한 경우
    if status == FeedbackStatus.WRONG_SENTENCE:
        raise HTTPException(status_code=423, detail="다른 문장을 발음했습니다.")

    ########################################################################################################
    #! <Multi-part/form-data>
    
    #! <PRONUNCIATION_SUCCESS & NOT_IMPLEMENTED>: 문장을 정확히 발음하거나 아직 피드백 알고리즘이 구현되지 않은 경우.
    if (status == FeedbackStatus.PRONUNCIATION_SUCCESS) or (status == FeedbackStatus.NOT_IMPLEMENTED):
        pronunciation_feedback_image_data = None
        intonation_feedback_image_data = None
    else:
        # 이미지 파일 읽기
        with open(pronunciation_feedback['feedback_images'][0], "rb") as f:
            pronunciation_feedback_image_data = f.read()

        with open(intonation_feedback['image_path'], "rb") as f:
            intonation_feedback_image_data = f.read()
    
    #* 고유한 boundary 설정
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"

    #* multipart 응답 바디를 바이너리로 초기화
    multipart_body = b""
    
    #* Multipart파트 추가를 위한 헬퍼 함수 정의    
    def add_text_part(name, content):
        nonlocal multipart_body
        part = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="{name}"\r\n'
            f'Content-Type: text/plain; charset=utf-8\r\n\r\n'
            f'{content}\r\n'
        ).encode('utf-8')
        multipart_body += part

    def add_file_part(name, filename, content, content_type):
        nonlocal multipart_body
        if content is None:  # 이미지 데이터가 없으면 "null"을 텍스트로 추가
            add_text_part(name, "null")
        else:
            part_header = (
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                f'Content-Type: {content_type}\r\n\r\n'
            ).encode('utf-8')
            multipart_body += part_header
            multipart_body += content  # 이미지 바이너리 데이터 추가
            multipart_body += b'\r\n'

    # 텍스트 파트 추가
    add_text_part('status', status)
    add_text_part('transcription', pronunciation_feedback['transcription'])
    add_text_part('pronunciation_feedback', pronunciation_feedback['pronunciation_feedback'])
    add_text_part('pronunciation_score', str(pronunciation_feedback['pronunciation_score']))
    add_text_part('intonation_feedback', intonation_feedback['intonation_feedback'])

    # 이미지 파트 추가
    add_file_part('pronunciation_feedback_image', 'pronunciation_feedback_image.png', pronunciation_feedback_image_data, 'image/png')
    add_file_part('intonation_feedback_image', 'intonation_feedback_image.png', intonation_feedback_image_data, 'image/png')

    # 마지막 boundary 추가
    multipart_body += f'--{boundary}--\r\n'.encode('utf-8')

    # 응답 헤더 설정
    headers = {
        'Content-Type': f'multipart/form-data; boundary={boundary}'
    }

    # 응답 반환
    return Response(content=multipart_body, media_type=f'multipart/form-data; boundary={boundary}', headers=headers)
    

"""
! 개발중인 API
! '/get-feedback' API의 인터페이스를 변경
! intonation feedback 부분 제거
! 반환 형태: Multipartfile -> Json (이미지와 피드백을 Spring 서버에 저장)
"""
@app.post("/get-pronunciation-feedback")
async def give_feedback(
    audio: UploadFile = File(...),
    text: str = Form(...)
):
    #* 다양한 format의 audio file을 wav format의 BytesIO로 변환
    audio_data = BytesIO(audio.file.read())
    wav_audio_data = convert_any_to_wav(audio_data, audio.filename)

    #! pronunciation(발음) 피드백 생성
    pronunciation_feedback = get_pronunciation_feedback(wav_audio_data, text)
    
    return pronunciation_feedback




@app.post("/get-feedback-test")
async def give_feedback_for_test(
    audio: UploadFile = File(...),
    text: str = Form(...) 
):
    #* 다양한 format의 audio file을 wav format의 BytesIO로 변환
    audio_data = BytesIO(audio.file.read())
    wav_audio_data = convert_any_to_wav(audio_data, audio.filename)
    
    #? 예외처리: 오디오 파일에 아무 말도 하지 않은 경우
    if is_not_speaking(wav_audio_data):
        raise HTTPException(status_code=422, detail="No speech detected in the audio file.")    

    #! A. pronunciation(발음) 피드백 생성
    pronunciation_feedback = get_pronunciation_feedback(wav_audio_data, text)

    return pronunciation_feedback
    

@app.post("/model-inference")
def pronunciation_asr_gpt(
    audio: UploadFile = File(...)
):
    #* 다양한 format의 audio file을 wav format의 BytesIO로 변환   
    audio_data = BytesIO(audio.file.read())
    wav_audio_data = convert_any_to_wav(audio_data, audio.filename) 
    
    transcription = get_asr_gpt(wav_audio_data)
    
    return {"Result": transcription}