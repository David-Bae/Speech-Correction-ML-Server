# 발음 교정 피드백 API

이 API는 사용자의 억양(intonation)을 분석하여 잘못된 억양을 교정하는 피드백을 반환합니다.

## API 정보

- **URL**: `/give-intonation-feedback`
- **Method**: `POST`

## Request
```http
POST /give-intonation-feedback
Content-Type: multipart/form-data
{
    "audio": <audio_file>,
    "text": "2_3"
}
```
### Form Data

- **audio** (필수, `File`):
  - 사용자 발화 음성 파일 (지원 포맷: 3gp, wav)
  
- **text** (필수, `String`):
  - 사용자가 읽은 한글 문장 번호. 
  - 예시: "2_3"은 의문문의 세 번째 문장을 의미.

## Multipart Response

이 API는 사용자의 억양 피드백을 Multipart 형식으로 반환합니다.

### Response Format

- **Content-Type**: `multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW`

### Response Body

Response Body는 여러 파트로 구성되며, 각 파트는 다음과 같은 정보를 포함합니다:

- **status** (`text/plain`):
  - 발음 상태를 나타내는 정수 값.
  - 예시: `1` (정확한 억양/피드백 없음), `2` (틀린 억양/피드백 있음).

- **feedback_count** (`text/plain`):
  - 생성된 피드백의 개수.

- **word_indexes** (`text/plain`):
  - 틀린 단어의 인덱스를 콤마로 구분한 문자열.

- **intonation_feedbacks** (`text/plain`):
  - 발음 교정 피드백 텍스트를 ','로 구분한 문자열.

- **intonation_score** (`text/plain`):
  - 사용자 발음을 평가한 점수. (float)

- **feedback_image** (`image/png`):
  - 사용자의 억양과 표준 억양을 비교하는 그래프 이미지.
  - 이미지가 없을 경우 `"null"` 텍스트로 대체됨.
### 422 Unprocessable Entity
- 음성 파일의 목소리가 없거나 매우 작을 때.
    ```json
    {
        "detail": "목소리를 인식하지 못했습니다."
    }
    ```