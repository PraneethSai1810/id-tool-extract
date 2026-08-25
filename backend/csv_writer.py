import csv
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

FIELDNAMES = [
    "trip_id", "title", "document_type", "id_number",
    "full_name", "given_name", "surname",
    "dob", "gender", "issue_date", "expiry_date", "scanned_at"
]


def _csv_path_for_trip(trip_id: str) -> str:
    return os.path.join(DATA_DIR, f"{trip_id}.csv")


def append_row(entry: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    path = _csv_path_for_trip(entry["trip_id"])
    file_exists = os.path.isfile(path)

    with open(path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "trip_id": entry.get("trip_id"),
            "title": entry.get("title"),
            "document_type": entry.get("document_type"),
            "id_number": entry.get("id_number"),
            "full_name": entry.get("full_name"),
            "given_name": entry.get("given_name"),
            "surname": entry.get("surname"),
            "dob": entry.get("dob"),
            "gender": entry.get("gender"),
            "issue_date": entry.get("issue_date"),
            "expiry_date": entry.get("expiry_date"),
            "scanned_at": datetime.now().isoformat(timespec="seconds"),
        })


def get_csv_path(trip_id: str) -> str | None:
    path = _csv_path_for_trip(trip_id)
    return path if os.path.isfile(path) else None