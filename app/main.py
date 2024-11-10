from fastapi import FastAPI, File, UploadFile, Form, Response, HTTPException
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

#* working directory: /workspace
from app.util import convert_any_to_wav, is_not_speaking, FeedbackStatus
from app.feedback.pronunciation_feedback import get_pronunciation_feedback
from app.feedback.intonation_feedback import get_intonation_feedback
from app.feedback.openai_api import get_asr_gpt
from app.hangul2ipa.worker import apply_pronunciation_rules
from app.models import HangulRequest

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


@app.post("/get-pronunciation-feedback")
async def give_pronunciation_feedback(
    audio: UploadFile = File(...),
    text: str = Form(...) 
):
    """
    사용자의 발음(pronunciation)을 분석하여 틀린 부분을 교정하는 피드백을 반환하는 API
    
    Returns:
    -------
    JSON:
        * status : FeedbackStatus (int)
            Feedback 수행 상태를 나타내는 변수. app/util.py의 FeedbackStatus 클래스를 참고.
        
        * transcription : str
            오디오 파일을 들리는대로 전사한 한글 텍스트.
        
        * feedback_count : int
            생성된 피드백 개수. 'word_index', 'pronunciation_feedbacks', 'feedback_image_names', 'wrong_spellings' 리스트의 개수와 동일.
        
        * word_index : list
            몇번쨰 단어에서 틀렸는지 나타내는 인덱스를 포함하는 리스트.
        
        * pronunciation_feedbacks : list
            발음 교정 피드백 텍스트를 포함하는 리스트.
        
        * feedback_image_names : list
            발음 교정을 위한 입모양 사진의 이름을 포함하는 리스트. 사진들은 S3에 저장됨.
        
        * wrong_spellings : list
            틀린 철자들 리스트.
        
        * pronunciation_score : float
            사용자 발음을 평가한 점수.

    Example Response:
    -----------------
    {
        "status": 1,
        "transcription": "나는 행복하게 끝나는 용화가 좋다.",
        "feedback_count": 2,
        "word_index": [3, 5],
        "pronunciation_feedbacks": ["feedback1", "feedback2"],
        "feedback_image_names": ["image1.png", "image2.png"],
        "wrong_spellings": ["ㅕ", "ㅈ"],
        "pronunciation_score": 0.85
    }
    """
    
    #* <반환값>
    status = FeedbackStatus.PRONUNCIATION_SUCCESS
    transcription = ""
    feedback_count = 0
    word_index = []
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
    
    if status == FeedbackStatus.NOT_IMPLEMENTED:
        #! <NOT_IMPLEMENTED>: 아직 피드백 알고리즘이 구현되지 않은 경우.  
        raise HTTPException(status_code=501, detail="아직 구현되지 않은 기능입니다.")
    
    if status == FeedbackStatus.PRONUNCIATION_SUCCESS:
        #! <PRONUNCIATION_SUCCESS>: 문장을 정확히 발음한 경우
        transcription = "정확한 발음입니다."
        pronunciation_score = 100.0
        
    return {
        "status": status,
        "transcription": transcription,
        "feedback_count": feedback_count,
        "word_indexes": word_indexes,
        "pronunciation_feedbacks": pronunciation_feedbacks,
        "feedback_image_names": feedback_image_names,
        "wrong_spellings": wrong_spellings,
        "pronunciation_score": pronunciation_score
    }
    
@app.post("/get-pronounced-text")
def get_pronounced_text(
    request: HangulRequest
):
    standard_hangul = request.hangul
    
    # 입력된 텍스트가 유효한 한글인지 검사
    if False:
        raise HTTPException(
            status_code=422,
            detail="유효한 한글 문장이 아닙니다."
        )
        
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



from app.feedback.openai_api import get_pregenerated_mo_pronunciation_feedback

@app.post("/get-pregenerated-feedback")
def get_pregenerated_feedback(
    standard_mo: str = Form(...),
    user_mo: str = Form(...)
):
    feedback = get_pregenerated_mo_pronunciation_feedback(standard_mo, user_mo)
    return {"feedback": feedback}




# @app.post("/get-pronounced-text")
# def get_pronounced_text(
#     standard_hangul: str = Form(...)
# ):
#     pronounced_text = apply_pronunciation_rules(standard_hangul)
#     return {"pronounced_text": pronounced_text}






"""
<deprecated> 사용하지 않는 함수
"""
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
    