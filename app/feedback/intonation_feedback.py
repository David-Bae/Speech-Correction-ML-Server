

def get_intonation_feedback(audio_data):
    
    intonation_feedback = "질문하는 상황에서는 마지막 부분을 올리세요."
    
    intonation_score = 77.3
    
    frequency_analysis_image_path = "/workspace/app/images/frequency_feedback.png"
    
    feedback = {
        "intonation_feedback": intonation_feedback,
        "image_path": frequency_analysis_image_path
    }
    
    return feedback