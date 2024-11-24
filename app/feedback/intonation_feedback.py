from app.util import FeedbackStatus
from PIL import Image

def get_intonation_feedback(audio_data):
    
    status = FeedbackStatus.PRONUNCIATION_SUCCESS
    feedback_count = 0
    word_indexes = []
    intonation_feedbacks = []
    intonation_score = 0.0
    feedback_image = None
    
    #! 억양 피드백 생성
    feedback_count = 1
    word_indexes = [0]
    intonation_feedbacks = ["억양 피드백 텍스트"]
    intonation_score = 77.3
    feedback_image = Image.open("/workspace/app/image/pitch.png")
    
    return{
        "status": status,
        "feedback_count": feedback_count,
        "word_indexes": word_indexes,
        "intonation_feedbacks": intonation_feedbacks,
        "feedback_image": feedback_image,
        "intonation_score": intonation_score,
    }