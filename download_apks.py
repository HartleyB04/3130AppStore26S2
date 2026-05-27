import requests
import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()
TOKEN = os.environ.get("COMP3130_TOKEN")
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
BASE_URL = "http://3.104.146.108/assets/apk/"
OUTPUT_DIR = Path("comp3130-apks")
INDEX_HTML = Path("index.html")
MAX_WORKERS = 4

# Extract embedded APPS JSON from index.html
print("Reading app list from index.html...")
html = INDEX_HTML.read_text()
match = re.search(r"const APPS = (\[.*?\]);", html, re.DOTALL)
if not match:
    print("Could not find APPS data in index.html. Make sure fetch_apps.py has been run first.")
    exit(1)

apps = json.loads(match.group(1))
apk_apps = [a for a in apps if a.get("hasApk") and a.get("slug")]
print(f"Found {len(apk_apps)} apps with APKs out of {len(apps)} total.\n")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
print(f"Saving to: {OUTPUT_DIR}")
print(f"Downloading {MAX_WORKERS} at a time...\n")

success = 0
skipped = 0
failed = []

def download(app, index, total):
    slug = app["slug"]
    name = app.get("name", slug)
    dest = OUTPUT_DIR / f"{slug}.apk"

    if dest.exists():
        return "skipped", name, None

    url = f"{BASE_URL}{slug}.apk"
    try:
        r = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        if r.status_code == 200:
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
            size_mb = dest.stat().st_size / (1024 * 1024)
            return "success", name, size_mb
        else:
            return "failed", name, f"HTTP {r.status_code}"
    except Exception as e:
        return "failed", name, str(e)

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(download, app, i, len(apk_apps)): app for i, app in enumerate(apk_apps, 1)}
    completed = 0
    for future in as_completed(futures):
        completed += 1
        status, name, detail = future.result()
        if status == "success":
            print(f"  [{completed}/{len(apk_apps)}] ✓ {name} ({detail:.1f} MB)")
            success += 1
        elif status == "skipped":
            print(f"  [{completed}/{len(apk_apps)}] – {name} (already downloaded)")
            skipped += 1
        else:
            print(f"  [{completed}/{len(apk_apps)}] ✗ {name} ({detail})")
            failed.append(name)

print(f"\nDone. {success} downloaded, {skipped} skipped, {len(failed)} failed.")
if failed:
    print("Failed:")
    for f in failed:
        print(f"  - {f}")
