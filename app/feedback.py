import librosa
from io import BytesIO
import numpy as np

import logging
logger = logging.getLogger(__name__)


def get_asr_inference(model, audio):
    # librosa.load 함수는 파일 경로 or 파일 객체만 받음.
    # 따라서 audio는 파일 경로 or 파일 객체.
    if isinstance(audio, str):
        pass
    else:
        audio = BytesIO(audio.file.read())
        
    logger.info(f"{audio}")
    
    speech_array,_ = librosa.load(audio, sr=model.feature_extractor.sampling_rate)
    
    result = model(speech_array)
    
    return result['text']

def get_llm_feedback(ipa_sample, ipa_correct):
    ipa_sample_clean = None
    feedback_img = 0
    feedback = "피드백"

    return ipa_sample_clean, feedback_img, feedback