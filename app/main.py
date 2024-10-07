from fastapi import FastAPI
from app.models import get_prediction

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "DeepLearning Inference API"}

@app.get("/predict/")
async def predict():
    result = get_prediction()
    return {"prediction": result}
