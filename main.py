from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

#  Load environment variables
load_dotenv()

#  Create required directories (prevents crash)
os.makedirs("data/uploads", exist_ok=True)
os.makedirs("data/reports", exist_ok=True)

#  Initialize app
app = FastAPI(title="FairLens API")

#  CORS (useful for frontend requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # safe for hackathon
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#  Import routes AFTER app creation (avoids circular issues)
from routes import (
    upload,
    audit,
    counterfactual,
    eu_mapper,
    fix,
    report,
    history,
)

#  Register routes
app.include_router(upload.router)
app.include_router(audit.router)
app.include_router(counterfactual.router)
app.include_router(eu_mapper.router)
app.include_router(fix.router)
app.include_router(report.router)
app.include_router(history.router)

#  Serve frontend safely
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
else:
    print("⚠ Frontend folder not found")

#  Health check (VERY useful for demo)
@app.get("/health")
def health_check():
    return {"status": "ok"}

#  Root fallback (optional safety)
@app.get("/api")
def api_root():
    return {"message": "FairLens API running"}