# Brightspace Scraper

Scrapes an entire BrightSpace course, maintaining proper file structure. 

Standard downloads typically flatten the directory structure, ignore external links, or omit the rich text context provided in module descriptions.

This scraper retrieves all of it, quickly and compactly.

## Prerequisites

* Python 3.11 or higher
* [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/rbmr/BrightspaceScraper
    cd BrightspaceScraper
    ```

2.  **Install dependencies:**
    
    Using **uv** (Recommended, uses `uv.lock`):
    ```bash
    uv sync
    ```

    Or using **pip**:
    ```bash
    pip install .
    ```

3.  **Install Playwright browsers:**
    This tool uses a real browser for authentication. You must install the browser binaries:
    ```bash
    playwright install chromium
    ```

## Authentication

Brightspace uses complex authentication (SSO, MFA) which is difficult to replicate with simple scripts. This project solves this by using a real browser to capture your session.

1.  Run the auth script with your university's Brightspace URL:
    ```bash
    # Example for TU Delft
    python src/auth.py [https://brightspace.tudelft.nl](https://brightspace.tudelft.nl)
    ```

2.  A Chromium browser window will open.
3.  Log in manually using your credentials (including any 2FA/MFA steps).
4.  Once you land on the Brightspace homepage (e.g., URL contains `/d2l/home`), the script will detect the login, save your session cookies and tokens to `auth.json`, and close the browser.

> **Note:** The `auth.json` file contains your session tokens. Do not share this file.

## Usage

Once authenticated, you can scrape a specific course.

1.  **Find the Course URL:**
    Navigate to the course you want to download in your browser and go to the "Content" tab. The URL should look something like:
    `https://brightspace.tudelft.nl/d2l/le/content/12345/Home`

2.  **Run the Scraper:**
    ```bash
    python src/main.py <COURSE_URL>
    ```

    **Options:**
    * `--output` / `-o`: Specify the download directory (default: `./downloads`).
    * `--auth` / `-a`: Path to the auth file (default: `auth.json`).

    **Example:**
    ```bash
    python src/main.py [https://brightspace.tudelft.nl/d2l/le/content/54321/Home](https://brightspace.tudelft.nl/d2l/le/content/54321/Home) --output ./my_courses
    ```

3.  **Output:**
    The tool will create a folder named `Course_<ID>` (or the course name) inside your output directory. Inside, you will find:
    * A full directory structure matching the course modules.
    * Course files (PDFs, PPTs, etc.).
    * `course_structure.json`: A detailed JSON map of the entire course hierarchy, including descriptions and links.