import time
from playwright.sync_api import sync_playwright


def save_auth_state(entry_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"👉 Navigate to {entry_url} and log in.")
        page.goto(entry_url)

        # Wait until we see a specific element that confirms login
        # Generic check: waiting until "d2l/home" is in the URL (typical dashboard)
        try:
            page.wait_for_url("**/d2l/home**", timeout=120000)  # 2 minute timeout for login
            print("✅ Login detected! Exiting...")
            time.sleep(1)
            context.storage_state(path="auth.json")
            print("💾 Auth state saved to 'auth.json'.")
        except Exception as e:
            print("❌ Timed out waiting for login. Did you reach the homepage?")

        browser.close()


if __name__ == "__main__":
    # Use the general login URL for your institution
    save_auth_state("https://brightspace.tudelft.nl/d2l/home")