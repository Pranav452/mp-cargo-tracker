import base64
import asyncio
from services.utils import human_type, kill_cookie_banners
from services.ai_service import solve_captcha_image

async def drive_china_airlines(page, tracking_number):
    """
    China Airlines (CI) Driver
    Features: AI Vision Captcha Solver + New Tab Handling + Frame Support
    """
    clean = tracking_number.replace(" ", "").replace("-", "")
    prefix = clean[:3]
    suffix = clean[3:]

    print(f"✈️ [China Airlines] Split: {prefix} + {suffix}")

    url = "https://cargo.china-airlines.com/CCNetv2/content/home/index.aspx"
    await page.goto(url, timeout=60000)

    # Cookie Handling
    try: await page.click("button:has-text('I accept')", timeout=3000)
    except: await kill_cookie_banners(page)

    # Menu Interaction
    print("   -> Clicking 'Shipment Tracking' menu...")
    await page.click("#shipment_traking")
    await page.wait_for_selector("#shipment_traking_block", state="visible", timeout=5000)

    # Fill Inputs
    await page.fill("#ContentPlaceHolder1_txtAwbPfx", prefix)
    await page.fill("#ContentPlaceHolder1_txtAwbNum", suffix)

    # CAPTCHA LOOP
    for attempt in range(2):
        print(f"   🔐 Captcha Attempt {attempt+1}...")

        # Screenshot
        img_selector = "#imgVldCode_Index_ShipmentTracking"
        captcha_element = page.locator(img_selector)
        await captcha_element.wait_for(state="visible")
        await asyncio.sleep(1)
        img_bytes = await captcha_element.screenshot()
        base64_img = base64.b64encode(img_bytes).decode('utf-8')

        # Solve
        captcha_text = await solve_captcha_image(base64_img)
        if not captcha_text: raise Exception("AI Vision failed")

        # Fill & Search
        await page.fill("#txtVldCode_Index_ShipmentTracking", captcha_text)
        print("   -> Clicking Search (Waiting for Popup)...")

        try:
            async with page.expect_popup(timeout=10000) as popup_info:
                await page.click("#button_st")

            new_page = await popup_info.value
            await new_page.wait_for_load_state("domcontentloaded")
            print("   ✅ Popup captured!")

            # --- ROBUST EXTRACTION ---
            # 1. Wait for network to settle (data loading)
            await new_page.wait_for_load_state("networkidle", timeout=10000)

            # 2. Check for Frames (Old sites love frames)
            frames = new_page.frames
            content = ""

            if len(frames) > 1:
                print(f"   -> Detected {len(frames)} frames. Scanning all...")
                for frame in frames:
                    try:
                        text = await frame.inner_text("body")
                        if len(text) > 50: # Only keep if it has substance
                            content += f"\n--- FRAME DATA ---\n{text}"
                    except: pass
            else:
                # No frames, just grab body
                print("   -> No frames detected. Grabbing main body.")
                content = await new_page.inner_text("body")

            # 3. Final Verification
            if len(content.strip()) < 10:
                print("   ⚠️ Content empty! Dumping HTML instead.")
                content = await new_page.content() # Fallback to HTML if text is empty

            print(f"   -> Extracted {len(content)} characters.")
            return content

        except Exception as e:
            print(f"   ⚠️ Popup failed (Captcha likely wrong): {e}")
            await page.click("#imgbReGen_Index_ShipmentTracking")
            await asyncio.sleep(2)
            continue

    raise Exception("Failed to solve Captcha after 2 attempts.")
