from fastapi import FastAPI, File, UploadFile, Form
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

#* working directory: /workspace
# from app.models.model_loader import load_asr_model
# from app.feedback import get_asr_inference
from app.util import convert_any_to_wav, encode_image_to_base64
from app.feedback.pronunciation_feedback import get_pronunciation_feedback
from app.feedback.intonation_feedback import get_intonation_feedback
from app.feedback.openai_api import get_asr_gpt

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
    #* 다양한 format의 audio file을 wav format의 BytesIO로 변환
    audio_data = BytesIO(audio.file.read())
    wav_audio_data = convert_any_to_wav(audio_data, audio.filename)


    #* pronunciation(발음) & intonation(억양) 피드백 병렬로 생성
    with ThreadPoolExecutor() as executor:
        #! A. pronunciation(발음) 피드백 생성
        pronunciation_feedback = executor.submit(get_pronunciation_feedback, wav_audio_data, text)
        #! B. intonation(억양) 피드백 생성
        intonation_feedback = executor.submit(get_intonation_feedback, wav_audio_data)

    pronunciation_feedback = pronunciation_feedback.result()
    intonation_feedback = intonation_feedback.result()
    
    
    # #* 이미지를 Base64로 Encoding
    # pronunciation_feedback['pronunciation_feedback_image'] = "multipartfile image"# encode_image_to_base64(pronunciation_feedback['image_path'])
    # del pronunciation_feedback['image_path']
    
    # intonation_feedback['intonation_feedback_image'] = "multipartfile image"# encode_image_to_base64(intonation_feedback['image_path'])
    # del intonation_feedback['image_path']
    

    # return {
    #     "pronunciation_feedback": pronunciation_feedback,
    #     "intonation_feedback": intonation_feedback
    # }
    
        # 이미지 파일 읽기
    with open(pronunciation_feedback['image_path'], "rb") as f:
        pronunciation_feedback_image_data = f.read()

    with open(intonation_feedback['image_path'], "rb") as f:
        intonation_feedback_image_data = f.read()

    # 고유한 boundary 설정
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"

    # multipart 응답 바디를 바이너리로 초기화
    multipart_body = b""

    # 파트 추가를 위한 헬퍼 함수 정의
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
        part_header = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
            f'Content-Type: {content_type}\r\n\r\n'
        ).encode('utf-8')
        multipart_body += part_header
        multipart_body += content  # 이미지 바이너리 데이터 추가
        multipart_body += b'\r\n'

    # 텍스트 파트 추가
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
    
    
    
    
    
    
    
    
    
    
    
@app.post("/model-inference")
def pronunciation_asr_gpt(
    audio: UploadFile = File(...)
):
    #* 다양한 format의 audio file을 wav format의 BytesIO로 변환   
    audio_data = BytesIO(audio.file.read())
    wav_audio_data = convert_any_to_wav(audio_data, audio.filename) 
    
    transcription = get_asr_gpt(wav_audio_data)
    
    return {"Result": transcription}
    


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


from fastapi import FastAPI, Response
import mimetypes

@app.get("/feedback")
def get_feedback():
    # 텍스트 데이터 준비
    transcription = "나는 행복하게 끝나는 용화가 조따."
    pronunciation_feedback = "'영화가'를 발음할 때, 'ㅕ' 발음이 'ㅛ'로 들려요. ..."
    pronunciation_score = 95.12
    intonation_feedback = "질문하는 상황에서는 마지막 부분을 올리세요."

    # 이미지 파일 경로 설정
    pronunciation_feedback_image_path = "/workspace/app/images/oral_feedback.png"
    intonation_feedback_image_path = "/workspace/app/images/frequency_feedback.png"

    # 이미지 파일 읽기
    with open(pronunciation_feedback_image_path, "rb") as f:
        pronunciation_feedback_image_data = f.read()

    with open(intonation_feedback_image_path, "rb") as f:
        intonation_feedback_image_data = f.read()

    # 고유한 boundary 설정
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"

    # multipart 응답 바디를 바이너리로 초기화
    multipart_body = b""

    # 파트 추가를 위한 헬퍼 함수 정의
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
        part_header = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
            f'Content-Type: {content_type}\r\n\r\n'
        ).encode('utf-8')
        multipart_body += part_header
        multipart_body += content  # 이미지 바이너리 데이터 추가
        multipart_body += b'\r\n'

    # 텍스트 파트 추가
    add_text_part('transcription', transcription)
    add_text_part('pronunciation_feedback', pronunciation_feedback)
    add_text_part('pronunciation_score', str(pronunciation_score))
    add_text_part('intonation_feedback', intonation_feedback)

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
