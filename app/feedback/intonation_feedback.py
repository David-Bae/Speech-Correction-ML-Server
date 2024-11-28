from app.util import FeedbackStatus
from app.feedback.intonation.pitch import get_time_and_pitch
from tempfile import TemporaryDirectory
from app.feedback.intonation.intonation_graph_generator import plot_intonation_graph

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_intonation_feedback(audio_data):
    
    status = FeedbackStatus.PRONUNCIATION_SUCCESS
    intonation_feedback = ""
    intonation_score = 0.0
    feedback_image = None
    
    #! <억양 피드백 생성>
    #! Pitch 데이터 추출
    time_resampled, pitch_resampled = get_time_and_pitch(audio_data)

    with TemporaryDirectory() as temp_dir:
        #! 그래프 이미지 생성
        plot_intonation_graph(time_resampled, pitch_resampled, temp_dir)

        #! 이미지 파일 읽기
        with open(f"{temp_dir}/test.jpg", "rb") as f:
            image_data = f.read()

    intonation_feedback = "억양 피드백 텍스트"
    intonation_score = 77.3
    feedback_image = "feedback_image_path"

    if feedback_image is None:
        logger.error("1. get_intonation_feedback: Feedback image is None")
    else:
        logger.info("1. get_intonation_feedback: Feedback image is not None")

    
    return{
        "status": status,
        "intonation_feedback": intonation_feedback,
        "feedback_image": feedback_image,
        "intonation_score": intonation_score,
    }