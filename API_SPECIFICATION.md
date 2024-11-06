# 발화 교정 피드백 API

이 API는 사용자의 발화와 문장을 분석하여 발음(pronunciation)과 억양(intonation)에 대한 피드백을 반환합니다.

## API 정보

- **URL**: `/get-feedback`
- **Method**: `POST`

## Request
```http
POST /get-feedback
Content-Type: multipart/form-data
{
    "audio": <audio_file>,
    "text": "안녕하세요"
}
```
### Form Data

- **audio** (필수, `File`):
  - 사용자 발화 음성 파일 (지원 포맷: 3gp, wav)
  
- **text** (필수, `String`):
  - 사용자가 읽은 한글 문장, 단어 텍스트.

## Response
```json
{
    "transcription": "나는 행보카게 끝나는 뇽화가 조따.",
    "pronunciation_feedback": "'ㅏ'를 발음할 때, 입모양을 더 크게 하세요.",
    "pronunciation_score": 93.2,
    "intonation_feedback": "질문하는 상황에서는 마지막 부분을 올리세요.",
    "pronunciation_feedback_image": "image_base64",
    "intonation_feedback_image": "image_base64"
}
```
### 422 Unprocessable Entity
- 음성 파일의 목소리가 없거나 매우 작을 때.
    ```json
    {
        "detail": "목소리를 인식하지 못했습니다."
    }
    ```
- 주어진 문장과 다른 문장을 말했을 때.
    ```json
    {
        "detail": "다른 문장을 발음했습니다."
    }
    ```

### Response 항목 설명
- **transcription** (`String`):
  - 사용자의 발화를 발음 그대로 전사한 한글 텍스트.

- **pronunciation_feedback** (`String`):
  - 발음에 대한 피드백.

- **pronunciation_score** (`float`):
  - 발음 정확도.

- **intonation_feedback** (`String`):
  - 억양에 대한 피드백.
 
- **pronunciation_feedback_image** (`Base64`):
  - 발음 피드백을 위한 구강구조 이미지.

- **intonation_feedback_image** (`Base64`):
  - 억양 분석을 위해 주파수 영역으로 변환한 이미지
