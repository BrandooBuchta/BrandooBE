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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("test")

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

scheduler = BackgroundScheduler()
scheduler.start()

router = APIRouter()

# Move the root route here to ensure it is registered
@router.get("/")
def read_root():
    return "Success! Go to /docs for Swagger API"

app.include_router(router)
app.include_router(user_router, prefix="/api/user", tags=["User"])
app.include_router(statistics_router, prefix="/api/statistics", tags=["Statistics"])
app.include_router(contacts_router, prefix="/api/contacts", tags=["Contacts"])

def delete_expired_codes_and_users():
    db: Session = SessionLocal()
    try:
        now = datetime.now(tz=timezone.utc)
        
        expired_codes = db.query(Code).filter(Code.created_at < (now - timedelta(minutes=5))).all()
        for code in expired_codes:
            db.delete(code)
        
        old_unverified_users = db.query(User).filter(User.is_verified == False, User.created_at < (now - timedelta(days=7))).all()
        for user in old_unverified_users:
            db.delete(user)
        
        db.commit()
    finally:
        db.close()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

if __name__ == "__main__":
#    uvicorn.run(app, host="0.0.0.0", port=8000)
    uvicorn.run(app)
