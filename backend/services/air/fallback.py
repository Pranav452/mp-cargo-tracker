import asyncio
from playwright.async_api import Page

async def drive_air_fallback(page: Page, tracking_number: str):
    """
    Service: Track-Trace Air Fallback
    """
    print(f"✈️ [Fallback] Routing {tracking_number} to Track-Trace...")

    await page.goto("https://www.track-trace.com/aircargo", timeout=45000)

    await page.fill("input[name='number']", tracking_number)

    try:
        async with page.expect_popup() as popup_info:
            await page.click("#wc-multi-form-button_direct")

        new_page = await popup_info.value
        await new_page.wait_for_load_state("domcontentloaded")

        # Interstitial
        try:
            btn = new_page.get_by_text("I'm sure, continue with", exact=False)
            if await btn.is_visible(timeout=3000): await btn.click()
        except: pass

        await asyncio.sleep(5)
        return await new_page.inner_text("body")

    except Exception as e:
        print(f"   ❌ Fallback Error: {e}")
        return "Fallback failed."
