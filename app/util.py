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


from fastapi import Response

def get_multipart_form_data(**parts):
    """
    주어진 파트들을 Multipart Form Data로 변환하여 반환.
    
    Parameters:
        **parts: Multipart Form Data로 변환할 파트들. 
                 텍스트 파트는 문자열로, 
                 파일 파트는 (filename, content, content_type) 형식의 튜플로 제공됩니다.
    
    Returns:
        Response: 멀티파트 폼 데이터로 변환된 응답 객체
    """
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

    def add_file_part(name, filename, content: BytesIO, content_type):
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
            multipart_body += content.getvalue()  # 이미지 바이너리 데이터 추가
            multipart_body += b'\r\n'

    for key, value in parts.items():
        if isinstance(value, tuple) and len(value) == 3:
            #* 파일 파트 추가 (filename, content, content_type)
            filename, content, content_type = value
            add_file_part(key, filename, content, content_type)
        else:
            #* 텍스트 파트 추가
            add_text_part(key, value)

    # 마지막 경계 추가
    multipart_body += f'--{boundary}--\r\n'.encode('utf-8')

    headers = {
        'Content-Type': f'multipart/form-data; boundary={boundary}'
    }
    
    return Response(content=multipart_body, media_type=f'multipart/form-data; boundary={boundary}', headers=headers)

#! Multi-Part로 변환하면서 사용 X
# def encode_image_to_base64(image_path):
#     with open(image_path, "rb") as image_file:
#         return base64.b64encode(image_file.read()).decode("utf-8")