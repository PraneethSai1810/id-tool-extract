import os
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    String,
    DateTime,
    ForeignKey,
    Integer,
    func,
)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

metadata = MetaData()


groups = Table(
    "groups",
    metadata,
    Column("trip_id", String, primary_key=True),
    Column("status", String, nullable=False, default="open"),
    Column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.now(),
    ),
)


id_entries = Table(
    "id_entries",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "trip_id",
        String,
        ForeignKey("groups.trip_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("title", String, nullable=True),
    Column("document_type", String, nullable=True),
    Column("id_number", String, nullable=True),
    Column("full_name", String, nullable=True),
    Column("given_name", String, nullable=True),
    Column("surname", String, nullable=True),
    Column("dob", String, nullable=True),
    Column("gender", String, nullable=True),
    Column("issue_date", String, nullable=True),
    Column("expiry_date", String, nullable=True),
    Column(
        "scanned_at",
        DateTime(timezone=True),
        server_default=func.now(),
    ),
)


def create_tables():
    metadata.create_all(engine)