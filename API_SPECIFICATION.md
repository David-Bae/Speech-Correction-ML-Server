# 발음 교정 피드백 API

이 API는 업로드된 음성 파일과 한글 텍스트를 분석하여 발음 교정 피드백을 제공합니다. 사용자는 음성 파일과 해당 음성에 맞는 텍스트를 입력하여 발음 정확도를 평가받고, 발음 교정 피드백을 얻을 수 있습니다.

## API 정보

- **URL**: `/get-feedback`
- **Method**: `POST`

## Request

### Form Data

- **audio** (필수, `File`):
  - 사용자 발화 음성 파일 업로드.
  
- **text** (필수, `String`):
  - 사용자가 읽은 한글 문장, 단어 텍스트.

### Example Request

```http
POST /get-feedback
Content-Type: multipart/form-data
{
    "audio": <audio_file>,
    "text": "안녕하세요"
}
```

## Response
### Response 항목 설명

- **oral_structure_image** (`String`):
  - 구강 구조 피드백을 시각적으로 제공하는 이미지 파일 경로.

- **frequency_analysis_image** (`String`):
  - 주파수 영역 분석 결과를 시각적으로 제공하는 이미지 파일 경로.

- **feedback_data** (`Object`):
  - 발음 피드백에 관한 상세 정보를 담은 객체입니다.

#### feedback_data 항목

- **incorrect_word_indices** (`List[int]`):
  - 음성에서 발음이 잘못된 단어의 인덱스를 제공합니다. 예: `[0, 3]`은 첫 번째와 네 번째 단어에서 오류가 발생했음을 나타냅니다.

- **accuracy** (`float`):
  - 발음 정확도를 퍼센티지(%)로 표현한 값입니다. 100점 만점 기준으로 계산되며, 예를 들어 `93.2`는 93.2%의 발음 정확도를 의미합니다.

- **speech_feedback** (`String`):
  - 사용자의 발음을 개선하기 위한 조언이나 피드백이 포함됩니다. 예: `'ㅏ'를 발음할 때, 입모양을 더 크게 하세요.`

- **frequency_feedback** (`String`):
  - 주파수 영역을 기반으로 한 발음 개선 피드백입니다. 예: `질문하는 상황에서는 마지막 부분을 올리세요.`



### Example Response

```json
{
    "oral_structure_image": "/workspace/app/images/oral_feedback.png",
    "frequency_analysis_image": "/workspace/app/images/frequency_feedback.png",
    "feedback_data": {
        "incorrect_word_indices": [0, 3],
        "accuracy": 93.2,
        "speech_feedback": "'ㅏ'를 발음할 때, 입모양을 더 크게 하세요.",
        "frequency_feedback": "질문하는 상황에서는 마지막 부분을 올리세요."
    }
}
```
