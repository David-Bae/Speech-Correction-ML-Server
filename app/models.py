from pydantic import BaseModel  # Pydantic에서 BaseModel을 가져옵니다
from typing import List

class FeedbackStatus:
    PRONUNCIATION_SUCCESS = 1   # 틀린 부분 없음
    FEEDBACK_PROVIDED = 2       # 피드백 생성
    NO_SPEECH = 3               # 말이 없음
    WRONG_SENTENCE = 4          # 다른 문장 발음
    NOT_IMPLEMENTED = 5         # 아직 구현 안됨
    WRONG_WORD_COUNT = 6        # 단어 개수 다름


class PronunciationFeedbackResponse(BaseModel):
    """
    사용자의 발음(pronunciation)을 분석하여 틀린 부분을 교정하는 피드백을 반환하는 API의 응답 모델
        * status : FeedbackStatus (int)
            Feedback 수행 상태를 나타내는 변수. app/util.py의 FeedbackStatus 클래스를 참고.
        
        * transcription : str
            오디오 파일을 들리는대로 전사한 한글 텍스트.
        
        * feedback_count : int
            생성된 피드백 개수. 'word_index', 'pronunciation_feedbacks', 'feedback_image_names', 'wrong_spellings' 리스트의 개수와 동일.
        
        * word_index : list
            몇번쨰 단어에서 틀렸는지 나타내는 인덱스를 포함하는 리스트.
        
        * pronunciation_feedbacks : list
            발음 교정 피드백 텍스트를 포함하는 리스트.
        
        * feedback_image_names : list
            발음 교정을 위한 입모양 사진의 이름을 포함하는 리스트. 사진들은 S3에 저장됨.
        
        * wrong_spellings : list
            틀린 철자들 리스트.
        
        * pronunciation_score : float
            사용자 발음을 평가한 점수.
    """
    status: int
    transcription: str
    feedback_count: int
    word_indexes: List[int]
    pronunciation_feedbacks: List[str]
    feedback_image_names: List[str]
    wrong_spellings: List[str]
    pronunciation_score: float



class HangulRequest(BaseModel):
    """
    한글 텍스트를 받아 발음 변환을 수행하는 API의 요청 모델
    """
    hangul: str