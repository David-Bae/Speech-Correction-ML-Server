from fastapi import FastAPI, File, UploadFile, Form, Response, HTTPException
from contextlib import asynccontextmanager
from io import BytesIO

#* working directory: /workspace
from app.util import convert_any_to_wav, is_not_speaking, FeedbackStatus, convert_Image_to_BytesIO
from app.feedback.pronunciation_feedback import get_pronunciation_feedback
from app.feedback.intonation_feedback import get_intonation_feedback
from app.feedback.openai_api import get_asr_gpt
from app.hangul2ipa.worker import apply_pronunciation_rules
from app.models import *
from app.util import get_multipart_form_data

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
    sentence_code: str = Form(...)
):
    #* <반환값>
    status = FeedbackStatus.PRONUNCIATION_SUCCESS
    intonation_feedback = ""
    intonation_score = 0.0
    feedback_image = None
    
    #* 다양한 format의 audio file을 wav format의 BytesIO로 변환
    audio_data = BytesIO(audio.file.read())
    wav_audio_data = convert_any_to_wav(audio_data, audio.filename)
    
    #! <NO_SPEECH>: 아무 말도 하지 않은 경우
    wav_audio_copy = BytesIO(wav_audio_data.getvalue()) # librosa에서 audio_data를 변형시킴. 따라서 copy 해야 함.
    if is_not_speaking(wav_audio_copy):
        raise HTTPException(status_code=422, detail="목소리를 인식하지 못했습니다.")

    #TODO <Intonation Feedback>: 개발중!!!
    intonation_feedback = get_intonation_feedback(wav_audio_data, sentence_code)
    
    status = intonation_feedback['status']
    intonation_score = intonation_feedback['intonation_score']
    feedback_text = intonation_feedback['feedback_text']
    feedback_image = intonation_feedback['feedback_image']

    parts = {
        "status": status,
        "intonation_score": intonation_score,
        "feedback_text": feedback_text,
        "feedback_image": ("feedback_image.jpg", feedback_image, "image/jpeg")
    }

    multipart_response = get_multipart_form_data(**parts)

    return multipart_response




#! <문장 유형 분류 API: Test용>
# from app.feedback.openai_api import classify_sentence_type

# sentence_type_dict = {
#     0: "의문문",
#     1: "평서문",
#     2: "감탄문",
#     3: "청유문"
# }

# @app.post("/get-sentence-type")
# async def get_sentence_type(
#     audio: UploadFile = File(...)
# ):
#     """
#     사용자의 음성을 분석하여 문장 유형을 분류하는 API
#     """    
#     #* 다양한 format의 audio file을 wav format의 BytesIO로 변환
#     audio_data = BytesIO(audio.file.read())
#     wav_audio_data = convert_any_to_wav(audio_data, audio.filename)    
    
#     sentence_type = classify_sentence_type(wav_audio_data)
    
#     if sentence_type in sentence_type_dict:
#         return {"sentence_type": sentence_type_dict[sentence_type]}
#     else:
#         return {"sentence_type": "알 수 없음"}
    


# #! <개발중: 음성 받아서 그래프 이미지 생성까지>
# from app.feedback.intonation.intonation_graph_generator import plot_intonation_graph
# from app.feedback.intonation.pitch import get_time_and_pitch

# #! 억양 교정 기능에서 문장 Align된 높낮이 그래프 이미지 생성.
# #! MFA Alignment를 사전에 수행하고, intonation/mfa_results에 TextGrid 파일 저장한 상태에서 호출 가능.
# @app.post("/generate-intonation-image")
# def generate_intonation_image(
#     audio: UploadFile = File(...)
# ):
#     #* 다양한 format의 audio file을 wav format의 BytesIO로 변환
#     audio_data = BytesIO(audio.file.read())
#     wav_audio_data = convert_any_to_wav(audio_data, audio.filename)

#     #! Pitch 데이터 추출
#     time_resampled, pitch_resampled = get_time_and_pitch(wav_audio_data)

#     #! 그래프 이미지 생성
#     image_binary = plot_intonation_graph(time_resampled, pitch_resampled)

#     parts = {
#         "feedback_image": ("feedback_image.jpg", image_binary, "image/jpeg"),
#     }

#     multipart_response = get_multipart_form_data(**parts)

#     return multipart_response