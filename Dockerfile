FROM python:3.11-slim

WORKDIR /workspace

RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]