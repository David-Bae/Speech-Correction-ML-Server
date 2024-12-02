from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def index():
    return {"message": "This is the index page of the ML Server."}