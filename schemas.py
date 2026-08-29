"""Pydantic schemas — validation for API endpoints (Concept 1)."""
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional


class ApplicationCreate(BaseModel):
    university: str = Field(..., min_length=1)
    scholarship_name: str = Field(..., min_length=1)
    status: str = Field(default="Pending")  # Applied / Rejected / Pending / Accepted
    applied_date: Optional[date] = None
    deadline: Optional[date] = None
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    university: Optional[str] = None
    scholarship_name: Optional[str] = None
    status: Optional[str] = None
    applied_date: Optional[date] = None
    deadline: Optional[date] = None
    notes: Optional[str] = None


class ApplicationOut(BaseModel):
    id: int
    university: str
    scholarship_name: str
    status: str
    applied_date: Optional[date]
    deadline: Optional[date]
    notes: Optional[str]
    eligibility: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExtractRequest(BaseModel):
    application_id: int
    raw_text: str = Field(..., min_length=10, description="Pasted scholarship description text")
