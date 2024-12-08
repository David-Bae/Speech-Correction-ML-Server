import logging
logger = logging.getLogger(__name__)


from pydub import AudioSegment
from io import BytesIO
import librosa
import numpy as np
from PIL import Image
from tempfile import NamedTemporaryFile
import subprocess




def convert_any_to_wav(audio) -> BytesIO:
    """
    다양한 format의 BytesIO를 wav format의 BytesIO로 변환
    """
    filename = audio.filename
    
    if filename.endswith(".3gpp"):
        wav_audio_data = convert_3gpp_to_wav_bytesio(audio)
    elif filename.endswith(".3gp"):
        audio_data = BytesIO(audio.file.read())
        wav_audio_data = convert_3gp_to_wav(audio_data)
    elif filename.endswith(".wav"):
        audio_data = BytesIO(audio.file.read())
        wav_audio_data = audio_data
        
    return wav_audio_data

def convert_3gpp_to_wav_bytesio(audio):
    # 임시 파일에 3gpp 파일 저장
    with NamedTemporaryFile(suffix=".3gpp", delete=False) as temp_3gpp:
        temp_3gpp.write(audio.file.read())
        temp_3gpp_path = temp_3gpp.name
    
    # 변환 후 저장될 WAV 파일 경로
    temp_wav_path = temp_3gpp_path.replace(".3gpp", ".wav")

    # ffmpeg 명령어 실행
    # -y 옵션은 파일이 있을 경우 덮어쓰기
    ffmpeg_cmd = ["ffmpeg", "-i", temp_3gpp_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", "-y", temp_wav_path]

    subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    # 변환 완료 후 WAV 파일을 AudioSegment로 로드
    wav_audio_data = AudioSegment.from_file(temp_wav_path, format="wav")

    # AudioSegment를 BytesIO로 export
    wav_bytes_io = BytesIO()
    wav_audio_data.export(wav_bytes_io, format="wav")
    wav_bytes_io.seek(0)  # 포인터를 맨 앞으로 이동
    
    return wav_bytes_io


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