# import librosa
# import numpy as np
# from io import BytesIO

from app.feedback import openai_api
from app.hangul2ipa.worker import hangul2ipa
from difflib import SequenceMatcher



import logging
logger = logging.getLogger(__name__)


def get_pronunciation_feedback(audio_data, standard_hangul):
    transcription = openai_api.get_asr_gpt(audio_data, standard_hangul)
    
    feedback = {
        "transcription": None,
        "pronunciation_feedback": None,
        "pronunciation_score": None,
        "image_path": None,
        "error_code": 0
    }
    
    #? 사용자가 정상적인 발화를 했다면.
    if transcription == '1':
        feedback['error_code'] = 1
    else:
        standard_ipa = hangul2ipa(standard_hangul)
        user_ipa = hangul2ipa(transcription)
        
        logger.info("*"*50)
        logger.info(f"문장       : {standard_hangul}")
        logger.info(f"사용자 발음: {transcription}")
        logger.info(f"문장 IPA   : {standard_ipa}")
        logger.info(f"사용자 IPA : {user_ipa}")
        logger.info("*"*50)
        
        #! ipa_standard와 ipa_user 비교하여 feedback 하는 함수 호출
        feedback["pronunciation_feedback"] = openai_api.get_pronunciation_feedback_gpt(standard_ipa, user_ipa, standard_hangul, transcription)
        feedback["oral_structure_image_path"] = "/workspace/app/images/요to여.png"
        
        #! 발화 점수 계산
        feedback["pronunciation_score"] = calculate_pronunciation_score(standard_ipa, user_ipa)
    
    return feedback


def calculate_pronunciation_score(original_ipa, user_ipa):
    """
    Levenshtein 거리 기반으로 유사도 점수를 계산하는 함수
    0 ~ 100 사이의 실수(소수점 아래 둘째자리) 반환
    """
    matcher = SequenceMatcher(None, original_ipa, user_ipa)
    
    match_ratio = matcher.ratio()
    
    pronunciation_score = round(match_ratio*100, 2)
    
    return pronunciation_score









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