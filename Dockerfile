FROM mmcauliffe/montreal-forced-aligner:latest  

WORKDIR /workspace

USER root

# 필요한 패키지 설치
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y ffmpeg git && \
    apt-get clean

# Python 및 FastAPI 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# COPY environment.yml .
# RUN conda env update --name base --file environment.yml


# 한국어 음향 모델 및 발음 사전 다운로드
RUN mfa model download acoustic korean_mfa && \
    mfa model download dictionary korean_mfa

# FastAPI 서버 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]