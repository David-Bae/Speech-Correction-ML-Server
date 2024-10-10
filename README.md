# 올발음 (Speech Correction) ML Inference Server

### Overview
This repository hosts the inference server for the "올발음" project, a speech visualization and pronunciation correction app designed to assist hearing-impaired individuals in improving their pronunciation. The inference server enables real-time evaluation of user speech, providing visual feedback by comparing the user's pronunciation to ideal speech patterns using AI-based models.

### Tech Stack
- Model: Hugging Face's Wav2Vec 2.0
- Framework: FastAPI for API handling

### Docker Image

`suhwan99/huggingface-fastapi`
- GPU 사용
```bash
docker run -d --gpus all -p 8000:8000 --name fastapi-gpu -v $(pwd):/workspace suhwan99/huggingface-fastapi:latest
```
- CPU 사용
```bash
docker run -d -p 8000:8000 --name fastapi-cpu -v $(pwd):/workspace suhwan99/huggingface-fastapi:latest
```
