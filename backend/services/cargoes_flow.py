import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

# Exact URL from your browser inspection
API_BASE_URL = "https://connect.cargoes.com/flow/api/public_tracking/v1/shipments"

# Strip() removes accidental spaces
API_KEY = os.getenv("CARGOES_FLOW_API_KEY", "").strip()
ORG_TOKEN = os.getenv("CARGOES_FLOW_ORG_TOKEN", "").strip()

async def check_cargoes_flow(tracking_number: str, carrier_type: str):
    """
    Queries Cargoes Flow API using Browser-like Headers.
    """
    if not API_KEY or not ORG_TOKEN:
        print("   ⚠️ Missing Cargoes Flow keys.")
        return None

    clean_number = tracking_number.replace(" ", "").replace("-", "")
    print(f"   ⚡ API: Checking Cargoes Flow for {clean_number}...")

    # Parameters from your browser request
    params = {}
    if carrier_type == "sea":
        params = {
            "shipmentType": "INTERMODAL_SHIPMENT",
            "containerNumber": clean_number,
            "includeUniqueContainers": "true", # From your curl
            "_limit": "50"
        }
    else:
        params = {
            "shipmentType": "AIR_SHIPMENT",
            "awbNumber": clean_number,
            "_limit": "50"
        }

    # HEADERS matching your successful browser request
    headers = {
        "X-DPW-ApiKey": API_KEY,
        "X-DPW-Org-Token": ORG_TOKEN,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                API_BASE_URL,
                params=params,
                headers=headers,
                timeout=20.0
            )

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    print("   ✅ API Success: Data found!")
                    return json.dumps(data, indent=2)
                else:
                    print("   🔸 API returned 200 but list is empty.")
                    return None
            elif response.status_code == 404:
                print("   🔸 API: Shipment not found.")
                return None
            elif response.status_code == 401:
                print("   ⛔ API Auth Failed (401).")
                return None
            else:
                print(f"   🔸 API Error {response.status_code}: {response.text}")
                return None

    except Exception as e:
        print(f"   ⚠️ API Connection Failed: {e}")
        return None
