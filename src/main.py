import json
import re
import requests
from pathlib import Path
from urllib.parse import unquote, urlparse
from typing import Optional, Dict, List

import typer

# Import your existing models
from models import Directory, File, Link, Node


class BrightspaceParser:
    def __init__(self, base_url: str, auth_path: Path):
        self.session = requests.Session()
        self.base_url = base_url
        self._setup_auth(auth_path)

    def _setup_auth(self, auth_path: Path):
        with open(auth_path, 'r') as f:
            data = json.load(f)

        for cookie in data.get('cookies', []):
            self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])

        origins = data.get('origins', [])
        token = None
        for origin in origins:
            if "brightspace.tudelft.nl" in origin['origin']:
                for item in origin['localStorage']:
                    if item['name'] == "D2L.Fetch.Tokens":
                        token_data = json.loads(item['value'])
                        first_key = next(iter(token_data))
                        token = token_data[first_key].get("access_token")
                        break

        if token:
            self.session.headers.update({
                "Authorization": f"Bearer {token}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            print("✅ Authenticated with Bearer Token.")
        else:
            raise ValueError("❌ Could not find Bearer token in auth.json.")

    def parse_course(self, course_url: str, output_root: Path) -> Directory:
        match = re.search(r"/content/(\d+)", course_url)
        if not match:
            raise ValueError("Could not find Course ID in URL.")
        course_id = match.group(1)

        # 1. Fetch Course Name
        course_name = f"Course_{course_id}"
        print(f"🔍 Parsing Course ID: {course_id}")

        # 2. Fetch Table of Contents
        versions_to_try = ["1.82", "1.74", "1.70", "1.67", "1.50"]
        toc_data = None

        for ver in versions_to_try:
            print(f"   Trying API v{ver}...")
            try:
                # ignoreDateRestrictions ensures we see hidden content
                endpoint = f"/d2l/api/le/{ver}/{course_id}/content/toc?ignoreDateRestrictions=true"
                toc_data = self._get_json(endpoint)
                if toc_data:
                    print(f"   ✅ Success with API v{ver}")
                    break
            except Exception as e:
                continue

        if not toc_data:
            raise Exception("❌ Failed to fetch Table of Contents.")

        # Try to find a better course name from the root module if available
        if 'Modules' in toc_data and len(toc_data['Modules']) > 0:
            # Just a heuristic, sometimes the root is the course name
            pass

        # Setup Output
        course_root = output_root / course_name
        course_root.mkdir(parents=True, exist_ok=True)

        children = []
        for module in toc_data.get('Modules', []):
            child = self._process_module(module, course_root)
            if child:
                children.append(child)

        root_node = Directory(name=course_name, children=children)
        root_node.save_json(course_root / "course_structure.json")
        print(f"\n✅ Done! Exported to: {course_root}")
        return root_node

    def _process_module(self, module_data: Dict, parent_path: Path) -> Optional[Directory]:
        title = self._clean_name(module_data.get('Title', 'Untitled Module'))

        # Extract Description (Rich Text is usually in 'Html')
        description = module_data.get('Description', {}).get('Html', None)

        current_path = parent_path / title
        current_path.mkdir(exist_ok=True)

        children = []

        # Recursively process sub-modules
        for sub_module in module_data.get('Modules', []):
            child = self._process_module(sub_module, current_path)
            if child:
                children.append(child)

        # Process Topics
        for topic in module_data.get('Topics', []):
            node = self._process_topic(topic, current_path)
            if node:
                children.append(node)

        # Pass description to Directory model
        return Directory(name=title, description=description, children=children)

    def _process_topic(self, topic_data: Dict, parent_path: Path) -> Optional[Node]:
        title = self._clean_name(topic_data.get('Title', 'Untitled Topic'))
        description = topic_data.get('Description', {}).get('Html', None)
        url = topic_data.get('Url', '')

        # KEY FIX: Use ActivityType and correct IDs
        # 1 = File, 2 = Link
        activity_type = topic_data.get('ActivityType', -1)

        if activity_type == 1:  # File
            file_name = self._get_filename_from_url(url) or f"{title}.pdf"
            save_path = parent_path / file_name
            download_url = f"{self.base_url}{url}"

            if not save_path.exists():
                print(f"  ⬇️  Downloading: {title}")
                self._download_file(download_url, save_path)
            else:
                print(f"  ⏭️  Skipping (exists): {title}")

            return File(name=title, description=description, file=save_path)

        elif activity_type == 2:  # Link
            return Link(name=title, description=description, url=url)

        else:
            # Debug: print what we are skipping so you know if we missed something
            # print(f"  ⚠️ Skipping unknown type {activity_type} for: {title}")
            pass

        return None

    def _get_json(self, endpoint: str) -> Dict:
        url = f"{self.base_url}{endpoint}"
        resp = self.session.get(url)
        if resp.status_code == 403: raise PermissionError(f"403 Forbidden")
        if resp.status_code == 404: return None
        resp.raise_for_status()
        return resp.json()

    def _download_file(self, url: str, path: Path):
        try:
            with self.session.get(url, stream=True) as r:
                r.raise_for_status()
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
        except Exception as e:
            print(f"  ❌ Failed to download {url}: {e}")

    def _clean_name(self, name: str) -> str:
        return re.sub(r'[<>:"/\\|?*]', '_', name).strip()

    def _get_filename_from_url(self, url: str) -> str:
        path = unquote(url.split('?')[0])
        return path.split('/')[-1]

def main(
    course_url: str = typer.Argument(..., help="The URL of the course content (e.g., https://brightspace.tudelft.nl/d2l/le/content/12345/Home)"),
    output: Path = typer.Option(Path("./downloads"), "--output", "-o", help="Output directory for downloaded content"),
    auth: Path = typer.Option(Path("auth.json"), "--auth", "-a", help="Path to the auth.json file")
):
    """
    Scrape a Brightspace course and download its content.
    """
    # Heuristic to find base_url
    parsed_uri = urlparse(course_url)
    base_url = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
    print(f"Detected Base URL: {base_url}")

    scraper = BrightspaceParser(base_url=base_url, auth_path=auth)
    scraper.parse_course(course_url, output)

if __name__ == "__main__":
    typer.run(main)