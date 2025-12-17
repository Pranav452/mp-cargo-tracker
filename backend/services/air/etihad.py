import asyncio
from services.utils import human_type, kill_cookie_banners

async def drive_etihad(page, tracking_number):
    """
    Etihad (607) Driver via ParcelsApp
    URL: https://parcelsapp.com/en/carriers/ethihad-airways-cargo
    """
    # ParcelsApp handles "607-12345678" or "60712345678".
    # We will use the clean version but ensure format 607-XXXX if needed.
    # Actually, aggregators usually prefer the raw clean number.
    clean = tracking_number.replace(" ", "").replace("-", "")

    print(f"✈️ [Etihad] Routing via ParcelsApp: {clean}")

    await page.goto("https://parcelsapp.com/en/carriers/ethihad-airways-cargo", timeout=60000)

    # 1. Input
    # Selector from your HTML: <input class="form-control" ...>
    input_sel = "input.form-control"
    await page.wait_for_selector(input_sel, state="visible")

    # Type full number
    await human_type(page, input_sel, clean)

    # 2. Click Track
    # Selector: <button class="btn btn-default btn-parcels">
    print("   -> Clicking Track...")
    await page.click("button.btn-parcels")

    # 3. Wait for Results
    print("   -> Waiting for results...")
    try:
        # ParcelsApp results usually appear in a div with class 'states' or 'tracking-info'
        # We wait for the spinner to disappear or content to appear
        await asyncio.sleep(5) # Initial wait for AJAX

        # Wait for any text indicating results
        await page.wait_for_selector(".states, .tracking-info, .alert-danger", timeout=20000)

        # Extract
        content = await page.inner_text("body")
        print(f"   -> Extracted {len(content)} chars.")
        return content

    except Exception as e:
        print(f"   ⚠️ Timeout waiting for ParcelsApp results: {e}")
        return await page.inner_text("body")
