from pydantic import BaseModel
from typing import Optional
from enum import Enum


class Gender(str, Enum):
    male = "Male"
    female = "Female"


class ExtractedID(BaseModel):
    document_type: Optional[str] = None
    full_name: Optional[str] = None
    given_name: Optional[str] = None
    surname: Optional[str] = None
    id_number: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[Gender] = None
    title: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    trip_id: str


class GroupStartResponse(BaseModel):
    trip_id: str


class GroupFinishRequest(BaseModel):
    trip_id: str


class GroupFinishResponse(BaseModel):
    trip_id: str
    status: str