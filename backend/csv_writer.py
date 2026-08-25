import csv
import os
import tempfile


FIELDNAMES = [
    "trip_id",
    "title",
    "document_type",
    "id_number",
    "full_name",
    "given_name",
    "surname",
    "dob",
    "gender",
    "issue_date",
    "expiry_date",
    "scanned_at",
]


def create_csv_file(trip_id: str, rows) -> str:

    temp_dir = tempfile.gettempdir()

    path = os.path.join(
        temp_dir,
        f"id_scan_{trip_id}.csv"
    )

    with open(
        path,
        mode="w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=FIELDNAMES,
        )

        writer.writeheader()

        for row in rows:
            writer.writerow({
                field: row.get(field)
                for field in FIELDNAMES
            })

    return path