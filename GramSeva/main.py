"""
app/main.py
GramSeva Backend — FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os

from app.database import connect_db, close_db
from app.routers import reports

load_dotenv()

# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "GramSeva API",
    description = "Rural Infrastructure Issue Reporting Portal — Backend API",
    version     = "1.0.0",
    docs_url    = "/docs",        # Swagger UI
    redoc_url   = "/redoc",
)

# ── CORS ───────────────────────────────────────────────────────────────────
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins     = [FRONTEND_URL, "http://localhost:5500", "http://127.0.0.1:5500"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Lifecycle ──────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    await connect_db()
    print("🚀  GramSeva API is running.")

@app.on_event("shutdown")
async def shutdown():
    await close_db()

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(reports.router, prefix="/api/v1")

# ── Health check ───────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "GramSeva API", "version": "1.0.0"}

@app.get("/health", tags=["Health"])
async def health():
    return JSONResponse({"status": "healthy"})
