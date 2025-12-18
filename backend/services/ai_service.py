import os
import json
from datetime import datetime
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are a Logistics Operations Manager.
Analyze tracking data to determine the REAL TIME status.

CURRENT DATE: {{CURRENT_DATE}}

INPUT DATA:
- You will receive JSON containing "predicted_arrival" (ETA) and "co2_emissions".
- You will also receive a list of events.

LOGIC RULES:
1. **LIVE ETA**:
   - Look for "predicted_arrival", "destinationOceanPortEta", or "lastPortEta".
   - Format: DD-Mon-YYYY (e.g., 26-Jan-2026).
   - If NO future date is found, and the last event was > 10 days ago, return "N/A (History)".

2. **STATUS**:
   - IF "predicted_arrival" is in the FUTURE -> "In Transit".
   - IF "predicted_arrival" is in the PAST (by > 2 days) -> "Arrived / Delayed".
   - IF event says "Delivered" -> "Delivered".
   - IF event says "Discharged" and date is past -> "Discharged / Port".

3. **SMART SUMMARY**:
   - Must include the CO2 emissions if available.
   - Must explicitly state if the shipment is LATE based on Current Date.
   - Example: "Shipment is in transit to Antwerp (ETA: 26-Jan-2026). CO2: 1952kg."
   - Example (Old): "Shipment arrived on 12-May-2025. Tracking ended 7 months ago."

JSON OUTPUT FORMAT:
{
  "latest_date": "string",
  "status": "string",
  "summary": "string"
}
"""

async def parse_tracking_data(raw_text: str, carrier: str):
    try:
        if not raw_text or len(raw_text) < 50:
             return {"latest_date": "N/A", "status": "Error", "summary": "Insufficient data."}

        # CALCULATE TODAY'S DATE
        today = datetime.now().strftime("%d-%b-%Y")

        # Simple replacement to avoid format() errors with JSON braces
        final_prompt = SYSTEM_PROMPT.replace("{{CURRENT_DATE}}", today)

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": final_prompt},
                {"role": "user", "content": f"Carrier: {carrier}\n\nData:\n{raw_text[:4000]}"}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"   ⚠️ AI Parse Error: {e}")
        return {"latest_date": "Error", "status": "AI Parse Failed", "summary": "Error analyzing data."}

# --- VISION CAPTCHA SOLVER ---
async def solve_captcha_image(base64_image: str):
    print("   🤖 Asking GPT-4o to solve CAPTCHA...")
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What is the text in this captcha? Return ONLY the text."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=10
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"   ❌ Vision Error: {e}")
        return None
