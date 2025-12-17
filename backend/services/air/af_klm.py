import asyncio
from services.utils import human_type, kill_cookie_banners

async def drive_af_klm(page, tracking_number):
    """
    Air France / KLM (057 / 074) Driver
    URL: https://www.afklcargo.com/mycargo/shipment/singlesearch
    """
    # Clean the number (057-12345678 -> 05712345678)
    clean = tracking_number.replace(" ", "").replace("-", "")
    print(f"✈️ [AF/KLM] Tracking: {clean}")

    # 1. Navigate to Direct Search Page
    await page.goto("https://www.afklcargo.com/mycargo/shipment/singlesearch", timeout=60000)

    # 2. Kill Cookies
    await kill_cookie_banners(page)

    # 3. Input (It's a textarea!)
    # Selector based on formcontrolname or placeholder
    input_sel = "textarea[formcontrolname='track']"

    print("   -> Typing AWB...")
    await page.wait_for_selector(input_sel, state="visible")
    await human_type(page, input_sel, clean)

    # 4. Handle 'Disabled' Button
    # The button is disabled until valid input is detected.
    # We wait for it to become enabled.
    submit_btn = page.locator("button[type='submit']").first

    # Force a small delay to let Angular/React detect the input
    await asyncio.sleep(1)

    if await submit_btn.is_disabled():
        print("   -> Button still disabled. Triggering input events...")
        # Sometimes typing isn't enough, we trigger 'blur' or press Enter
        await page.locator(input_sel).press("Enter")
        await asyncio.sleep(1)

    # 5. Click Track
    print("   -> Clicking Track...")
    await submit_btn.click()

    # 6. Wait for Results
    print("   -> Waiting for results...")
    # Wait for the result card or container
    # Usually has class 'shipment-details' or similar, but 'body' is safe fallback
    try:
        await page.wait_for_load_state("networkidle")
        await page.wait_for_selector("afkl-shipment-details, .shipment-status", timeout=20000)
    except:
        print("   -> Specific selector timeout. Grabbing body text.")

    return await page.inner_text("body")