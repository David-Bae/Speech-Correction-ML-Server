from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from io import BytesIO

#* working directory: /workspace
from app.utils.audio_image import convert_any_to_wav, is_not_speaking
from app.feedback.pronunciation_feedback import get_pronunciation_feedback
from app.hangul2ipa.worker import apply_pronunciation_rules
from app.feedback.openai_api import get_asr_gpt
from app.models import *


#* Debugging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter()

@router.post("/get-pronunciation-feedback")
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


@router.post("/get-pronounced-text")
def get_pronounced_text(
    request: HangulRequest
):
    standard_hangul = request.hangul
    pronounced_text = apply_pronunciation_rules(standard_hangul)
    return {"pronounced_text": pronounced_text}


@router.post("/model-inference")
def pronunciation_asr_gpt(
    audio: UploadFile = File(...)
):
    #* 다양한 format의 audio file을 wav format의 BytesIO로 변환   
    audio_data = BytesIO(audio.file.read())
    wav_audio_data = convert_any_to_wav(audio_data, audio.filename) 
    
    transcription = get_asr_gpt(wav_audio_data)
    
    return {"Result": transcription}