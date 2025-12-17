import asyncio
import random

# Stealth Args: Makes the bot look like a real Chrome user
STEALTH_ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--disable-infobars',
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--window-size=1920,1080',
]

async def human_type(page, selector, text):
    """Types text slowly with random delays to mimic a human."""
    try:
        # Highlight for visual debugging
        await page.locator(selector).highlight()
        # Type char by char
        for char in text:
            await page.type(selector, char, delay=random.randint(50, 150))
    except Exception as e:
        print(f"   [Type Error] Could not type into {selector}: {e}")
        # Emergency fill
        await page.fill(selector, text)

async def kill_cookie_banners(page):
    """Tries to click common 'Accept' buttons."""
    try:
        # Common selectors for cookie buttons
        selectors = [
            "button:has-text('Accept')",
            "button:has-text('Agree')",
            "button:has-text('Allow All')",
            "#onetrust-accept-btn-handler",
            ".cookie-close-btn"
        ]
        for sel in selectors:
            if await page.locator(sel).first.is_visible(timeout=500):
                print("   🍪 Splat! Cookie banner killed.")
                await page.locator(sel).first.click()
                return
    except:
        pass
