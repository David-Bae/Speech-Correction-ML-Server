from app.util import FeedbackStatus
from app.feedback.intonation.pitch import get_time_and_pitch
from app.feedback.intonation.intonation_graph_generator import plot_intonation_graph

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_intonation_feedback(audio_data):
    
    status = FeedbackStatus.PRONUNCIATION_SUCCESS
    feedback_text = ""
    intonation_score = 0.0
    feedback_image = None
    
    
    #* 사용자 음성에서 Pitch 데이터 추출
    time_resampled, pitch_resampled = get_time_and_pitch(audio_data)

    #! <세 기능 병렬처리 가능>
    #* 음성 높낮이 그래프 이미지 생성
    feedback_image = plot_intonation_graph(time_resampled, pitch_resampled)

    #* 억양 피드백 텍스트 생성
    feedback_text = "억양 피드백 텍스트"

    #* 억양 점수 생성
    intonation_score = 77.3

    
    return{
        "status": status,
        "intonation_score": intonation_score,
        "feedback_text": feedback_text,
        "feedback_image": feedback_image,
    }