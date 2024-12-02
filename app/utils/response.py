import logging
logger = logging.getLogger(__name__)

from io import BytesIO
from fastapi import Response


def get_multipart_form_data(**parts):
    """
    주어진 파트들을 Multipart Form Data로 변환하여 반환.
    
    Parameters:
        **parts: Multipart Form Data로 변환할 파트들. 
                 텍스트 파트는 문자열로, 
                 파일 파트는 (filename, content, content_type) 형식의 튜플로 제공됩니다.
    
    Returns:
        Response: 멀티파트 폼 데이터로 변환된 응답 객체
    """
    #* 고유한 boundary 설정
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"

    #* multipart 응답 바디를 바이너리로 초기화
    multipart_body = b""
    
    #* Multipart파트 추가를 위한 헬퍼 함수 정의    
    def add_text_part(name, content):
        nonlocal multipart_body
        part = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="{name}"\r\n'
            f'Content-Type: text/plain; charset=utf-8\r\n\r\n'
            f'{content}\r\n'
        ).encode('utf-8')
        multipart_body += part

    def add_file_part(name, filename, content: BytesIO, content_type):
        nonlocal multipart_body
        if content is None:  # 이미지 데이터가 없으면 "null"을 텍스트로 추가
            add_text_part(name, "null")
        else:
            part_header = (
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                f'Content-Type: {content_type}\r\n\r\n'
            ).encode('utf-8')
            multipart_body += part_header
            multipart_body += content.getvalue()  # 이미지 바이너리 데이터 추가
            multipart_body += b'\r\n'

    for key, value in parts.items():
        if isinstance(value, tuple) and len(value) == 3:
            #* 파일 파트 추가 (filename, content, content_type)
            filename, content, content_type = value
            add_file_part(key, filename, content, content_type)
        else:
            #* 텍스트 파트 추가
            add_text_part(key, value)

    # 마지막 경계 추가
    multipart_body += f'--{boundary}--\r\n'.encode('utf-8')

    headers = {
        'Content-Type': f'multipart/form-data; boundary={boundary}'
    }
    
    return Response(content=multipart_body, media_type=f'multipart/form-data; boundary={boundary}', headers=headers)
