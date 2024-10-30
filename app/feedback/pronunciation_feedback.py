# import librosa
# import numpy as np
# from io import BytesIO

from app.feedback import openai_api
from app.hangul2ipa.worker import hangul2ipa



import logging
logger = logging.getLogger(__name__)


def get_pronunciation_feedback(audio_data, hangul):
    transcription = openai_api.get_asr_gpt(audio_data)
    
    ipa_standard = hangul2ipa(hangul)
    ipa_user = hangul2ipa(transcription)
    
    #! ipa_standard와 ipa_user 비교하여 feedback 하는 함수 호출
    pronunciation_feedback = openai_api.get_pronunciation_feedback_gpt()
    oral_structure_image_path = "/workspace/app/images/oral_feedback.png"
    
    #! 발화 점수 계산
    pronunciation_score = calculate_pronunciation_score(ipa_standard, ipa_user)
    
    feedback = {
        "transcription": transcription,
        "pronunciation_feedback": pronunciation_feedback,
        "pronunciation_score": pronunciation_score,
        "image_path": oral_structure_image_path
    }
    
    return feedback


def calculate_pronunciation_score(ipa_standard, ipa_user):
    dummy_score = 93.2
    return dummy_score



# def get_asr_inference(model, audio_data: BytesIO):
#     # librosa.load 함수는 파일 경로 or 파일 객체만 받음.
#     # 따라서 audio는 파일 경로 or 파일 객체.
#     # if isinstance(audio, str):
#     #     pass
#     # else:
#     #     audio = BytesIO(audio.file.read())
    
#     speech_array,_ = librosa.load(audio_data, sr=model.feature_extractor.sampling_rate)
    
#     result = model(speech_array)
    
#     return result['text']