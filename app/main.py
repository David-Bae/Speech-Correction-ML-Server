from fastapi import FastAPI, File, UploadFile, Form, Response, HTTPException
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

#* working directory: /workspace
from app.util import convert_any_to_wav, is_not_speaking, FeedbackStatus, convert_Image_to_BytesIO
from app.feedback.pronunciation_feedback import get_pronunciation_feedback
from app.feedback.intonation_feedback import get_intonation_feedback
from app.feedback.openai_api import get_asr_gpt
from app.hangul2ipa.worker import apply_pronunciation_rules
from app.models import *

#* Debugging
from datetime import datetime, timedelta, timezone
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


@app.post("/get-pronunciation-feedback")
async def give_pronunciation_feedback(
    audio: UploadFile = File(...),
    text: str = Form(...) 
):
    """
    사용자의 발음(pronunciation)을 분석하여 틀린 부분을 교정하는 피드백을 반환하는 API
    """
    
    #* <반환값>
    status = FeedbackStatus.PRONUNCIATION_SUCCESS
    transcription = ""
    feedback_count = 0
    word_indexes = []
    pronunciation_feedbacks = []    #? ML서버에 저장
    feedback_image_names = []       #? S3에 저장
    wrong_spellings = []
    pronunciation_score = 0.0
    
    
    #* 다양한 format의 audio file을 wav format의 BytesIO로 변환
    audio_data = BytesIO(audio.file.read())
    wav_audio_data = convert_any_to_wav(audio_data, audio.filename)
    

    #! <NO_SPEECH>: 아무 말도 하지 않은 경우
    wav_audio_copy = BytesIO(wav_audio_data.getvalue()) # librosa에서 audio_data를 변형시킴. 따라서 copy 해야 함.
    if is_not_speaking(wav_audio_copy):
        raise HTTPException(status_code=422, detail="목소리를 인식하지 못했습니다.")

    
    #! <Pronunciation Feedback>
    pronunciation_feedback = get_pronunciation_feedback(wav_audio_data, text)
    
    status = pronunciation_feedback['status']
    transcription = pronunciation_feedback['transcription']
    feedback_count = pronunciation_feedback['feedback_count']
    word_indexes = pronunciation_feedback['word_indexes']
    pronunciation_feedbacks = pronunciation_feedback['pronunciation_feedbacks']
    feedback_image_names = pronunciation_feedback['feedback_image_names']
    wrong_spellings = pronunciation_feedback['wrong_spellings']
    pronunciation_score = pronunciation_feedback['pronunciation_score']
    
    
    if status == FeedbackStatus.WRONG_SENTENCE:
        #! <WRONG_SENTENCE>: 사용자가 다른 문장을 발화한 경우
        raise HTTPException(status_code=423, detail="다른 문장을 발음했습니다.")
    
    elif status == FeedbackStatus.NOT_IMPLEMENTED:
        #! <NOT_IMPLEMENTED>: 아직 피드백 알고리즘이 구현되지 않은 경우.  
        raise HTTPException(status_code=501, detail="아직 구현되지 않은 기능입니다.")
    
    elif status == FeedbackStatus.PRONUNCIATION_SUCCESS:
        #! <PRONUNCIATION_SUCCESS>: 문장을 정확히 발음한 경우
        transcription = "정확한 발음입니다."
        pronunciation_score = 100.0
    else:
        #! 사용자가 발음한 문장에 발음 법칙 적용.
        transcription = apply_pronunciation_rules(transcription)    
    
        
    return PronunciationFeedbackResponse(
        status=status,
        transcription=transcription,
        feedback_count=feedback_count,
        word_indexes=word_indexes,
        pronunciation_feedbacks=pronunciation_feedbacks,
        feedback_image_names=feedback_image_names,
        wrong_spellings=wrong_spellings,
        pronunciation_score=pronunciation_score
    )


  
@app.post("/get-pronounced-text")
def get_pronounced_text(
    request: HangulRequest
):
    standard_hangul = request.hangul
    pronounced_text = apply_pronunciation_rules(standard_hangul)
    return {"pronounced_text": pronounced_text}



@app.post("/model-inference")
def pronunciation_asr_gpt(
    audio: UploadFile = File(...)
):
    #* 다양한 format의 audio file을 wav format의 BytesIO로 변환   
    audio_data = BytesIO(audio.file.read())
    wav_audio_data = convert_any_to_wav(audio_data, audio.filename) 
    
    transcription = get_asr_gpt(wav_audio_data)
    
    return {"Result": transcription}


