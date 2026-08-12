"""
app/routers/reports.py
All API endpoints for the GramSeva report system.

Routes:
  POST   /reports/            → Submit new report (+ image upload)
  GET    /reports/            → List reports (with filters & pagination)
  GET    /reports/{ticket_id} → Get single report by ticket
  PATCH  /reports/{ticket_id} → Update status (department/admin use)
  DELETE /reports/{ticket_id} → Delete report + Cloudinary image
  GET    /reports/stats/summary → Dashboard statistics
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime
import asyncio

from app.database import get_db
from app.models.report import (
    IssueCategory, UrgencyLevel, ReportStatus,
    ReportInDB, ReportResponse, StatusUpdate,
)
from app.services.cloudinary_service import upload_report_image, delete_report_image
from app.services.email_service import send_department_alert
from app.utils.ticket import generate_ticket_id

router = APIRouter(prefix="/reports", tags=["Reports"])


# ── Helper: serialize MongoDB doc ─────────────────────────────────────────
def serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id", ""))
    return doc


# ─────────────────────────────────────────────────────────────────────────
# POST /reports/   — Submit a new report
# ─────────────────────────────────────────────────────────────────────────
@router.post("/", status_code=201)
async def create_report(
    name:        str           = Form(...),
    phone:       str           = Form(...),
    village:     str           = Form(...),
    district:    str           = Form(...),
    state:       Optional[str] = Form(None),
    category:    IssueCategory = Form(...),
    description: str           = Form(...),
    urgency:     UrgencyLevel  = Form(UrgencyLevel.MEDIUM),
    latitude:    Optional[float] = Form(None),
    longitude:   Optional[float] = Form(None),
    photo:       Optional[UploadFile] = File(None),
):
    db = get_db()

    # ── Upload image if provided ──────────────────────────────
    image_url = None
    image_public_id = None
    if photo and photo.filename:
        img_data = await upload_report_image(photo)
        image_url       = img_data["url"]
        image_public_id = img_data["public_id"]

    # ── Build DB document ─────────────────────────────────────
    ticket_id = generate_ticket_id()
    report_doc = ReportInDB(
        ticket_id       = ticket_id,
        name            = name,
        phone           = phone,
        village         = village,
        district        = district,
        state           = state,
        category        = category,
        description     = description,
        urgency         = urgency,
        image_url       = image_url,
        image_public_id = image_public_id,
        latitude        = latitude,
        longitude       = longitude,
        department      = _resolve_department(category),
    ).model_dump()

    # ── Insert into MongoDB ───────────────────────────────────
    await db.reports.insert_one(report_doc)

    # ── Send email to department (non-blocking) ───────────────
    asyncio.create_task(send_department_alert(report_doc))

    return JSONResponse(status_code=201, content={
        "success":   True,
        "ticket_id": ticket_id,
        "message":   "Report submitted successfully. Department has been notified.",
        "department": report_doc["department"],
    })


# ─────────────────────────────────────────────────────────────────────────
# GET /reports/    — List all reports (with filters)
# ─────────────────────────────────────────────────────────────────────────
@router.get("/")
async def list_reports(
    category: Optional[str]          = Query(None),
    status:   Optional[ReportStatus] = Query(None),
    district: Optional[str]          = Query(None),
    urgency:  Optional[UrgencyLevel] = Query(None),
    page:     int                    = Query(1, ge=1),
    limit:    int                    = Query(20, ge=1, le=100),
):
    db = get_db()
    query = {}
    if category: query["category"] = category
    if status:   query["status"]   = status
    if district: query["district"] = {"$regex": district, "$options": "i"}
    if urgency:  query["urgency"]  = urgency

    skip  = (page - 1) * limit
    total = await db.reports.count_documents(query)
    cursor = db.reports.find(query).sort("created_at", -1).skip(skip).limit(limit)
    docs   = [serialize(doc) async for doc in cursor]

    return {
        "total": total,
        "page":  page,
        "pages": (total + limit - 1) // limit,
        "data":  docs,
    }


# ─────────────────────────────────────────────────────────────────────────
# GET /reports/stats/summary  — Dashboard stats
# ─────────────────────────────────────────────────────────────────────────
@router.get("/stats/summary")
async def get_stats():
    db = get_db()
    total      = await db.reports.count_documents({})
    resolved   = await db.reports.count_documents({"status": "resolved"})
    in_progress= await db.reports.count_documents({"status": "in_progress"})
    pending    = await db.reports.count_documents({"status": "pending"})
    high_urg   = await db.reports.count_documents({"urgency": "high"})

    # Reports per category
    pipeline = [{"$group": {"_id": "$category", "count": {"$sum": 1}}}]
    cat_cursor = db.reports.aggregate(pipeline)
    by_category = {doc["_id"]: doc["count"] async for doc in cat_cursor}

    return {
        "total":       total,
        "resolved":    resolved,
        "in_progress": in_progress,
        "pending":     pending,
        "high_urgency":high_urg,
        "by_category": by_category,
    }


# ─────────────────────────────────────────────────────────────────────────
# GET /reports/{ticket_id}  — Single report detail
# ─────────────────────────────────────────────────────────────────────────
@router.get("/{ticket_id}")
async def get_report(ticket_id: str):
    db  = get_db()
    doc = await db.reports.find_one({"ticket_id": ticket_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")
    return serialize(doc)


# ─────────────────────────────────────────────────────────────────────────
# PATCH /reports/{ticket_id}  — Update status
# ─────────────────────────────────────────────────────────────────────────
@router.patch("/{ticket_id}")
async def update_status(ticket_id: str, payload: StatusUpdate):
    db = get_db()
    result = await db.reports.update_one(
        {"ticket_id": ticket_id},
        {"$set": {
            "status":     payload.status,
            "remarks":    payload.remarks,
            "updated_at": datetime.utcnow(),
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")
    return {"success": True, "ticket_id": ticket_id, "new_status": payload.status}


# ─────────────────────────────────────────────────────────────────────────
# DELETE /reports/{ticket_id}
# ─────────────────────────────────────────────────────────────────────────
@router.delete("/{ticket_id}", status_code=204)
async def delete_report(ticket_id: str):
    db  = get_db()
    doc = await db.reports.find_one({"ticket_id": ticket_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")

    # Remove image from Cloudinary
    if doc.get("image_public_id"):
        await delete_report_image(doc["image_public_id"])

    await db.reports.delete_one({"ticket_id": ticket_id})
    return None   # 204 No Content


# ── Private helper ─────────────────────────────────────────────────────────
def _resolve_department(category: IssueCategory) -> str:
    mapping = {
        IssueCategory.WATER_SUPPLY:     "Public Health Engineering Dept",
        IssueCategory.ROADS:            "Rural Roads Department",
        IssueCategory.WATER_MANAGEMENT: "Irrigation Department",
        IssueCategory.STREET_LIGHTS:    "Rural Electrification Dept",
        IssueCategory.DRAINAGE:         "Sanitation Department",
        IssueCategory.OTHER:            "Gram Panchayat",
    }
    return mapping.get(category, "Gram Panchayat")
