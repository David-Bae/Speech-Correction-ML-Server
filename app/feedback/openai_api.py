import sys
sys.path.append("/workspace")

from openai import OpenAI
import base64
from io import BytesIO
from app.feedback.ipa_processing import compare_ipa_with_word_index
from jamo import h2j, j2hcj
from app.util import FeedbackStatus
import pandas as pd

import logging
logger = logging.getLogger(__name__)

client = OpenAI()


def get_asr_role_and_prompt(standard_hangul, threshold=50):
    role = (
        "오디오의 발음과 동일하게 한국어 문장을 전사하는 역할"
    )

    prompt = (
        f"주어진 문장: '{standard_hangul}'\n"

        "사용자가 위 문장을 발음했습니다.\n"
        "사용자는 1. 주어진 문장을 말하거나 2. 다른 문장을 말할 수 있습니다.\n"
        "사용자가 주어진 문장을 말했다면, 발음을 교정하기 위해 들리는 발음을 한국어로 그대로 전사해 주세요.\n"
        f"1. 발음이 '주어진 문장'과 {threshold}% 이상 유사하면 그대로 두고, 많이 틀린 발음은 들리는 대로 정확하게 전사해 주세요.\n"
        "2. 단어를 올바르게 수정하지 말고, 들리는 발음 그대로 전사해 주세요.\n"
        "예시: '내 친구는 항상 옆집 아이를 돌봐준다'라는 문장이 '내이 친구는 항상 욥칩 아이 돌봐 준다'로 발음되었다면, "
        "'내이 친구는 항상 욥칩 아이 돌봐 준다'로 전사해 주세요.\n"
        "답변은 오직 발음 그대로의 한국어 전사로만 작성해 주세요.\n\n"
        "단, 음성 파일에서 다른 문장을 말하고 있다면 반드시 '1'을 반환하세요.\n"
    )

    return (role, prompt)






def get_asr_gpt(audio_data:BytesIO, standard_hangul:str):
    """
    OpenAI Audio API를 호출하여
    음성 파일에 들어있는 한국어 발화를
    들리는 대로 전사(한글)하여 반환.
    """
    
    role, prompt = get_asr_role_and_prompt(standard_hangul)

    audio_file_base64 = base64.b64encode(audio_data.read()).decode('utf-8')
    
    response = client.chat.completions.create(
        model="gpt-4o-audio-preview",
        modalities=["text"],
        messages=[
            {"role": "system", "content": role},
            {
                "role": "user",
                "content": [
                    { 
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_file_base64,
                            "format": "wav"
                        }
                    }
                ]
            },
        ],
        temperature=0
    )
    
    return response.choices[0].message.content


    
"""
피드백 문장 생성을 위한 함수
모든 피드백 생성 완료
"""
# MO_INSTRUCTION = None
# with open("/workspace/app/feedback/table/mo_pronunciation_instructions.csv", "r") as file:
#     MO_INSTRUCTION = pd.read_csv(file)


# def get_role_and_prompt_for_pregenerated_mo_pronunciation_feedback(standard_mo, user_mo):
#     role = (
#         "당신은 한국어 발음을 교정해주는 전문 교육자입니다.\n\n"
#         "다음의 원칙을 반드시 준수해주세요:\n"
#         "1. 학습자의 현재 발음 상태를 정확히 파악하고 개선점을 제시합니다.\n"
#         "2. 발음 교정 방법을 구체적이고 단계적으로 설명합니다.\n"
#         "3. 입 모양과 혀의 위치를 해부학적으로 정확하게 설명합니다.\n"
#         "4. 학습자가 이해하기 쉽도록 명확하고 간단한 문장을 사용합니다.\n"
#         "5. 항상 긍정적이고 격려하는 톤을 유지합니다."
#     )
    
#     prompt = (
#         f"[발음 교정 요청]\n"
#         f"- 목표 발음: '{standard_mo}'\n" 
#         f"- 현재 발음: '{user_mo}'\n\n"
#         f"[피드백 작성 요구사항]\n"
#         f"1. 정확히 3개의 문장으로 구성하여 다음 순서로 작성해주세요:\n"
#         f"   a) 입 모양 교정 방법\n"
#         f"   b) 혀 위치 교정 방법\n"
#         f"   c) 두 발음의 핵심적 차이점\n\n"
#         f"2. 반드시 '{user_mo}'에서 '{standard_mo}'로 개선하는 방향으로 설명해주세요.\n"
#         f"3. 모음을 언급할 때는 반드시 작은따옴표로 묶어서 표기해주세요. (예: '{user_mo}', '{standard_mo}')\n"
#         f"4. 이모티콘이나 특수문자는 사용하지 마세요.\n"
#         f"5. '피드백:', '교정 방법:', '1. ' 등의 제목이나 부가 설명 없이 순수 피드백 문장만 작성해주세요.\n\n"
#         f"[참고 자료 - 표준 모음 발음법]\n"
#         f"{MO_INSTRUCTION}"
#     )

#     return (role, prompt)


# def get_pregenerated_mo_pronunciation_feedback(standard_mo, user_mo):
#     role, prompt = get_role_and_prompt_for_pregenerated_mo_pronunciation_feedback(standard_mo, user_mo)

#     feedback = client.chat.completions.create(
#         model="chatgpt-4o-latest",
#         messages=[
#             {"role": "system", "content": role},
#             {
#                 "role": "user",
#                 "content": prompt
#             }
#         ],
#         temperature=0
#     )

#     feedback_text = feedback.choices[0].message.content
#     return feedback_text


# JA_INSTRUCTION = None
# with open("/workspace/app/feedback/table/ja_pronunciation_instructions.csv", "r") as file:
#     JA_INSTRUCTION = pd.read_csv(file)
# JA = JA_INSTRUCTION['Ja']


