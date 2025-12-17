import asyncio
from services.utils import human_type, kill_cookie_banners

async def drive_silk_way(page, tracking_number):
    """
    Silk Way West (7L) Driver
    Prefix: 501 / 463
    Challenge: Results load inside a dynamic iFrame.
    """
    clean = tracking_number.replace(" ", "").replace("-", "")
    prefix = clean[:3]
    suffix = clean[3:]

    print(f"✈️ [Silk Way] Split: {prefix} + {suffix}")

    await page.goto("https://www.silkwaywest.com/e-services/shipment-tracking/", timeout=60000)

    # 1. Kill Cookies
    await kill_cookie_banners(page)

    # 2. Input
    await page.wait_for_selector("input[name='pfx']", state="visible")
    await page.fill("input[name='pfx']", "")
    await page.fill("input[name='pfx']", prefix)
    await page.fill("input[name='awb']", suffix)

    # 3. Click Track
    print("   -> Clicking Track...")
    await page.click(".call_iframe")

    # 4. Handle the iFrame
    print("   -> Waiting for iFrame container...")
    await page.wait_for_selector(".iframe_block", state="visible", timeout=10000)

    # Wait for the iframe source to load (Critical delay)
    await asyncio.sleep(5)

    # GET FRAME PROPERLY
    frame_element = await page.wait_for_selector(".iframe_block iframe")
    frame = await frame_element.content_frame()

    if not frame:
        raise Exception("Could not attach to tracking iFrame.")

    print("   -> Attached to iFrame. Waiting for data table...")

    try:
        # Wait for the table rows to appear inside the frame
        # We look for a cell containing "Flight Nr" or similar header
        await frame.wait_for_selector("table", timeout=20000)

        # Get all text from the frame body
        # We use evaluate to get innerText which preserves formatting better
        text = await frame.evaluate("document.body.innerText")

        print(f"   -> Extracted {len(text)} chars from iFrame.")

        if len(text) < 50:
            print("   ⚠️ Text too short. Dumping HTML.")
            return await frame.content()

        return text

    except Exception as e:
        print(f"   ⚠️ Frame Read Error: {e}")
        return await frame.content()
