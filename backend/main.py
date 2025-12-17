from fastapi import FastAPI
from pydantic import BaseModel
from services.scraper_engine import master_scraper
from services.ai_service import parse_tracking_data
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

class TrackRequest(BaseModel):
    tracking_number: str
    carrier: str = ""
    type: str = "air" # 'air' or 'sea'

@app.post("/track/single")
async def track_single(request: TrackRequest):
    # 1. Scrape the Site (The "Eyes")
    raw_text = await master_scraper(request.tracking_number, request.type, request.carrier)

    # 2. Analyze the Data (The "Brain")
    ai_result = await parse_tracking_data(raw_text, request.carrier)

    # 3. Return Clean JSON
    return {
        "tracking_number": request.tracking_number,
        "carrier": request.carrier,
        "status": ai_result.get("status"),
        "live_eta": ai_result.get("latest_date"),
        "smart_summary": ai_result.get("summary"),
        "raw_data_snippet": raw_text[:200] + "..." # Keep a snippet just for debugging
    }
