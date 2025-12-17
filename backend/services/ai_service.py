import os
import json
import base64
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- TEXT PARSING SYSTEM PROMPT ---
SYSTEM_PROMPT = """
You are an expert Logistics Operations Assistant for MP Cargo.
Extract critical tracking details from raw website text.

RULES:
1. "latest_date": Extract the date of the MOST RECENT event (Format: DD-Mon-YYYY).
2. "status": One of [Booked, In Transit, Arrived, Customs Hold, Delivered, Exception].
3. "summary": A concise, professional 1-sentence summary.

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
             return {"latest_date": "N/A", "status": "Error", "summary": "Insufficient data."}

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Carrier: {carrier}\n\nRaw Data:\n{raw_text[:3000]}"}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"AI Parse Error: {e}")
        return {"latest_date": "Error", "status": "AI Parse Failed", "summary": "Error."}

# --- VISION CAPTCHA SOLVER ---
async def solve_captcha_image(base64_image: str):
    """
    Sends the CAPTCHA image to GPT-4o for solving.
    """
    print("   🤖 Asking GPT-4o to solve CAPTCHA...")
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What is the text in this captcha image? Return ONLY the text, no spaces, no punctuation."},
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
        captcha_text = response.choices[0].message.content.strip()
        print(f"   🤖 AI Solved: {captcha_text}")
        return captcha_text
    except Exception as e:
        print(f"   ❌ Vision Error: {e}")
        return None
