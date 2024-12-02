from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routers import router

#* Debugging
from datetime import datetime, timedelta, timezone
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    KST = timezone(timedelta(hours=9))
    start_time = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

    logger.info("="*50)
    logger.info("||      ML Server has started successfully      ||")
    logger.info(f"||      Started at: {start_time}         ||")
    logger.info("="*50)

    yield
    
    logger.info("Service is stopping...")


app = FastAPI(lifespan=lifespan)
app.include_router(router)



