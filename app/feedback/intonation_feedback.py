from app.util import FeedbackStatus
from PIL import Image

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    if feedback_image is None:
        logger.error("1. get_intonation_feedback: Feedback image is None")
    else:
        logger.info("1. get_intonation_feedback: Feedback image is not None")

    
    return{
        "status": status,
        "feedback_count": feedback_count,
        "word_indexes": word_indexes,
        "intonation_feedbacks": intonation_feedbacks,
        "feedback_image": feedback_image,
        "intonation_score": intonation_score,
    }
    


def plot_intonation_graph(words_time_info, time_resampled, pitch_resampled, sentence_number):
    plt.clf()
    
    # # 축 눈금 제거
    plt.xticks([])
    plt.yticks([])  
    
    plt.plot(time_resampled, pitch_resampled, linewidth=5, color='orange')
    
    for word in words_time_info:
        plt.text((word['start'] + word['end']) / 2, min(pitch_resampled) * 0.9, word['text'],
            horizontalalignment='center', verticalalignment='top', fontsize=12, color='red')
    
    
    save_file_path = f"/workspace/intonation_images/{sentence_number}.png"
    plt.savefig(save_file_path, bbox_inches='tight', pad_inches=0)