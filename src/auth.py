import argparse
import time
from pathlib import Path

import typer
from playwright.sync_api import sync_playwright


def save_auth_state(
    url: str = typer.Argument(..., help="The login URL for your Brightspace instance (e.g., https://brightspace.tudelft.nl)"),
    output: Path = typer.Option(Path("auth.json"), "--output", "-o", help="Path to save the auth file")
):
    with sync_playwright() as p:
        print(f"Launching browser...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"Navigate to {url} and log in.")
        page.goto(url)

        # Wait until we see a specific element that confirms login
        # Generic check: waiting until "d2l/home" is in the URL (typical dashboard)
        try:
            page.wait_for_url("**/d2l/home**", timeout=300_000)
            print("Login detected! Exiting...")
            time.sleep(1)
            context.storage_state(path=output)
            print("Auth state saved to 'auth.json'.")
        except Exception as e:
            print("Timed out waiting for login. Did you reach the homepage?")

        browser.close()


if __name__ == "__main__":
    typer.run(save_auth_state)