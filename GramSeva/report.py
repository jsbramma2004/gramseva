"""
app/models/report.py
Pydantic schemas for request validation and DB serialization.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
from enum import Enum
import re


# ── Enums ──────────────────────────────────────────────────────────────────

class IssueCategory(str, Enum):
    WATER_SUPPLY      = "Water Supply / Pipe Leakage"
    ROADS             = "Roads & Pathways"
    WATER_MANAGEMENT  = "Water Management"
    STREET_LIGHTS     = "Street Lights"
    DRAINAGE          = "Drainage System"
    OTHER             = "Other Issue"


class UrgencyLevel(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


class ReportStatus(str, Enum):
    PENDING    = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED   = "resolved"
    REJECTED   = "rejected"


# ── Request Schemas ────────────────────────────────────────────────────────

class ReportCreate(BaseModel):
    """Validated on form submission (multipart data parsed separately)."""
    name:        str          = Field(..., min_length=2,  max_length=100)
    phone:       str          = Field(..., min_length=10, max_length=15)
    village:     str          = Field(..., min_length=2,  max_length=100)
    district:    str          = Field(..., min_length=2,  max_length=100)
    state:       Optional[str] = Field(None, max_length=100)
    category:    IssueCategory
    description: str          = Field(..., min_length=10, max_length=2000)
    urgency:     UrgencyLevel = UrgencyLevel.MEDIUM
    latitude:    Optional[float] = None
    longitude:   Optional[float] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        digits = re.sub(r"[\s\-\+]", "", v)
        if not digits.isdigit():
            raise ValueError("Phone number must contain only digits")
        if len(digits) < 10:
            raise ValueError("Phone number too short")
        return digits


class StatusUpdate(BaseModel):
    status:  ReportStatus
    remarks: Optional[str] = Field(None, max_length=500)


# ── DB / Response Schemas ──────────────────────────────────────────────────

class ReportInDB(BaseModel):
    ticket_id:    str
    name:         str
    phone:        str
    village:      str
    district:     str
    state:        Optional[str]
    category:     IssueCategory
    description:  str
    urgency:      UrgencyLevel
    status:       ReportStatus        = ReportStatus.PENDING
    image_url:    Optional[str]       = None
    image_public_id: Optional[str]   = None   # Cloudinary public_id for deletion
    latitude:     Optional[float]     = None
    longitude:    Optional[float]     = None
    department:   Optional[str]       = None   # resolved department name
    email_sent:   bool                = False
    created_at:   datetime            = Field(default_factory=datetime.utcnow)
    updated_at:   datetime            = Field(default_factory=datetime.utcnow)


class ReportResponse(BaseModel):
    """Shape returned to the frontend."""
    ticket_id:   str
    name:        str
    village:     str
    district:    str
    category:    str
    urgency:     str
    status:      str
    image_url:   Optional[str]
    department:  Optional[str]
    created_at:  datetime

    class Config:
        from_attributes = True