#! <Intonation Feedback: 개발중>
@app.post("/get-intonation-feedback")
def give_intonation_feedback(
    audio: UploadFile = File(...),
    text: str = Form(...)
):
    #* <반환값>
    status = FeedbackStatus.PRONUNCIATION_SUCCESS    
    feedback_count = 0
    word_indexes = []
    intonation_feedbacks = []
    intonation_score = 0.0
    feedback_image = None
    
    #* 다양한 format의 audio file을 wav format의 BytesIO로 변환
    audio_data = BytesIO(audio.file.read())
    wav_audio_data = convert_any_to_wav(audio_data, audio.filename)
    

    #! <NO_SPEECH>: 아무 말도 하지 않은 경우
    wav_audio_copy = BytesIO(wav_audio_data.getvalue()) # librosa에서 audio_data를 변형시킴. 따라서 copy 해야 함.
    if is_not_speaking(wav_audio_copy):
        raise HTTPException(status_code=422, detail="목소리를 인식하지 못했습니다.")

    #! <Intonation Feedback>
    intonation_feedback = get_intonation_feedback(wav_audio_data)
    
    status = intonation_feedback['status']
    feedback_count = intonation_feedback['feedback_count']
    word_indexes = intonation_feedback['word_indexes']
    intonation_feedbacks = intonation_feedback['intonation_feedbacks']
    intonation_score = intonation_feedback['intonation_score']
    feedback_image = intonation_feedback['feedback_image'] #! feedback_image의 자료형은 Image

    if feedback_image is None:
        logger.error("2. give_intonation_feedback: Feedback image is None")
    else:
        logger.info("2. give_intonation_feedback: Feedback image is not None")
    
    feedback_image_binary = convert_Image_to_BytesIO(feedback_image) #! 멀티파트로 전송하기 위해 binary로 변환
    
    if feedback_image_binary is None:
        logger.error("5. give_intonation_feedback: Feedback image binary is None")
    else:
        logger.info("5. give_intonation_feedback: Feedback image binary is not None")

    ########################################################################################################
    #! <Multi-part/form-data>    
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
    add_text_part('feedback_count', str(feedback_count))
    add_text_part('word_indexes', ','.join(map(str, word_indexes)))
    add_text_part('intonation_feedbacks', ','.join(intonation_feedbacks))
    add_text_part('intonation_score', str(intonation_score))
    
    #! 이미지 파트 추가 feedback_image의 자료형은 BytesIO
    feedback_image_bin_value = feedback_image_binary.getvalue()

    if feedback_image_bin_value is None:
        logger.error("6. give_intonation_feedback: Feedback image binary value is None")
    else:
        logger.info("6. give_intonation_feedback: Feedback image binary value is not None")

    add_file_part('feedback_image', 'feedback_image.png', feedback_image_bin_value, 'image/png')

    # 마지막 boundary 추가
    multipart_body += f'--{boundary}--\r\n'.encode('utf-8')

    # 응답 헤더 설정
    headers = {
        'Content-Type': f'multipart/form-data; boundary={boundary}'
    }

    # 응답 반환
    return Response(content=multipart_body, media_type=f'multipart/form-data; boundary={boundary}', headers=headers)
    

# #! <MFA: 개발중>
# from app.feedback.intonation.intonation_graph_generator import plot_intonation_graph
# from app.feedback.intonation.pitch import get_time_and_pitch

# #! 억양 교정 기능에서 문장 Align된 높낮이 그래프 이미지 생성.
# #! MFA Alignment를 사전에 수행하고, intonation/mfa_results에 TextGrid 파일 저장한 상태에서 호출 가능.
# @app.post("/intonation-feedback-test")
# def give_intonation_feedback_test(
#     audio: UploadFile = File(...),
#     sentence_number: str = Form(...)
# ):
#     #* 다양한 format의 audio file을 wav format의 BytesIO로 변환
#     audio_data = BytesIO(audio.file.read())
#     wav_audio_data = convert_any_to_wav(audio_data, audio.filename)
    
#     #! Pitch 데이터 추출
#     time_resampled, pitch_resampled = get_time_and_pitch(wav_audio_data)
    
#     #! 그래프 이미지 생성
#     plot_intonation_graph(time_resampled, pitch_resampled)
      
#     return {"message": "success"}






from mfa.mfa import align_mfa

"""
MFA 실행 함수
'/workspace/mfa/source'에 같은 이름의 오디오 파일과 텍스트 파일을 넣는다.
execute-mfa API를 호출한다.
!주의: 한 번 mfa를 실행하고, 다시 실행하면 이미 mfa를 수행했다고 인식하여 또 실행하지 않는다.
! 따라서 매번 폴더의 이름을 바꿔줘야 한다.
"""
@app.get("/execute-mfa")
def execute_mfa():
    FOLDER_NAME = "/workspace/mfa/source"
    align_mfa(FOLDER_NAME)



