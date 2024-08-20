# main.py

import logging
import asyncio
from fastapi import FastAPI, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timezone, timedelta
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from database import SessionLocal
import uvicorn

from database import SessionLocal, engine, Base
from models.user import User, Code

from routers.user import router as user_router
from routers.statistics import router as statistics_router
from routers.form import router as form_router
from crud.user import delete_unverified_users, delete_expired_code, refresh_all_auth_tokens

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Brandoo API"
)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    "https://www.brandoo.cz",
    "https://app.brandoo.cz",
    "https://api.brandoo.cz"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/contacts/new-contact") or request.url.path.startswith("/api/statistics/value"):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT"
            response.headers["Access-Control-Allow-Headers"] = "*"
        return response

app.add_middleware(CustomCORSMiddleware)

# Middleware to log requests and responses
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"},
    )

def refresh_hook():
    db = SessionLocal()
    try:
        delete_unverified_users(db)
        delete_expired_code(db)
        refresh_all_auth_tokens(db)
    finally:
        db.close()

scheduler = BackgroundScheduler()
scheduler.add_job(refresh_hook, trigger=IntervalTrigger(hours=1))
scheduler.start()

router = APIRouter()

@router.get("/")
def read_root():
    return "Success! Go to /docs for Swagger API"

app.include_router(router)
app.include_router(user_router, prefix="/api/user", tags=["User"])
app.include_router(statistics_router, prefix="/api/statistics", tags=["Statistics"])
app.include_router(form_router, prefix="/api/contacts", tags=["Contacts"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
