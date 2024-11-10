# 발음 교정 피드백 API

이 API는 사용자의 발음(pronunciation)을 분석하여 틀린 부분을 교정하는 피드백을 반환합니다.

## API 정보

- **URL**: `/get-pronunciation-feedback`
- **Method**: `POST`

## Request
```http
POST /get-pronunciation-feedback
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
    "status": 1,
    "transcription": "나는 행복하게 끝나는 용화가 좋다.",
    "feedback_count": 1,
    "word_index": [3],
    "pronunciation_feedbacks": ["입술을 동그랗게 모으는 대신 ..."],
    "feedback_image_names": ["ㅛ_ㅕ.jpg"],
    "wrong_spellings": ["ㅕ"],
    "pronunciation_score": 97.56
}
```
### 422 Unprocessable Entity
- 음성 파일의 목소리가 없거나 매우 작을 때.
    ```json
    {
        "detail": "목소리를 인식하지 못했습니다."
    }
    ```
### 423 Unprocessable Entity
- 주어진 문장과 다른 문장을 말했을 때.
    ```json
    {
        "detail": "다른 문장을 발음했습니다."
    }
    ```
### 501 Not Implemented
- 아직 피드백 알고리즘이 구현되지 않은 경우.
    ```json
    {
        "detail": "아직 구현되지 않은 기능입니다."
    }
    ```

### Response 항목 설명
- **status** (`int`):
  - 1 : 정확한 발음. 피드백 & 입모양 사진 없음.
  - 2 : 발음에 틀린 부분 있음. 피드백 & 입모양 사진 있음.

- **transcription** (`String`):
  - 사용자의 발화를 발음 그대로 전사한 한글 텍스트.

- **feedback_count** (`int`):
  - 생성된 피드백 개수 - word_index, pronunciation_feedbacks, feedback_image_names, wrong_spellings의 길이와 같음.

- **word_index** (`list`):
  - 몇 번째 단어에서 틀렸는지 나타내는 인덱스를 포함하는 리스트.

- **pronunciation_feedbacks** (`list`):
  - 발음 교정 피드백 텍스트를 포함하는 리스트.

- **feedback_image_names** (`list`):
  - 발음 교정을 위한 입모양 사진의 이름을 포함하는 리스트.

- **wrong_spellings** (`list`):
  - 틀린 철자들 리스트.

- **pronunciation_score** (`float`):
  - 사용자 발음을 평가한 점수.