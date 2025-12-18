import asyncio
from services.utils import human_type, kill_cookie_banners

async def drive_msc(page, container_number):
    """
    MSC Driver (Official Site)
    URL: https://www.msc.com/en/track-a-shipment
    """
    print(f"🚢 [MSC] Tracking: {container_number}")

    await page.goto("https://www.msc.com/en/track-a-shipment", timeout=60000)

    # 1. Kill Cookies (MSC has a big banner)
    await kill_cookie_banners(page)

    # 2. Input
    # Selector from your HTML: id="trackingNumber"
    print("   -> Finding Input...")
    await page.wait_for_selector("#trackingNumber", state="visible")

    await human_type(page, "#trackingNumber", container_number)

    # 3. Click Search
    # Usually a button with icon-search or type=submit inside the form
    # We use a broad text match to be safe, or the search icon class
    print("   -> Clicking Search...")

    # Try multiple button selectors common on MSC
    search_selectors = [
        "button[type='submit']",
        "button.search-button",
        "button .fa-search"
    ]

    clicked = False
    for sel in search_selectors:
        if await page.locator(sel).first.is_visible():
            await page.locator(sel).first.click()
            clicked = True
            break

    if not clicked:
        # Fallback: Press Enter in the input box
        await page.locator("#trackingNumber").press("Enter")

    # 4. Wait for Results
    print("   -> Waiting for results...")
    try:
        # MSC loads results dynamically via AJAX
        await page.wait_for_load_state("networkidle")

        # Look for result container
        await page.wait_for_selector(".result-container, .tracking-result", timeout=20000)

        return await page.inner_text("body")
    except:
        print("   ⚠️ MSC Timeout. Returning body dump.")
        return await page.inner_text("body")
