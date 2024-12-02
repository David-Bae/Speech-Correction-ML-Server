import sys
sys.path.append("/workspace")

from openai import OpenAI
import base64
from io import BytesIO

import logging
logger = logging.getLogger(__name__)

client = OpenAI()

def call_gpt_audio_api(audio_data:BytesIO, role:str, prompt:str):
    """
    OpenAI Audio API를 호출
    """
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


def get_asr_gpt(audio_data:BytesIO, standard_hangul:str, threshold=50):
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
    
    result = call_gpt_audio_api(audio_data, role, prompt)

    return result



def classify_sentence_type(audio_data:BytesIO):
    role = (
        "한국어 음성의 오디오를 분석하여 의문문, 청유문, 감탄문, 평서문과 같은 문장 유형을 분류하는 역할"
    )

    prompt = (
        "주어진 오디오 파일에 들어있는 한국어 음성을 분석하여 의문문, 청유문, 감탄문, 평서문과 같은 문장 유형을 분류하세요."
        "문맥을 통해 문장 유형을 판단하지 말고, 오직 억양과 높낮이를 분석하여 문장 유형을 분류해 주세요."
        "예를 들어 '오늘도 바빠?'라는 문장을 평서문처럼 '오늘도 바빠.'라고 발음했다면, 이 문장은 평서문으로 분류해 주세요."
        "의문문:0, 평서문:1, 감탄문:2, 청유문:3 - 답변은 번호로만 작성해 주세요."
    )
    
    result = call_gpt_audio_api(audio_data, role, prompt)
    
    try:
        return int(result)
    except:
        logger.error(f"Failed to classify sentence type: {result}")
        return -1

