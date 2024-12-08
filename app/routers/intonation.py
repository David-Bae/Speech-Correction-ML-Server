from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from io import BytesIO

#* working directory: /workspace
from app.utils.audio_image import convert_any_to_wav, is_not_speaking, convert_3gpp_to_wav_bytesio
from app.models import FeedbackStatus
from app.feedback.intonation_feedback import get_intonation_feedback
from app.utils.response import get_multipart_form_data

#* Debugging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter()


#! <Intonation Feedback>
@router.post("/get-intonation-feedback")
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
    wav_audio_data = convert_any_to_wav(audio)
    
    #! <NO_SPEECH>: 아무 말도 하지 않은 경우
    wav_audio_copy = BytesIO(wav_audio_data.getvalue()) # librosa에서 audio_data를 변형시킴. 따라서 copy 해야 함.
    if is_not_speaking(wav_audio_copy):
        raise HTTPException(status_code=422, detail="목소리를 인식하지 못했습니다.")

    #* <Intonation Feedback>
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