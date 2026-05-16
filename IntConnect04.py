import time
import urllib.request
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# ── Config ───────

# Plain HTTP so it doesn't trick edge into thinking it's online
# neverssl.com is always http.
PORTAL_TRIGGER_URL = "http://neverssl.com"

# check connectivity 
CHECK_INTERVAL = 15

# Pause between consecutive button clicks
BUTTON_CLICK_DELAY = 2

# Maximum button clicks to attempt per login cycle
# Most browsers need 2 (Accept → Continue), Edge typically needs 1
MAX_BUTTON_CLICKS = 3

# Matches the first visible button-like element on the page, 
# whatever its text, we know it's a "primary-button" on the spoons button but sometimes others may be different
FIRST_BUTTON_XPATH = (
    "(//button | //input[@type='submit'] | //button[contains(@class, 'primary-button')] | //input[@type='button'] | //a[@role='button'])[1]"
)

# ── Helpers ───────
def check_internet(timeout: int = 5) -> bool:
    try:
        response = urllib.request.urlopen(
            "http://www.msftconnecttest.com/connecttest.txt", timeout=timeout
        )
        return response.read().strip() == b"Microsoft Connect Test"
    except (urllib.error.URLError, OSError):
        return False


def wait_for_page_load(driver, timeout: int = 10) -> bool:
    """Block until document.readyState == 'complete', or timeout."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        return True
    except Exception:
        return False


def click_first_button(driver, now: str) -> bool:
    """
    Find and click the first button-like element on the page.
    Returns True on success, False if nothing was found.
    """
    try:
        btn = driver.find_element(By.XPATH, FIRST_BUTTON_XPATH)
        label = btn.text.strip() or btn.get_attribute("value") or "unlabelled button"
        btn.click()
        print(f"[{now}] ✅ Button: Clicked '{label}'")
        return True
    except Exception as e:
        print(f"[{now}] ℹ️  Button: No clickable button found — {e}")
        return False

# ── Core logic ────────────

def attempt_portal_login(driver, now: str) -> None:
    """Navigate to the portal trigger URL and click through accept/continue screens."""
    print(f"[{now}] 🌐 No internet — attempting captive portal login...")

    try:
        driver.get(PORTAL_TRIGGER_URL)
    except Exception as e:
        print(f"[{now}] ⚠️  Navigation failed: {e}")
        return

    if not wait_for_page_load(driver):
        print(f"[{now}] ⏳ Page did not finish loading — skipping button clicks")
        return

    print(f"[{now}] ✅ Page loaded: {driver.current_url}")

    for attempt in range(1, MAX_BUTTON_CLICKS + 1):
        clicked = click_first_button(driver, now)
        if not clicked:
            break  # No button found; nothing more to try

        time.sleep(BUTTON_CLICK_DELAY)

        if check_internet():
            print(f"[{now}] ✅ Internet: Connected after click {attempt}!")
            return

        print(f"[{now}] ⏳ Still no connection after click {attempt} — trying next button...")

    print(f"[{now}] ❌ Could not connect after {MAX_BUTTON_CLICKS} click(s)")


def run_checks(driver, now: str) -> None:
    if check_internet():
        print(f"[{now}] ✅ Internet: Connected")
    else:
        print(f"[{now}] ❌ Internet: No connection")
        attempt_portal_login(driver, now)

# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    options = Options()
    options.add_argument("--start-maximized")

    print("Opening Microsoft Edge...")
    driver = webdriver.Edge(options=options)
    driver.get(PORTAL_TRIGGER_URL)
    print(f"Navigated to {PORTAL_TRIGGER_URL}")
    print(f"Checking connectivity every {CHECK_INTERVAL}s — press Ctrl+C to stop.\n")

    try:
        while True:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                run_checks(driver, now)
            except Exception as e:
                print(f"[{now}] ⚠️  Unexpected error: {e}")
            print()
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
