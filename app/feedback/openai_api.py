from openai import OpenAI
import base64
from io import BytesIO

client = OpenAI()

PROMPT_KO = """
오디오 파일에는 한국어 음성이 포함되어 있습니다.
발음 교정을 위해, 들리는 발음을 그대로 한글로 전사해 주세요.
들리는 그대로 정확하게 전사하며, 원래 문장을 보정하거나 수정하지 말아 주세요.
답변은 오직 발음 그대로의 한국어 전사로만 작성해 주세요.
예를 들어, '내 친구는 항상 옆집 아이를 돌봐준다'라는 문장이 '내이 친구는 항상 욥칩 아이 돌봐 준다'로 발음되었다면,
단어들을 올바르게 보정하지 말고 들리는 그대로 전사해 주세요.
"""


"""
OpenAI Audio API를 호출하여
음성 파일에 들어있는 한국어 발화를
들리는 대로 전사(한글)하여 반환.
"""
def get_asr_gpt(audio_data:BytesIO):
    audio_file_base64 = base64.b64encode(audio_data.read()).decode('utf-8')
    
    response = client.chat.completions.create(
        model="gpt-4o-audio-preview",
        modalities=["text"],
        messages=[
            {
                "role": "user",
                "content": [
                    { 
                        "type": "text",
                        "text": PROMPT_KO
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
        ]
    )
    
    return response.choices[0].message.content



"""
OpenAI Audio API를 호출하여
한글과 IPA를 입력받고,
IPA에 대한 피드백을 반환.
? 아직 매개변수는 미정.
"""
def get_pronunciation_feedback_gpt():
    dummy_feedback = "'ㅏ'를 발음할 때, 입모양을 더 크게 하세요."
    return dummy_feedback