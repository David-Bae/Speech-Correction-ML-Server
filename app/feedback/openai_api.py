from openai import OpenAI
import base64
from io import BytesIO
from app.feedback.util import compare_ipa_with_word_index
from jamo import h2j, j2hcj

import logging
logger = logging.getLogger(__name__)

client = OpenAI()


def get_asr_role_and_prompt(standard_hangul):    
    role = (
        "오디오의 발음과 동일하게 한국어 문장을 전사하는 역할"
    )
    
    prompt = (
       f"사용자는 '{standard_hangul}'을(를) 발음했습니다. "
       "사용자는 1. 위 문장을 말하거나 2. 다른 문장을 말하거나\n"
       "만약 사용자가 위 문장을 말했다면, 발음을 교정하기 위해 들리는 발음을 한국어로 그대로 전사해 주세요.\n"
        "1. 발음이 표준 발음과 80% 이상 유사하면 그대로 넘어가고, 많이 틀린 발음은 들리는 대로 정확하게 전사해 주세요.\n"
        "2. 단어를 올바르게 보정하지 말고, 들리는 발음 그대로 전사해 주세요.\n"
        "예시: '내 친구는 항상 옆집 아이를 돌봐준다'라는 문장이 '내이 친구는 항상 욥칩 아이 돌봐 준다'로 발음되었다면, "
        "'내이 친구는 항상 욥칩 아이 돌봐 준다'로 전사해 주세요.\n"
        "답변은 오직 발음 그대로의 한국어 전사로만 작성해 주세요.\n\n"
        "단, 음성 파일에서 다른 문장을 말하고 있다면 반드시 1을 반환하세요.\n"
    )
    
    prompt_ = (
       f"오디오 파일에는 '{standard_hangul}'을(를) 발음한 한국어 음성이 포함되어 있습니다. "
       "발음을 교정하기 위해, 들리는 발음을 한국어로 그대로 전사해 주세요.\n"
        "1. 발음이 표준 발음과 80% 이상 유사하면 그대로 넘어가고, 많이 틀린 발음은 들리는 대로 정확하게 전사해 주세요.\n"
        "2. 단어를 올바르게 보정하지 말고, 들리는 발음 그대로 전사해 주세요.\n"
        "예시: '내 친구는 항상 옆집 아이를 돌봐준다'라는 문장이 '내이 친구는 항상 욥칩 아이 돌봐 준다'로 발음되었다면, "
        "'내이 친구는 항상 욥칩 아이 돌봐 준다'로 전사해 주세요.\n"
        "답변은 오직 발음 그대로의 한국어 전사로만 작성해 주세요.\n"
        "단, 음성 파일에서 아무 말도 하지 않는다면 반드시 정말 반드시 1을 반환하세요.\n"
        "또한, 음성 파일에서 다른 문장을 말하고 있다면 반드시 2를 반환하세요."
    )
    return (role, prompt)

def get_asr_gpt(audio_data:BytesIO, standard_hangul:str):
    """
    OpenAI Audio API를 호출하여
    음성 파일에 들어있는 한국어 발화를
    들리는 대로 전사(한글)하여 반환.
    """
    
    logger.info("여기까진 옴1")
    
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

    logger.info("여기까진 옴2")
    
    return response.choices[0].message.content



import pandas as pd
IPA2KO = pd.read_csv('/workspace/app/feedback/table/ipa2ko.csv')
ZA = dict(zip(IPA2KO['IPA'][:32], IPA2KO['Korean'][:32]))
MO = dict(zip(IPA2KO['IPA'][32:], IPA2KO['Korean'][32:]))
MO_HANGUL = list(IPA2KO['Korean'][32:])

MO_INSTRUCTION = None
with open("/workspace/app/feedback/table/mo_pronunciation_instruction.txt", "r") as file:
    MO_INSTRUCTION = file.read()



def get_mo_pronunciation_feedback_role_and_prompt(standard_word, user_word, standard_mo, user_mo):
    role = (
        "당신은 한국어 발음 교정 전문가입니다. "
        "항상 친절하고, 상대방이 쉽게 이해할 수 있도록 명확하고 친근하게 설명해 주세요."
    )
    
    prompt = (
        f"사용자가 '{standard_word}'를 '{user_word}'라고 발음했어요. "
        f"즉 '{standard_mo}'을 '{user_mo}'로 발음했는데, 아래의 모음 발음 방법을 참고하여 피드백을 해주세요.\r\n"
        f"- 피드백은 5문장 이내로 작성하고, '{standard_word}'을(를) 발음할때, '{standard_mo}' 발음이 '{user_mo}' 로 들려요. 로 시작해주세요.\r\n"
        f"-'{user_mo}'에서 '{standard_mo}'로 교정하기 위한 발음 방법을 중심으로 설명해 주세요. (두 발음 방법 차이를 설명)\r\n"
        f"- 이모티콘은 포함하지 않습니다.\r\n"
        f"모음 발음 방법:\r\n"
        f"{MO_INSTRUCTION}"
    )

    return (role, prompt)


def get_pronunciation_feedback_gpt(ipa_standard, ipa_user, standard_hangul, user_hangul):
    """
    OpenAI Audio API를 호출하여
    한글과 IPA를 입력받고,
    IPA에 대한 피드백을 반환.
    """
    # 두 IPA를 비교하여 error를 찾음.
    errors = compare_ipa_with_word_index(ipa_standard, ipa_user)
    logger.info(f"Difference : {errors}")
    
    # error가 없으면 종료.
    if len(errors) == 0:
        return "정확하게 발음했습니다!"
    
    #* 여러 error에 대한 feedback을 저장할 리스트.
    feedbacks = []
    
    
    standard_hangul_words = standard_hangul.split(" ")
    user_hangul_words = user_hangul.split(" ")
    
    prompt = ""
    
    for error in errors:
        word_id, standard_ipa, user_ipa = error
        
        #* error가 발생한 단어.
        standard_word = standard_hangul_words[word_id]
        user_word = user_hangul_words[word_id]
        
        if (standard_ipa in MO) and (user_ipa in MO):
            role, prompt = get_mo_pronunciation_feedback_role_and_prompt(standard_word, user_word, MO[standard_ipa], MO[user_ipa])
            
            feedback = client.chat.completions.create(
                model="chatgpt-4o-latest",
                messages=[
                    {"role": "system", "content": role},
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            #! 아직 모음 피드백 하나만 반환.
            return feedback.choices[0].message.content

    if not prompt:
        return "아직 자음 피드백은 구현하지 않았습니다."