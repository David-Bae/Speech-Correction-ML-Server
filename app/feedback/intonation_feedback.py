from app.models import FeedbackStatus
from app.feedback.intonation.pitch import get_time_and_pitch
from app.feedback.intonation.intonation_graph_generator import plot_intonation_graph
from app.feedback.openai_api import classify_sentence_type
from io import BytesIO
import concurrent.futures

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


sentence_type_dict = {
    0: "의문문",
    1: "평서문",
    2: "감탄문",
    3: "청유문"
}

correct_sentence_type_feedback_dict = {
    0: "의문문을 자연스럽게 발음했어요! 말의 끝이 올라가서 질문 의도가 분명하게 전달되었어요.",
    1: "평서문을 안정적으로 말했어요! 정보나 의견을 명확히 전달했네요.",
    2: "감탄문에서 감정을 잘 표현했어요! 기쁨이나 놀라움이 확실히 느껴졌어요.",
    3: "청유문을 부드럽게 말했어요! 상대방이 함께 하고 싶어질 것 같아요."
}

incorrect_sentence_type_feedback_dict = {
    0: "의문문은 말의 끝부분이 올라가는 경우가 많아요. 문장의 마지막 단어를 조금 더 높고 부드럽게 말해보세요. 그러면 상대방이 질문임을 바로 알 수 있어요.",
    1: "평서문은 억양이 일정하고 끝이 내려가는 경우가 많아요. 마지막 단어를 낮은 음으로 안정감 있게 마무리해보세요.",
    2: "감탄문은 강하게 강조하거나, 말의 중간이나 끝이 올라가는 경우가 많아요. 감정을 표현할 때는 말의 중간에 강세를 주거나 끝에서 높게 말해보세요.",
    3: "청유문은 의문문처럼 들리지만, 끝부분이 약간 더 부드럽고 낮게 마무리돼요. 말의 끝을 높이되, 부드럽고 따뜻하게 발음해보세요."
}


from app.feedback.intonation.pitch import calculate_intonation_score


def get_intonation_feedback(audio_data, sentence_code):
    """
    억양 피드백 생성 함수
    """
    status = FeedbackStatus.PRONUNCIATION_SUCCESS
    feedback_text = ""
    intonation_score = 0.0
    feedback_image = None   
    
    audio_data_copy = BytesIO(audio_data.getvalue())
    
    def generate_feedback_image_and_score(audio_data):
        #* 사용자 음성에서 Pitch 데이터 추출
        user_time, user_pitch = get_time_and_pitch(audio_data)
        
        #* 음성 높낮이 그래프 이미지 생성
        feedback_image = plot_intonation_graph(user_time, user_pitch)
        
        #* 억양 점수 계산
        intonation_score = calculate_intonation_score(user_time, user_pitch, sentence_code)
        
        return feedback_image, intonation_score

    def generate_feedback_text(audio_data, sentence_code):
        #* 억양 피드백 텍스트 생성
        ref_sentence_type = int(sentence_code.split("_")[0])
        user_sentence_type = classify_sentence_type(audio_data)
        
        logger.info(f"ref_sentence_type: {ref_sentence_type}, user_sentence_type: {user_sentence_type}")
        
        if user_sentence_type not in sentence_type_dict:
            return "알 수 없는 문장 유형"
        
        if user_sentence_type == ref_sentence_type:
            feedback_text = correct_sentence_type_feedback_dict[user_sentence_type]
        else:
            feedback_text = f"'{sentence_type_dict[user_sentence_type]}'처럼 들려요. {incorrect_sentence_type_feedback_dict[ref_sentence_type]}"

        return feedback_text

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_pitch_data = executor.submit(generate_feedback_image_and_score, audio_data_copy)
        future_feedback_text = executor.submit(generate_feedback_text, audio_data, sentence_code)

        feedback_image, intonation_score = future_pitch_data.result()
        feedback_text = future_feedback_text.result()

    return{
        "status": status,
        "intonation_score": intonation_score,
        "feedback_text": feedback_text,
        "feedback_image": feedback_image,
    }
    






    
