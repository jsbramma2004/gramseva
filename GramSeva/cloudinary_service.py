"""
app/services/cloudinary_service.py
Handles image uploads and deletions via Cloudinary.
"""
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException
from dotenv import load_dotenv
import os

load_dotenv()

# ── Configure Cloudinary ───────────────────────────────────────────────────
cloudinary.config(
    cloud_name  = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key     = os.getenv("CLOUDINARY_API_KEY"),
    api_secret  = os.getenv("CLOUDINARY_API_SECRET"),
    secure      = True,
)

ALLOWED_TYPES  = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
MAX_SIZE_BYTES = 5 * 1024 * 1024   # 5 MB


async def upload_report_image(file: UploadFile) -> dict:
    """
    Validate and upload an image to Cloudinary.

    Returns:
        { "url": str, "public_id": str }
    """
    # ── Validate content type ──────────────────────────────────
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file.content_type}'. Allowed: JPG, PNG, WEBP"
        )

    # ── Read & validate size ───────────────────────────────────
    contents = await file.read()
    if len(contents) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="Image too large. Maximum allowed size is 5 MB."
        )

    # ── Upload to Cloudinary ───────────────────────────────────
    try:
        result = cloudinary.uploader.upload(
            contents,
            folder          = "gramseva/reports",
            resource_type   = "image",
            quality         = "auto:good",     # auto-compress
            fetch_format    = "auto",           # serve as WebP when supported
            transformation  = [
                {"width": 1200, "crop": "limit"},  # max width 1200px
            ],
        )
        return {
            "url":       result["secure_url"],
            "public_id": result["public_id"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")


async def delete_report_image(public_id: str) -> bool:
    """Delete an image from Cloudinary by its public_id."""
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get("result") == "ok"
    except Exception:
        return False
