import asyncio
from services.utils import human_type, kill_cookie_banners

async def drive_saudia(page, tracking_number):
    """
    Saudia Cargo (065) Driver
    URL: https://saudiacargo.com/en/digital-services?tab=trackShipment
    """
    # Clean the number (065-12345678 -> 06512345678)
    clean = tracking_number.replace(" ", "").replace("-", "")
    print(f"✈️ [Saudia] Tracking: {clean}")

    # 1. Navigate
    await page.goto("https://saudiacargo.com/en/digital-services?tab=trackShipment", timeout=60000)

    # 2. Kill Cookies
    await kill_cookie_banners(page)

    # 3. Input
    # Target: <input placeholder="Enter AWB Number">
    input_sel = "input[placeholder='Enter AWB Number']"

    print("   -> Waiting for input...")
    await page.wait_for_selector(input_sel, state="visible")

    # Clear and Type
    await page.click(input_sel)
    await page.fill(input_sel, "")
    await human_type(page, input_sel, clean)

    # 4. Click Submit
    # Target: <button ...>Submit</button>
    print("   -> Clicking Submit...")
    submit_btn = page.locator("button").filter(has_text="Submit")
    await submit_btn.click()

    # 5. Wait for Results
    print("   -> Waiting for data...")
    try:
        # Wait for network requests to finish (API calls) - be more lenient
        try:
            await page.wait_for_load_state("networkidle", timeout=20000)
            print("   -> Network idle reached")
        except:
            print("   -> Network idle timeout, continuing anyway...")

        # Wait a bit more for dynamic content to load
        await asyncio.sleep(5)
        print("   -> Waited for dynamic content")

        # Check if error message appeared
        try:
            if await page.locator(".text-red-600").is_visible():
                print("   ⚠️ Site reported an error (Invalid AWB or System Down).")
                return "Error: Invalid AWB or system error"
        except:
            pass  # Element might not exist

        # First, let's see what's actually on the page now
        current_url = page.url
        print(f"   -> Current URL: {current_url}")

        # Try to find the results container - look for any element containing tracking data
        # Based on the HTML you showed, look for elements with AWB, Status, Date, etc.
        results_selectors = [
            "table",  # Results table
            ".tracking-results",
            ".results-container",
            "[class*='result']",
            "[class*='tracking']",
            ".shipment-details",
            ".tracking-table",
            ".status-table",
            "[id*='result']",
            "[id*='tracking']",
            "tbody",  # Table body
            "tr",     # Table rows
            "[class*='status']",
            "[class*='tracking']"
        ]

        results_content = ""

        # First, try to find elements that contain "AWB:" or "Status:" or "Date:"
        tracking_indicators = ["AWB:", "Status:", "Date:", "Destination:", "Flight", "RCF", "DMM"]

        for selector in results_selectors:
            try:
                elements = page.locator(selector)
                count = await elements.count()
                if count > 0:
                    print(f"   -> Checking {count} elements with selector: {selector}")
                    # Extract text from all matching elements
                    for i in range(min(count, 10)):  # Limit to first 10 to avoid spam
                        element = elements.nth(i)
                        text = await element.inner_text()
                        # Check if this element contains tracking data
                        if text.strip() and len(text) > 10:
                            has_tracking = any(indicator in text for indicator in tracking_indicators)
                            if has_tracking:
                                results_content += f"\n--- TRACKING DATA ---\n{text}\n"
                                print(f"   -> Found tracking data in element {i}: {len(text)} chars")
                    if results_content:
                        break
            except Exception as e:
                print(f"   -> Selector {selector} failed: {e}")
                continue

        # If we found specific results, return them
        if results_content:
            print(f"   -> Extracted specific results: {len(results_content)} chars")
            return results_content

        # Fallback: Extract body but look for tracking data specifically
        print("   -> No specific results found, scanning entire page...")
        body_text = await page.inner_text("body")

        # Look for tracking-related keywords and patterns
        tracking_keywords = ["AWB:", "Status:", "Date:", "Destination:", "Flight", "Segment", "RCF", "DMM", "Total Pieces", "Weight", "Volume"]
        has_tracking_data = any(keyword in body_text for keyword in tracking_keywords)

        if has_tracking_data:
            print("   -> Found tracking keywords in body text")
            # Extract just the relevant parts - look for lines that contain tracking info
            lines = body_text.split('\n')
            tracking_lines = []

            # Collect lines that have tracking data
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Check if line contains tracking keywords or looks like data (contains dates, times, etc.)
                has_keyword = any(keyword in line for keyword in tracking_keywords)
                has_data_pattern = any(pattern in line for pattern in [":", "-", "/", "Local Time", "Flight", "Departed", "Arrived"])

                if has_keyword or (has_data_pattern and len(line) > 5):
                    tracking_lines.append(line)

            if tracking_lines:
                result = '\n'.join(tracking_lines)
                print(f"   -> Extracted {len(tracking_lines)} tracking lines, {len(result)} chars")
                return result

            # If no specific lines found, return the whole body but limit it
            return body_text[:5000]  # Limit to avoid too much data
        else:
            print("   ⚠️ No tracking data found in response")
            return "Error: No tracking data found"

    except Exception as e:
        print(f"   ⚠️ Wait Error: {e}")
        # Even on error, try to get whatever is there
        try:
            return await page.inner_text("body")
        except:
            return f"Error: {e}"
