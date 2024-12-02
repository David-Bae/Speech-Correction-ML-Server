from fastapi import APIRouter
from .ping import router as ping_router
from .pronunciation import router as pronunciation_router
from .intonation import router as intonation_router

router = APIRouter()
router.include_router(pronunciation_router)
router.include_router(intonation_router)
router.include_router(ping_router)