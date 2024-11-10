from pydantic import BaseModel  # Pydantic에서 BaseModel을 가져옵니다

class HangulRequest(BaseModel):
    hangul: str