# def get_role_and_prompt_for_pregenerated_ja_pronunciation_feedback(from_ja, to_ja):
#     role = (
#         "당신은 한국어 발음을 교정해주는 전문 교육자입니다.\n\n"
#         "다음의 원칙을 반드시 준수해주세요:\n"
#         "1. 학습자의 현재 발음 상태를 정확히 파악하고 개선점을 제시합니다.\n"
#         "2. 발음 교정 방법을 구체적이고 단계적으로 설명합니다.\n"
#         "3. 입 모양과 혀의 위치를 해부학적으로 정확하게 설명합니다.\n"
#         "4. 학습자가 이해하기 쉽도록 명확하고 간단한 문장을 사용합니다.\n"
#         "5. 항상 긍정적이고 격려하는 톤을 유지합니다."
#     )
    
#     prompt = (
#         f"[발음 교정 요청]\n"
#         f"- 목표 발음: '{to_ja}'\n" 
#         f"- 현재 발음: '{from_ja}'\n\n"
#         f"[피드백 작성 요구사항]\n"
#         f"1. 두 발음의 다음 두가지 차이점을 중심으로 비교하며 2개의 문장으로 짧게 작성해주세요:\n"
#         f"   a) 혀 위치 교정 방법\n"
#         f"   b) 발음할 때 공기를 내보내는 세기\n"
#         f"2. 반드시 '{from_ja}'에서 '{to_ja}'로 개선하는 방향으로 설명해주세요.\n"
#         # f"3. 자음을 언급할 때는 반드시 작은따옴표로 묶어서 표기해주세요. (예: '{from_ja}', '{to_ja}')\n"
#         f"3. 이모티콘이나 특수문자는 사용하지 마세요.\n"
#         f"4. '피드백:', '교정 방법:', '1. ' 등의 제목이나 부가 설명 없이 순수 피드백 문장만 작성해주세요.\n\n"
#         f"[참고 자료 - 표준 자음 발음법]\n"
#         f"{JA_INSTRUCTION}"
#     )

#     return (role, prompt)


# def get_pregenerated_ja_pronunciation_feedback(from_ja, to_ja):
#     role, prompt = get_role_and_prompt_for_pregenerated_ja_pronunciation_feedback(from_ja, to_ja)

#     feedback = client.chat.completions.create(
#         model="chatgpt-4o-latest",
#         messages=[
#             {"role": "system", "content": role},
#             {
#                 "role": "user",
#                 "content": prompt
#             }
#         ],
#         temperature=0
#     )

#     feedback_text = feedback.choices[0].message.content
#     return feedback_text


if __name__ == "__main__":
    pass


"""
! 사용하지 않는 함수
"""
# def get_pronunciation_feedback_gpt_deprecated(ipa_standard, ipa_user, standard_hangul, user_hangul):
#     """
#     <Role>
#         1. 두 IPA를 비교하여 틀린 부분 찾기 <- compare_ipa_with_word_index
#         2. 에러가 발생한 단어에 대해 피드백 문장 생성 <- get_mo_pronunciation_feedback_role_and_prompt #! 이 부분을 대체
#         3. 피드백 문장 번호와 이미지 번호 반환
        
#     *feedbacks: 각 틀린 부분에 대한 피드백 저장.
#     *feedback_images: 각 틀린 부분에 대한 피드백 이미지 이름 저장. (이미지는 spring 서버에 있음)
#     *status: FeedbackStatus - PRONUNCIATION_SUCCESS / FEEDBACK_PROVIDED / NOT_IMPLEMENTED
#     """
#     #* 여러 error에 대한 feedback과 image 이름을 저장할 리스트.
#     feedbacks = []
#     feedback_images = []
#     status = FeedbackStatus.PRONUNCIATION_SUCCESS
    
#     # 두 IPA를 비교하여 error를 찾음.
#     errors = compare_ipa_with_word_index(ipa_standard, ipa_user)
#     logger.info(f"Difference : {errors}")
    
#     # error가 1개 이상이면 피드백 생성
#     if len(errors) > 0:
#         standard_hangul_words = standard_hangul.split(" ")
#         user_hangul_words = user_hangul.split(" ")
        
#         for error in errors:
#             word_id, standard_ipa, user_ipa = error
            
#             #* error가 발생한 단어.
#             standard_word = standard_hangul_words[word_id]
#             user_word = user_hangul_words[word_id]
            
#             if (standard_ipa in MO) and (user_ipa in MO):
#                 standard_mo = MO[standard_ipa]
#                 user_mo = MO[user_ipa]
#                 role, prompt = get_mo_pronunciation_feedback_role_and_prompt(standard_word, user_word, standard_mo, user_mo)
                
#                 feedback = client.chat.completions.create(
#                     model="chatgpt-4o-latest",
#                     messages=[
#                         {"role": "system", "content": role},
#                         {
#                             "role": "user",
#                             "content": prompt
#                         }
#                     ]
#                 )
                
#                 feedback_text = feedback.choices[0].message.content
#                 feedbacks.append(feedback_text)
                
#                 feedback_images.append(f"/workspace/app/images/mo_transition/{standard_mo}_{user_mo}.jpg")
#                 #! 아직 모음 피드백 하나만 반환.
#                 break
        
#         # 피드백을 정상적으로 생성한 경우
#         if len(feedbacks) > 0:
#             status = FeedbackStatus.FEEDBACK_PROVIDED
#         # 에러는 있지만 피드백을 생성하지 못한 경우
#         else:
#             status = FeedbackStatus.NOT_IMPLEMENTED

#     return {
#         "feedbacks": feedbacks,
#         "feedback_images": feedback_images,
#         "status": status
#     }
