# 한글 발음 법칙 적용 API

이 API는 입력된 한글 텍스트에 발음 법칙을 적용한 한글 텍스트를 반환합니다.

## API 정보

- **URL**: `/get-pronounced-text`
- **Method**: `POST`

## Request
```http
POST /get-pronounced-text
Content-Type: application/json
{
    "hangul": "저기 계신 저 분이 박 법학사이시고"
}
```

### Request Body

- **hangul** (필수, `String`):
  - 발음 변환을 원하는 한글 문장 또는 단어.

## Response
```json
{
    "pronounced_text": "저기 계신 저 부니 박 버팍싸이시고"
}
```

### 422 Unprocessable Entity
- 입력된 텍스트가 유효한 한글 문장이 아닐 때.
    ```json
    {
        "detail": "유효한 한글 문장이 아닙니다."
    }
    ```

### Response 항목 설명

- **pronounced_text** (`String`):
  - 발음 법칙이 적용된 한글 텍스트.