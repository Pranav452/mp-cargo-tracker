import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are an expert Logistics Operations Assistant for MP Cargo.
Your task is to extract critical tracking details from raw website text.

INPUT: Raw text scraped from a carrier website (Air India, Hapag, etc.).
OUTPUT: Strict JSON format.

RULES:
1. "latest_date": Extract the date of the MOST RECENT event (Format: DD-Mon-YYYY).
2. "status": One of [Booked, In Transit, Arrived, Customs Hold, Delivered, Exception].
3. "summary": A concise, professional 1-sentence summary for the Operations Manager.
   - If "CONSIGNEE IS NOTIFIED" or "DELIVERED" is found, mark as "Arrived" or "Delivered".
   - If dates are confusing, prioritize the latest "Departed" or "Arrived" event.

JSON STRUCTURE:
{
  "latest_date": "string",
  "status": "string",
  "summary": "string"
}
"""

async def parse_tracking_data(raw_text: str, carrier: str):
    try:
        if not raw_text or len(raw_text) < 50:
             return {
                "latest_date": "N/A",
                "status": "Error",
                "summary": "Scraper returned insufficient data."
            }

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Carrier: {carrier}\n\nRaw Data:\n{raw_text[:3000]}"} # Limit tokens
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"AI Error: {e}")
        return {
            "latest_date": "Error",
            "status": "AI Parse Failed",
            "summary": "Could not analyze data."
        }
