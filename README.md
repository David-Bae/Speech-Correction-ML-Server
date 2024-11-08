# 올발음 (Speech Correction) ML Inference Server

### Overview
This repository hosts the inference server for the "올발음" project, a speech visualization and pronunciation correction app designed to assist hearing-impaired individuals in improving their pronunciation. The inference server enables real-time evaluation of user speech, providing visual feedback by comparing the user's pronunciation to ideal speech patterns using AI-based models.

### Tech Stack
- Framework: FastAPI for API handling

### Docker Image

- Image Name: `suhwan99/vocalist-ml-server`
```bash
docker run -d -p 8000:8000 --name ml-server -v ${PWD}:/workspace --env-file .env suhwan99/vocalist-ml-server:latest
```
