import asyncio
from services.utils import human_type, kill_cookie_banners

async def drive_air_india(page, tracking_number):
    """
    Air India Driver: Handles '098-12345678' split format.
    Updated: Uses text-matching for results to avoid CSS timeouts.
    """
    clean = tracking_number.replace(" ", "").replace("-", "")
    prefix = clean[:3]
    suffix = clean[3:]

    print(f"✈️ [Air India] Split: {prefix} + {suffix}")

    await page.goto("https://cargo.airindia.com/in/en/track-shipment.html", timeout=60000)

    # 1. Kill Cookies
    await kill_cookie_banners(page)

    # 2. Input 1: Airline Code
    await page.wait_for_selector("input[formcontrolname='airlineCode']", state="visible")
    await page.fill("input[formcontrolname='airlineCode']", prefix)

    # 3. Input 2: AWB Number
    await page.fill("input[formcontrolname='airwayBillNumber']", suffix)

    # 4. Click Track
    print("   -> Clicking Track button...")
    await page.click("button[title='Track Shipment']")

    # 5. Wait for Results (The Robust Way)
    print("   -> Waiting for results...")

    try:
        # We wait for the text "SHIPMENT DETAILS" or "Origin" which appears in the result table
        # This is better than looking for a specific class ID
        await page.wait_for_selector("text=SHIPMENT DETAILS", timeout=20000)
        print("   -> 'SHIPMENT DETAILS' text found. Success.")
    except:
        print("   -> Text match timed out. Trying generic load wait...")
        # Backup: Just wait for the network to stop loading things
        await page.wait_for_load_state("networkidle", timeout=5000)

    # 6. GRAB EVERYTHING
    # Even if we timed out waiting for specific text, the page might still show data.
    # We grab the body text and let the AI figure it out.
    body_text = await page.inner_text("body")

    # Basic validation to ensure we didn't just grab the login page again
    if "SHIPMENT DETAILS" in body_text or "Origin" in body_text:
        return body_text
    else:
        # If we really got nothing, raise error so Fallback can try (even if AI blocks frames)
        raise Exception("Air India page did not display result data.")
