import subprocess
from tempfile import TemporaryDirectory
import os
import textgrid

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#! 중요
MFA_RESULTS_DIRECTORY = "/workspace/app/feedback/intonation/mfa_results"

INTONATION_SENTENCES_DIRECTORY = "/workspace/app/feedback/intonation_sentences"
MFA_ACOUSTIC_MODEL_PATH = "/mfa/pretrained_models/acoustic/korean_mfa.zip"
MFA_DICTIONARY_PATH = "/mfa/pretrained_models/dictionary/korean_mfa.dict"


#! MFA를 수행하고 나서, TextGrid 파일에서 단어 시간 정보 추출
def get_mfa_alignment_result_from_file(file_name):
    #* MFA 결과 파일에서 단어 정보 추출
    textgrid_path = os.path.join(MFA_RESULTS_DIRECTORY, f"{file_name}.TextGrid")
    tg = textgrid.TextGrid.fromFile(textgrid_path)

    word_tier = tg.getFirst('words')
    words_time_info = []
    for interval in word_tier:
        start_time = interval.minTime
        end_time = interval.maxTime
        text = interval.mark
        if text.strip():  # 공백이 아닌 경우에만 추가
            words_time_info.append({'start': start_time, 'end': end_time, 'text': text})
    
    return words_time_info


#! MFA를 실행하여 {MFA_RESULTS_DIRECTORY}에 TextGrid 파일 생성
def execute_mfa_alignment(audio_data, sentence, sentence_number):
    with TemporaryDirectory() as temp_dir:
        #* 임시 폴더에 오디오 파일 저장
        audio_file_path = os.path.join(temp_dir, f"{sentence_number}.wav")
        with open(audio_file_path, "wb") as audio_file:
            audio_file.write(audio_data.getvalue())

        #* 임시 폴더에 텍스트 파일 저장
        text_file_path = os.path.join(temp_dir, f"{sentence_number}.txt")
        with open(text_file_path, "w") as text_file:
            text_file.write(sentence)

        #* MFA 실행
        align_mfa(temp_dir, MFA_DICTIONARY_PATH, MFA_ACOUSTIC_MODEL_PATH, MFA_RESULTS_DIRECTORY)

#! MFA 호출하는 함수 (직접적으로 사용되지 않음)
def align_mfa(corpus_directory, dictionary_path, acoustic_model_path, output_directory):
    command = [
        'mfa', 'align',
        corpus_directory,
        dictionary_path,
        acoustic_model_path,
        output_directory
    ]
    
    try:
        subprocess.run(command, check=True)
        logger.info("Alignment completed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"An error occurred: {e}")