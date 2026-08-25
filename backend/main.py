import uuid
import logging
import os

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from sqlalchemy import select, update, insert, delete

from gemini_client import extract_id_details
from csv_writer import create_csv_file
from models import GroupStartResponse, GroupFinishRequest, GroupFinishResponse
from database import engine, groups, id_entries, create_tables


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://id-extract-tool.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


ALLOWED_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
    "application/pdf",
}


MAX_FILE_SIZE = 10 * 1024 * 1024


@app.on_event("startup")
def startup():
    create_tables()
    logger.info("Database tables ready")


@app.post("/group/start", response_model=GroupStartResponse)
def start_group():
    trip_id = str(uuid.uuid4())

    with engine.begin() as connection:
        connection.execute(
            insert(groups).values(
                trip_id=trip_id,
                status="open",
            )
        )

    return GroupStartResponse(trip_id=trip_id)


@app.post("/group/finish", response_model=GroupFinishResponse)
def finish_group(payload: GroupFinishRequest):
    trip_id = str(payload.trip_id)

    with engine.begin() as connection:
        result = connection.execute(
            select(groups.c.trip_id, groups.c.status)
            .where(groups.c.trip_id == trip_id)
        ).first()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Group not found"
            )

        if result.status == "closed":
            raise HTTPException(
                status_code=400,
                detail="Group is already finished"
            )

        connection.execute(
            update(groups)
            .where(groups.c.trip_id == trip_id)
            .values(status="closed")
        )

    return GroupFinishResponse(
        trip_id=trip_id,
        status="closed",
    )


@app.post("/extract")
async def extract(
    file: UploadFile = File(...),
    trip_id: str = Form(...),
):
    # Check group
    with engine.connect() as connection:
        group = connection.execute(
            select(groups.c.status)
            .where(groups.c.trip_id == trip_id)
        ).first()

    if not group:
        raise HTTPException(
            status_code=400,
            detail="Invalid trip_id — start a group first"
        )

    if group.status != "open":
        raise HTTPException(
            status_code=400,
            detail="This group is already finished"
        )

    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Allowed: JPG, JPEG, PNG, WEBP, HEIC, PDF."
        )

    file_bytes = await file.read()

    # Validate size
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 10 MB."
        )

    try:
        extracted = extract_id_details(
            file_bytes,
            file.content_type,
        )

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

    # Add trip ID
    extracted["trip_id"] = trip_id

    # Save extracted data to Neon
    with engine.begin() as connection:
        connection.execute(
            insert(id_entries).values(
                trip_id=trip_id,
                title=extracted.get("title"),
                document_type=extracted.get("document_type"),
                id_number=extracted.get("id_number"),
                full_name=extracted.get("full_name"),
                given_name=extracted.get("given_name"),
                surname=extracted.get("surname"),
                dob=extracted.get("dob"),
                gender=extracted.get("gender"),
                issue_date=extracted.get("issue_date"),
                expiry_date=extracted.get("expiry_date"),
            )
        )

    return extracted


@app.get("/download-csv/{trip_id}")
def download_csv(trip_id: str):

    # Check group exists and is finished
    with engine.connect() as connection:
        group = connection.execute(
            select(groups.c.status)
            .where(groups.c.trip_id == trip_id)
        ).first()

    if not group:
        raise HTTPException(
            status_code=404,
            detail="Group not found"
        )

    if group.status != "closed":
        raise HTTPException(
            status_code=400,
            detail="Finish the group before downloading CSV"
        )

    # Get entries
    with engine.connect() as connection:
        rows = connection.execute(
            select(id_entries)
            .where(id_entries.c.trip_id == trip_id)
            .order_by(id_entries.c.id)
        ).mappings().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="No scanned data found for this group"
        )

    # Create temporary CSV
    csv_path = create_csv_file(trip_id, rows)

    return FileResponse(
        csv_path,
        media_type="text/csv",
        filename=f"id_scan_{trip_id[:8]}.csv",
        background=BackgroundTask(
            cleanup_after_download,
            trip_id,
            csv_path,
        ),
    )


def cleanup_after_download(trip_id: str, csv_path: str):
    try:
        # Delete temporary CSV file
        if os.path.exists(csv_path):
            os.remove(csv_path)

        # Delete sensitive data from database
        with engine.begin() as connection:
            connection.execute(
                delete(id_entries)
                .where(id_entries.c.trip_id == trip_id)
            )

            connection.execute(
                delete(groups)
                .where(groups.c.trip_id == trip_id)
            )

        logger.info(
            f"Deleted group and ID data for {trip_id}"
        )

    except Exception:
        logger.exception(
            f"Cleanup failed for group {trip_id}"
        )


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "database": "connected"
    }