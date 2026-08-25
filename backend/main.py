import uuid
import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
import os

from gemini_client import extract_id_details
from csv_writer import append_row, get_csv_path
from models import GroupStartResponse, GroupFinishRequest, GroupFinishResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Allowed file types
ALLOWED_TYPES = {
    "image/jpeg",      # .jpg, .jpeg
    "image/png",       # .png
    "image/webp",      # .webp
    "image/heic",      # .heic
    "image/heif",      # some iPhones
    "application/pdf", # .pdf
}

# 10 MB limit
MAX_FILE_SIZE = 10 * 1024 * 1024

open_groups = set()


@app.post("/group/start", response_model=GroupStartResponse)
def start_group():
    trip_id = str(uuid.uuid4())
    open_groups.add(trip_id)
    return GroupStartResponse(trip_id=trip_id)


@app.post("/group/finish", response_model=GroupFinishResponse)
def finish_group(payload: GroupFinishRequest):
    if payload.trip_id not in open_groups:
        raise HTTPException(status_code=404, detail="Group not found or already closed")

    open_groups.remove(payload.trip_id)
    return GroupFinishResponse(trip_id=payload.trip_id, status="closed")


@app.post("/extract")
async def extract(file: UploadFile = File(...), trip_id: str = Form(...)):
    if trip_id not in open_groups:
        raise HTTPException(status_code=400, detail="Invalid or closed trip_id — start a group first")

    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Allowed: JPG, JPEG, PNG, WEBP, HEIC, PDF."
        )

    file_bytes = await file.read()

    # Validate file size
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 10 MB."
        )

    mime_type = file.content_type

    try:
        extracted = extract_id_details(file_bytes, mime_type)
    except ValueError:
        logger.exception("Extraction failed")
        raise HTTPException(
            status_code=502,
            detail="Couldn't extract details. Please upload a clearer image."
        )
    except Exception:
        logger.exception("Unexpected server error")
        raise HTTPException(
            status_code=500,
            detail="Internal server error."
        )

    extracted["trip_id"] = trip_id
    append_row(extracted)
    return extracted


@app.get("/download-csv/{trip_id}")
def download_csv(trip_id: str):
    path = get_csv_path(trip_id)
    if not path:
        raise HTTPException(status_code=404, detail="No data found for this group")

    return FileResponse(
        path=path,
        media_type="text/csv",
        filename=f"id_scan_{trip_id[:8]}.csv",
        background=BackgroundTask(os.remove, path),
    )


@app.get("/")
def health_check():
    return {"status": "ok"}