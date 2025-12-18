from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # <--- NEW
from pydantic import BaseModel
from services.scraper_engine import master_scraper
from services.ai_service import parse_tracking_data
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# --- ENABLE CORS (Allow Frontend to connect) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Allow Next.js
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TrackRequest(BaseModel):
    tracking_number: str
    carrier: str = ""
    type: str = "air"

@app.post("/track/single")
async def track_single(request: TrackRequest):
    # 1. Scrape/API
    raw_text = await master_scraper(request.tracking_number, request.type, request.carrier)
    # 2. AI Parse
    ai_result = await parse_tracking_data(raw_text, request.carrier)

    return {
        "tracking_number": request.tracking_number,
        "carrier": request.carrier,
        "status": ai_result.get("status"),
        "live_eta": ai_result.get("latest_date"),
        "smart_summary": ai_result.get("summary"),
        "raw_data_snippet": raw_text[:200]
    }
