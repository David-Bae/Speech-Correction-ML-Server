import logging
logger = logging.getLogger(__name__)


from pydub import AudioSegment
from io import BytesIO
import librosa
import numpy as np
from PIL import Image

class FeedbackStatus:
    PRONUNCIATION_SUCCESS = 1   # 틀린 부분 없음
    FEEDBACK_PROVIDED = 2       # 피드백 생성
    NO_SPEECH = 3               # 말이 없음
    WRONG_SENTENCE = 4          # 다른 문장 발음
    NOT_IMPLEMENTED = 5         # 아직 구현 안됨
    WRONG_WORD_COUNT = 6        # 단어 개수 다름


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
    if image is None:
        logger.error("3. convert_Image_to_BytesIO: Image is None")
    else:
        logger.info("3. convert_Image_to_BytesIO: Image is not None")

    image_binary = BytesIO()
    image.save(image_binary, format="PNG")
    image_binary.seek(0)  # 파일 포인터를 처음 위치로 이동

    if image_binary is None:
        logger.error("4. convert_Image_to_BytesIO: Image binary is None")
    else:
        logger.info("4. convert_Image_to_BytesIO: Image binary is not None")
    
    return image_binary





#! Multi-Part로 변환하면서 사용 X
# def encode_image_to_base64(image_path):
#     with open(image_path, "rb") as image_file:
#         return base64.b64encode(image_file.read()).decode("utf-8")