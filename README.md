﻿# 올발음 (Speech Correction) ML Inference Server

### Overview
This repository hosts the inference server for the "올발음" project, a speech visualization and pronunciation correction app designed to assist hearing-impaired individuals in improving their pronunciation. The inference server enables real-time evaluation of user speech, providing visual feedback by comparing the user's pronunciation to ideal speech patterns using AI-based models.

### Tech Stack
- Model: Hugging Face's Wav2Vec 2.0
- Framework: FastAPI for API handling

### Docker Image

This project uses the pre-configured Docker image `suhwan99/huggingface-fastapi`, which includes all necessary dependencies such as Hugging Face libraries, FastAPI, and Python modules.
