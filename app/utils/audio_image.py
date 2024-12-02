import logging
logger = logging.getLogger(__name__)


from pydub import AudioSegment
from io import BytesIO
import librosa
import numpy as np
from PIL import Image

def convert_any_to_wav(audio_data: BytesIO, filename) -> BytesIO:
    """
    다양한 format의 BytesIO를 wav format의 BytesIO로 변환
    """

    if filename.endswith(".3gp"):
        wav_audio_data = convert_3gp_to_wav(audio_data)
    elif filename.endswith(".wav"):
        wav_audio_data = audio_data
        
    return wav_audio_data


def convert_3gp_to_wav(three_gp_data: BytesIO) -> BytesIO:
    """
    Converts a 3gp audio file to wav format.
    
    Parameters:
        three_gp_data (BytesIO): The 3gp audio data as a BytesIO object.
        
    Returns:
        BytesIO: The converted wav audio data as a BytesIO object.
    """    
    # 3gp 파일을 AudioSegment로 로드
    audio_segment = AudioSegment.from_file(three_gp_data, format="3gp")
    
    # wav 형식으로 변환하여 BytesIO 객체에 저장
    wav_data = BytesIO()
    audio_segment.export(wav_data, format="wav")
    wav_data.seek(0)  # 파일 포인터를 처음 위치로 이동
    
    return wav_data


def is_not_speaking(audio, threshold=0.0001):
    y,_ = librosa.load(audio, sr=None)
    
    # 오디오 신호의 에너지 계산
    energy = np.sum(y ** 2) / len(y)
    
    logger.info(f"Energy: {energy}")
    
    # 에너지가 임계값보다 작으면 말이 없다고 판단
    return energy < threshold



def convert_Image_to_BytesIO(image: Image) -> BytesIO:
    """
    PIL의 Image 객체를 바이트 문자열로 변환
    
    Parameters:
        image (Image): PIL Image 객체
        
    Returns:
        bytes: 변환된 이미지의 바이트 문자열
    """

    image_binary = BytesIO()
    image.save(image_binary, format="PNG")
    image_binary.seek(0)  # 파일 포인터를 처음 위치로 이동
    
    return image_binary