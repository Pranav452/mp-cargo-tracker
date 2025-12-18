import asyncio
from playwright.async_api import async_playwright
from services.utils import STEALTH_ARGS

# --- API SERVICE ---
from services.cargoes_flow import check_cargoes_flow  # <--- NEW

# --- DRIVERS ---
from services.air.air_india import drive_air_india
from services.air.china_airlines import drive_china_airlines
from services.air.silk_way import drive_silk_way
from services.air.af_klm import drive_af_klm
from services.air.etihad import drive_etihad
from services.air.saudia import drive_saudia
from services.air.fallback import drive_air_fallback

# SEA DRIVERS (Placeholders/Active)
from services.sea.hapag import drive_hapag
from services.sea.cma import drive_cma
from services.sea.fallback import drive_sea_fallback

async def master_scraper(tracking_number: str, carrier_type: str = "air", carrier_name: str = ""):
    clean = tracking_number.replace(" ", "").replace("-", "")
    prefix = clean[:3]

    print(f"\n🚦 Processing: {tracking_number} | Type: {carrier_type}")

    # ============================================================
    # TIER 1: CARGOES FLOW API (The Fast Lane)
    # ============================================================
    # We try API first. If it works, we skip Playwright entirely.
    api_result = await check_cargoes_flow(tracking_number, carrier_type)
    if api_result:
        return f"Source: Cargoes Flow API\n{api_result}"

    # ============================================================
    # TIER 2: SCRAPING (The Fallback)
    # ============================================================
    print("   🐢 API didn't have data. Switching to Scraper...")

    async with async_playwright() as p:
        # REMOVED: The iPhone/Mobile logic. Back to standard Desktop for everyone.
        browser = await p.chromium.launch(headless=False, args=STEALTH_ARGS)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        try:
            raw_data = None

            # --- SEA ROUTING ---
            if carrier_type == "sea":
                # ... (Keep existing Sea logic) ...
                carrier_lower = str(carrier_name).lower()
                if "hapag" in carrier_lower:
                    raw_data = await drive_hapag(page, clean)
                elif "cma" in carrier_lower:
                    raw_data = await drive_cma(page, clean)
                else:
                    raw_data = await drive_sea_fallback(page, clean)

            # --- AIR ROUTING ---
            else:
                if prefix == "098":
                    # THE ONLY ACTIVE DRIVER
                    raw_data = await drive_air_india(page, clean)
                elif prefix == "607": # Etihad
                    raw_data = await drive_etihad(page, tracking_number) # Pass FULL number (with dash if needed)
                elif prefix == "297":
                    raw_data = await drive_china_airlines(page, clean)
                elif prefix in ["501", "463"]: # Silk Way
                    raw_data = await drive_silk_way(page, clean)
                elif prefix in ["057", "074"]:
                    raw_data = await drive_af_klm(page, clean)
                elif prefix == "065": # Saudia
                    raw_data = await drive_saudia(page, clean)
                else:
                    raw_data = await drive_air_fallback(page, clean)

            await browser.close()
            return raw_data if raw_data else "Driver Not Implemented."

        except Exception as e:
            print(f"❌ Crash: {e}")
            await browser.close()
            return f"Error: {e}"
