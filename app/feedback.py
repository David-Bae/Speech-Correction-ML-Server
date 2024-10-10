import librosa
from io import BytesIO

import logging
logger = logging.getLogger(__name__)


def get_asr_inference(model, audio):    
    audio = BytesIO(audio.file.read())
    
    speech_array,_ = librosa.load(audio, sr=model.feature_extractor.sampling_rate)
    
    result = model(speech_array)
    
    return result['text']

def get_llm_feedback(ipa_sample, ipa_correct):
    ipa_sample_clean = None
    feedback_img = 0
    feedback = "피드백"

    return ipa_sample_clean, feedback_img, feedback