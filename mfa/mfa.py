import subprocess
from tempfile import TemporaryDirectory
import os

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#! 중요
MFA_ACOUSTIC_MODEL_PATH = "/mfa/pretrained_models/acoustic/korean_mfa.zip"
MFA_DICTIONARY_PATH = "/mfa/pretrained_models/dictionary/korean_mfa.dict"
MFA_RESULTS_DIRECTORY = "/workspace/mfa/mfa_results"


#! MFA 호출하는 함수 (직접적으로 사용되지 않음)
def align_mfa(folder_name):
    command = [
        'mfa', 'align',
        folder_name,
        MFA_DICTIONARY_PATH,
        MFA_ACOUSTIC_MODEL_PATH,
        MFA_RESULTS_DIRECTORY
    ]
    
    try:
        subprocess.run(command, check=True)
        logger.info("Alignment completed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"An error occurred: {e}")



# #! MFA를 실행하여 {MFA_RESULTS_DIRECTORY}에 TextGrid 파일 생성 (deprecated)
# def execute_mfa_alignment(audio_data, sentence, sentence_number):
#     with TemporaryDirectory() as temp_dir:
#         #* 임시 폴더에 오디오 파일 저장
#         audio_file_path = os.path.join(temp_dir, f"{sentence_number}.wav")
#         with open(audio_file_path, "wb") as audio_file:
#             audio_file.write(audio_data.getvalue())

#         #* 임시 폴더에 텍스트 파일 저장
#         text_file_path = os.path.join(temp_dir, f"{sentence_number}.txt")
#         with open(text_file_path, "w") as text_file:
#             text_file.write(sentence)

#         #* MFA 실행
#         align_mfa(temp_dir, MFA_DICTIONARY_PATH, MFA_ACOUSTIC_MODEL_PATH, MFA_RESULTS_DIRECTORY)