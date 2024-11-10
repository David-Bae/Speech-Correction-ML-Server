from app.feedback import openai_api
from app.hangul2ipa.worker import hangul2ipa
from difflib import SequenceMatcher
from app.util import FeedbackStatus
from app.feedback.ipa_processing import compare_ipa_with_word_index
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

import logging
logger = logging.getLogger(__name__)


def get_pronunciation_feedback(audio_data, standard_hangul):
    """        
    Process
    -------
    1. OpenAI Audio API를 사용하여 음성을 텍스트로 변환 (get_asr_gpt)
    2. 사용자가 다른 문장을 말한 경우 예외 처리
    3. 정답 문장과 사용자 발화를 IPA(국제음성기호)로 변환 
    4. 두 IPA를 비교하여 발음 오류 검출 및 피드백 생성
    
    Returns
    -------
    dict
        *status : int
            피드백 생성 상태 (FeedbackStatus)
        *transcription : str
            사용자 발화 전사 텍스트
        *feedback_count : int
            생성된 피드백 개수
        *word_index : list
            오류가 발생한 단어의 인덱스 리스트
        *pronunciation_feedbacks : list
            발음 교정 피드백 텍스트 리스트
        *feedback_image_names : list
            피드백 관련 이미지 파일명 리스트
        *wrong_spellings : list
            잘못 발음한 음소 리스트
        *pronunciation_score : float
            발음 평가 점수 (0-100)
    """
    status = 0
    transcription = ""
    feedback_count = 0
    word_indexes = []
    pronunciation_feedbacks = []
    feedback_image_names = []
    wrong_spellings = []
    pronunciation_score = 0.0
    
    #! <OpenAI Audio ASR>: 사용자의 발화를 텍스트로 변환
    transcription = openai_api.get_asr_gpt(audio_data, standard_hangul)

    
    if transcription == '1':
    #! <Wrong Sentence>: 사용자가 다른 문장을 말한 경우
        status = FeedbackStatus.WRONG_SENTENCE
    else:
    
        standard_ipa = hangul2ipa(standard_hangul)
        user_ipa = hangul2ipa(transcription)
        
        # logger.info("*"*50)
        # logger.info(f"문장       : {standard_hangul}")
        # logger.info(f"사용자 발음: {transcription}")
        # logger.info(f"문장 IPA   : {standard_ipa}")
        # logger.info(f"사용자 IPA : {user_ipa}")
        # logger.info("*"*50)
        
        #! <Pronunciation Feedback>: 사용자의 발음을 분석하여 피드백 생성
        with ThreadPoolExecutor() as executor:
            feedback_response = executor.submit(get_pregenerated_pronunciation_feedback, standard_ipa, user_ipa, standard_hangul, transcription)
            score_future = executor.submit(calculate_pronunciation_score, standard_ipa, user_ipa)

            feedback_response = feedback_response.result()
            pronunciation_score = score_future.result()

        status = feedback_response['status']
        feedback_count = len(feedback_response['pronunciation_feedbacks'])
        word_indexes = feedback_response['word_indexes']
        pronunciation_feedbacks = feedback_response['pronunciation_feedbacks']
        feedback_image_names = feedback_response['feedback_image_names']
        wrong_spellings = feedback_response['wrong_spellings']

    return{
        "status": status,
        "transcription": transcription,
        "feedback_count": feedback_count,
        "word_indexes": word_indexes,
        "pronunciation_feedbacks": pronunciation_feedbacks,
        "feedback_image_names": feedback_image_names,
        "wrong_spellings": wrong_spellings,
        "pronunciation_score": pronunciation_score,   
    }


"""
변경 사항
1. 피드백 문장 생성 방법 변경. (gpt 생성 -> 미리 생성된 피드백 테이블 사용)
"""

IPA2KO = pd.read_csv('/workspace/app/feedback/table/ipa2ko.csv')
ZA = dict(zip(IPA2KO['IPA'][:32], IPA2KO['Korean'][:32]))
MO = dict(zip(IPA2KO['IPA'][32:], IPA2KO['Korean'][32:]))
MO_HANGUL = list(IPA2KO['Korean'][32:])

pregenerated_feedback_csv_path = "/workspace/app/feedback/table/pregenerated_feedback.csv"
PREGENERATED_FEEDBACK = pd.read_csv(pregenerated_feedback_csv_path)

def get_pregenerated_pronunciation_feedback(ipa_standard, ipa_user, standard_hangul, user_hangul):
    """
    <Role>
        1. 두 IPA를 비교하여 틀린 부분 찾기 <- compare_ipa_with_word_index
        2. 에러가 발생한 단어에 대해 피드백 문장 찾기
        3. 피드백 문장 번호와 이미지 번호 반환
        
    *feedbacks: 각 틀린 부분에 대한 피드백 저장.
    *feedback_images: 각 틀린 부분에 대한 피드백 이미지 이름 저장. (이미지는 spring 서버에 있음)
    *status: FeedbackStatus - PRONUNCIATION_SUCCESS / FEEDBACK_PROVIDED / NOT_IMPLEMENTED
    """
    #* 여러 error에 대한 feedback과 image 이름을 저장할 리스트.
    status = 0
    word_indexes = []
    pronunciation_feedbacks = []
    feedback_image_names = []
    wrong_spellings = []
    
    # 두 IPA를 비교하여 error를 찾음.
    errors = compare_ipa_with_word_index(ipa_standard, ipa_user)
    logger.info(f"Difference : {errors}")
    
    
    if len(errors) == 0:
        #! 틀린 부분이 없는 경우
        status = FeedbackStatus.PRONUNCIATION_SUCCESS
    else:
        #! 틀린 부분이 1개 이상이면 피드백 생성
        # standard_hangul_words = standard_hangul.split(" ")
        # user_hangul_words = user_hangul.split(" ")
        
        for error in errors:
            word_id, standard_ipa, user_ipa = error
            
            # error가 발생한 단어.
            # standard_word = standard_hangul_words[word_id] 
            # user_word = user_hangul_words[word_id]
            
            if (standard_ipa in MO) and (user_ipa in MO):
                before_mo = MO[user_ipa]
                after_mo = MO[standard_ipa]
                
                # 피드백 찾기
                combination = f"{before_mo}_{after_mo}"
                feedback = PREGENERATED_FEEDBACK[PREGENERATED_FEEDBACK["combination"] == combination]["feedback"].values[0]
                
                #* 틀린 부분의 단어 인덱스 저장
                word_indexes.append(word_id)
                #* 피드백 저장
                pronunciation_feedbacks.append(feedback)
                #* 피드백 이미지 이름 저장
                feedback_image_names.append(f"{before_mo}_{after_mo}.jpg")
                #* 잘못 발음한 음소 저장
                wrong_spellings.append(f"{after_mo}")
               
                # break #! 아직 모음 피드백 하나만 반환.
        
        if len(pronunciation_feedbacks) > 0:
            #! 피드백을 정상적으로 생성한 경우
            status = FeedbackStatus.FEEDBACK_PROVIDED
        else:
            #! 아직 구현되지 않은 기능인 경우
            status = FeedbackStatus.NOT_IMPLEMENTED

    return {
        "status": status,
        "word_indexes": word_indexes,
        "pronunciation_feedbacks": pronunciation_feedbacks,
        "feedback_image_names": feedback_image_names,
        "wrong_spellings": wrong_spellings,
        "status": status
    }



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