# """
# <deprecated> 사용하지 않는 함수
# """
# @app.post("/get-feedback")
# async def give_feedback(
#     audio: UploadFile = File(...),
#     text: str = Form(...) 
# ):
#     #* 다양한 format의 audio file을 wav format의 BytesIO로 변환
#     audio_data = BytesIO(audio.file.read())
#     wav_audio_data = convert_any_to_wav(audio_data, audio.filename)
    

#     #! <NO_SPEECH>: 아무 말도 하지 않은 경우
#     #* Demo 시연할 때, 반드시 아래 주석을 풀어야 함. 목소리도 크게 말해야 함.
#     wav_audio_copy = BytesIO(wav_audio_data.getvalue()) #! librosa에서 audio_data를 변형시킴. 따라서 copy 해야 함.
#     if is_not_speaking(wav_audio_copy):
#         raise HTTPException(status_code=422, detail="목소리를 인식하지 못했습니다.")

#     ########################################################################################################
#     #! <Pronunciation & Intonation Feedback>
    
#     with ThreadPoolExecutor() as executor:
#         #! A. pronunciation(발음) 피드백 생성
#         pronunciation_feedback = executor.submit(get_pronunciation_feedback, wav_audio_data, text)
#         #! B. intonation(억양) 피드백 생성
#         intonation_feedback = executor.submit(get_intonation_feedback, wav_audio_data)

#     pronunciation_feedback = pronunciation_feedback.result()
#     intonation_feedback = intonation_feedback.result()
    
#     status = pronunciation_feedback['status']
    
#     #! <WRONG_SENTENCE>: 사용자가 다른 문장을 발화한 경우
#     if status == FeedbackStatus.WRONG_SENTENCE:
#         raise HTTPException(status_code=423, detail="다른 문장을 발음했습니다.")

#     ########################################################################################################
#     #! <Multi-part/form-data>
    
#     #! <PRONUNCIATION_SUCCESS & NOT_IMPLEMENTED>: 문장을 정확히 발음하거나 아직 피드백 알고리즘이 구현되지 않은 경우.
#     if (status == FeedbackStatus.PRONUNCIATION_SUCCESS) or (status == FeedbackStatus.NOT_IMPLEMENTED):
#         pronunciation_feedback_image_data = None
#         intonation_feedback_image_data = None
#     else:
#         # 이미지 파일 읽기
#         with open(pronunciation_feedback['feedback_images'][0], "rb") as f:
#             pronunciation_feedback_image_data = f.read()

#         with open(intonation_feedback['image_path'], "rb") as f:
#             intonation_feedback_image_data = f.read()
    
#     #* 고유한 boundary 설정
#     boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"

#     #* multipart 응답 바디를 바이너리로 초기화
#     multipart_body = b""
    
#     #* Multipart파트 추가를 위한 헬퍼 함수 정의    
#     def add_text_part(name, content):
#         nonlocal multipart_body
#         part = (
#             f'--{boundary}\r\n'
#             f'Content-Disposition: form-data; name="{name}"\r\n'
#             f'Content-Type: text/plain; charset=utf-8\r\n\r\n'
#             f'{content}\r\n'
#         ).encode('utf-8')
#         multipart_body += part

#     def add_file_part(name, filename, content, content_type):
#         nonlocal multipart_body
#         if content is None:  # 이미지 데이터가 없으면 "null"을 텍스트로 추가
#             add_text_part(name, "null")
#         else:
#             part_header = (
#                 f'--{boundary}\r\n'
#                 f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
#                 f'Content-Type: {content_type}\r\n\r\n'
#             ).encode('utf-8')
#             multipart_body += part_header
#             multipart_body += content  # 이미지 바이너리 데이터 추가
#             multipart_body += b'\r\n'

#     # 텍스트 파트 추가
#     add_text_part('status', status)
#     add_text_part('transcription', pronunciation_feedback['transcription'])
#     add_text_part('pronunciation_feedback', pronunciation_feedback['pronunciation_feedback'])
#     add_text_part('pronunciation_score', str(pronunciation_feedback['pronunciation_score']))
#     add_text_part('intonation_feedback', intonation_feedback['intonation_feedback'])

#     # 이미지 파트 추가
#     add_file_part('pronunciation_feedback_image', 'pronunciation_feedback_image.png', pronunciation_feedback_image_data, 'image/png')
#     add_file_part('intonation_feedback_image', 'intonation_feedback_image.png', intonation_feedback_image_data, 'image/png')

#     # 마지막 boundary 추가
#     multipart_body += f'--{boundary}--\r\n'.encode('utf-8')

#     # 응답 헤더 설정
#     headers = {
#         'Content-Type': f'multipart/form-data; boundary={boundary}'
#     }

#     # 응답 반환
#     return Response(content=multipart_body, media_type=f'multipart/form-data; boundary={boundary}', headers=headers)
    