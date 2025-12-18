import asyncio
from playwright.async_api import Page

async def drive_sea_fallback(page: Page, container_number: str):
    """
    Service: Track-Trace Container Fallback
    """
    print(f"⚓ [Fallback] Routing {container_number} to Track-Trace...")

    await page.goto("https://www.track-trace.com/container", timeout=45000)

    # 1. Input
    await page.fill("input[name='number']", container_number)

    # 2. Click Track & Catch New Tab
    try:
        async with page.expect_popup() as popup_info:
            await page.click("#wc-multi-form-button_direct")

        # 3. Switch to the New Tab
        new_page = await popup_info.value
        await new_page.wait_for_load_state("domcontentloaded")

        # 4. Handle "I'm Sure" Interstitial
        print("   -> Checking for Interstitial...")
        try:
            # Look for button text
            btn = new_page.get_by_text("I'm sure, continue with", exact=False)
            if await btn.is_visible(timeout=5000):
                print("   -> Clicking Interstitial...")
                await btn.click()
                await new_page.wait_for_load_state("domcontentloaded")
        except:
            pass

        # 5. Wait for external site to load
        print("   -> Waiting for results...")
        await asyncio.sleep(8)

        return await new_page.inner_text("body")

    except Exception as e:
        print(f"   ❌ Fallback Error: {e}")
        return "Fallback failed to retrieve data."
