import logging
from fastapi import FastAPI, Request, APIRouter, File, UploadFile, HTTPException, Query, status
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware

from starlette.responses import JSONResponse
from bs4 import BeautifulSoup
import httpx
from database import SessionLocal, engine, Base
import uvicorn
import paramiko
import os
import uuid
from dotenv import load_dotenv
from tenacity import retry, wait_fixed, stop_after_attempt
import re

from database import SessionLocal, engine, Base
from models.user import User, Code
from routers.user import router as user_router
from routers.statistics import router as statistics_router
from routers.form import router as form_router
from routers.event import router as event_router
from routers.label import router as label_router
from routers.cms import router as content_router
from crud.user import delete_unverified_users, delete_expired_code, refresh_all_auth_tokens

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,  # Allow extra connections if needed
    pool_timeout=30,  # Adjust connection timeout
    pool_recycle=3600,  # Recycle connections after 1 hour
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Brandoo API"
)

# Origins for private endpoints
allowed_origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8000",
    "https://www.brandoo.cz",
    "https://app.brandoo.cz",
    "https://api.brandoo.cz",
    "https://dev.api.brandoo.cz",
    "https://dev.app.brandoo.cz",
]

# Public endpoints regex patterns
public_endpoints_regex = [
    re.compile(r"^/api/(forms/(create-response|property/options)|statistics/value|contents)/[a-fA-F0-9-]+$")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.middleware("http")
async def check_origin_middleware(request: Request, call_next):
    request_origin = request.headers.get("origin")
    request_path = str(request.url.path)

    if request_origin in allowed_origins:
        return await call_next(request)

    if any(regex.match(request_path) for regex in public_endpoints_regex):
        return await call_next(request)

    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": "Forbidden: Origin not allowed"},
    )

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"},
    )

# Retry logic for database operations
@retry(wait=wait_fixed(10), stop=stop_after_attempt(3))
def refresh_hook():
    db = SessionLocal()
    try:
        delete_unverified_users(db)
        delete_expired_code(db)
        refresh_all_auth_tokens(db)
    except Exception as e:
        logger.error(f"Error in refresh_hook: {e}")
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
app.include_router(form_router, prefix="/api/forms", tags=["Forms"])
app.include_router(event_router, prefix="/api/event", tags=["Events"])
app.include_router(label_router, prefix="/api/label", tags=["Labels"])
app.include_router(content_router, prefix="/api/contents", tags=["Contents"])

load_dotenv()

# SFTP Configuration
SFTP_HOST = os.getenv("SFTP_HOST")
SFTP_PORT = int(os.getenv("SFTP_PORT"))
SFTP_USERNAME = os.getenv("SFTP_USERNAME")
SFTP_PASSWORD = os.getenv("SFTP_PASSWORD")
SFTP_UPLOAD_DIR = os.getenv("SFTP_UPLOAD_DIR")
PUBLIC_URL_BASE = os.getenv("PUBLIC_URL_BASE")

@app.post("/api/upload-file")
async def upload_file(file: UploadFile = File(...), user_id: str = Query(None)):
    try:
        file_location = f"/tmp/{file.filename}"
        with open(file_location, "wb") as buffer:
            buffer.write(await file.read())

        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        remote_file_path = f"{SFTP_UPLOAD_DIR}/{file_id}{file_extension}"

        sftp.put(file_location, remote_file_path)
        sftp.close()
        transport.close()

        public_url = f"{PUBLIC_URL_BASE}/{file_id}{file_extension}"

        return public_url

    except paramiko.SSHException as ssh_error:
        raise HTTPException(status_code=500, detail=f"SSH error: {str(ssh_error)}")
    except paramiko.SFTPError as sftp_error:
        raise HTTPException(status_code=500, detail=f"SFTP error: {str(sftp_error)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.delete("/api/delete-file/{file_name}")
async def delete_file(file_name: str, user_id: str = Query(None)):
    try:
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)

        sftp = paramiko.SFTPClient.from_transport(transport)
        remote_file_path = f"{SFTP_UPLOAD_DIR}/{file_name}"

        sftp.remove(remote_file_path)
        sftp.close()
        transport.close()

        return {"detail": f"File {file_name} deleted successfully."}

    except paramiko.SSHException as ssh_error:
        raise HTTPException(status_code=500, detail=f"SSH error: {str(ssh_error)}")
    except paramiko.SFTPError as sftp_error:
        raise HTTPException(status_code=500, detail=f"SFTP error: {str(sftp_error)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File deletion failed: {str(e)}")

# Endpoint to fetch the title of a webpage
@app.get("/api/get-title")
async def get_title(url: str):
    """
    Endpoint to fetch the meta title from a URL
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Failed to fetch the URL: {url}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find("title")
        
        if title:
            return {"title": title.text.strip()}
        else:
            raise HTTPException(status_code=404, detail="No title found for this URL")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
