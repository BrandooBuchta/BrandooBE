import logging
from fastapi import FastAPI, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone, timedelta
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import uvicorn

from database import SessionLocal, engine, Base
from models.user import User, Code

from routers.user import router as user_router
from routers.statistics import router as statistics_router
from routers.contacts import router as contacts_router

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

def delete_expired_codes_and_users():
    db: Session = SessionLocal()
    try:
        now = datetime.now(tz=timezone.utc)  # Get the current time in UTC

        # Find expired codes (older than 5 minutes)
        expired_codes = db.query(Code).filter(Code.created_at < (now - timedelta(minutes=5))).all()
        logger.info(f"Found {len(expired_codes)} expired codes")
        for code in expired_codes:
            logger.info(f"Deleting code created at {code.created_at}")
            db.delete(code)

        # Find unverified users older than 7 days
        old_unverified_users = db.query(User).filter(User.is_verified == False, User.created_at < (now - timedelta(days=7))).all()
        logger.info(f"Found {len(old_unverified_users)} old unverified users")
        for user in old_unverified_users:
            logger.info(f"Deleting user created at {user.created_at}")
            db.delete(user)

        db.commit()
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        db.rollback()
    finally:
        db.close()

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

scheduler = BackgroundScheduler()
scheduler.start()

# Add the job to the scheduler to run every 2 minutes
scheduler.add_job(delete_expired_codes_and_users, 'interval', minutes=2)

router = APIRouter()

# Move the root route here to ensure it is registered
@router.get("/")
def read_root():
    return "Success! Go to /docs for Swagger API"

app.include_router(router)
app.include_router(user_router, prefix="/api/user", tags=["User"])
app.include_router(statistics_router, prefix="/api/statistics", tags=["Statistics"])
app.include_router(contacts_router, prefix="/api/contacts", tags=["Contacts"])

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
