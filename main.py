# main.py
import logging
import asyncio  # Add asyncio for scheduling tasks
from fastapi import FastAPI, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import uvicorn

from database import SessionLocal, engine, Base
from models.user import User, Code

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Statistify API"
)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    "https://www.brandoo.cz",
    "https://app.brandoo.cz",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware for CORS exceptions
class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/contacts/new-contact") or request.url.path.startswith("/api/statistics/value"):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
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

router = APIRouter()

@router.get("/")
def read_root():
    return "Success! Go to /docs for Swagger API"

app.include_router(router)
app.include_router(user_router, prefix="/api/user", tags=["User"])
app.include_router(statistics_router, prefix="/api/statistics", tags=["Statistics"])
app.include_router(contacts_router, prefix="/api/contacts", tags=["Contacts"])


async def delete_expired_codes():
    """Background task to delete expired codes."""
    while True:
        try:
            db: Session = SessionLocal()
            expiration_time = datetime.now(tz=timezone.utc) - timedelta(minutes=5)
            expired_codes = db.query(Code).filter(Code.created_at < expiration_time).all()
            for code in expired_codes:
                db.delete(code)
            db.commit()
            db.close()
            logger.info(f"Deleted {len(expired_codes)} expired codes.")
        except Exception as e:
            logger.error(f"Error deleting expired codes: {e}")
        await asyncio.sleep(300)  # Sleep for 5 minutes


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(delete_expired_codes())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
