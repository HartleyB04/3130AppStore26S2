import requests
import time
import json
import os
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()
TOKEN = os.environ.get("COMP3130_TOKEN")
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
BASE_API = "http://3.104.146.108/api/app/"
BASE_ASSETS = "http://3.104.146.108"
INDEX_HTML = Path("index.html")
SCREENSHOTS_DIR = Path("comp3130-screenshots")
FULL_DATA_FILE = Path("full_data.json")

# ── Step 1: Extract IDs from existing index.html ──────────────────────────────
print("Reading app IDs from index.html...")
html = INDEX_HTML.read_text()
match = re.search(r"const APPS = (\[.*?\]);", html, re.DOTALL)
if not match:
    print("Could not find APPS data in index.html. Run fetch_app.py first.")
    exit(1)

apps_slim = json.loads(match.group(1))
ids = [a["id"] for a in apps_slim if a.get("id")]
print(f"Found {len(ids)} app IDs.\n")

# ── Step 2: Fetch full detail for each ID ─────────────────────────────────────
def fetch_detail(app_id):
    try:
        r = requests.get(f"{BASE_API}{app_id}", headers=HEADERS, timeout=15)
        if r.status_code == 200:
            data = r.json().get("data")
            return app_id, data
        return app_id, None
    except Exception as e:
        return app_id, None

print("Fetching full details for each app...")
full_apps = {}
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(fetch_detail, app_id): app_id for app_id in ids}
    done = 0
    for future in as_completed(futures):
        app_id, data = future.result()
        done += 1
        if data:
            full_apps[app_id] = data
            print(f"  [{done}/{len(ids)}] ✓ {data.get('name', app_id)}", end="\r")
        else:
            print(f"  [{done}/{len(ids)}] ✗ Failed: {app_id}", end="\r")

print(f"\n\nFetched {len(full_apps)} apps.\n")

# Save raw full data
with open(FULL_DATA_FILE, "w") as f:
    json.dump(list(full_apps.values()), f, indent=2)
print(f"Full data saved to {FULL_DATA_FILE}\n")

# ── Step 3: Download first screenshot for each app ────────────────────────────
SCREENSHOTS_DIR.mkdir(exist_ok=True)
print("Downloading screenshots...")

def download_screenshots(app):
    images = app.get("images", [])
    if not images:
        return app["id"], []
    filenames = []
    for idx, image in enumerate(images):
        url_path = image.get("url", "")
        ext = Path(url_path).suffix or ".png"
        filename = f"{app['slug']}_{idx}{ext}"
        dest = SCREENSHOTS_DIR / filename
        if dest.exists():
            filenames.append(filename)
            continue
        try:
            r = requests.get(f"{BASE_ASSETS}{url_path}", headers=HEADERS, timeout=30, stream=True)
            if r.status_code == 200:
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(1024 * 256):
                        f.write(chunk)
                filenames.append(filename)
        except:
            pass
    return app["id"], filenames

screenshot_map = {}
total_images = sum(len(app.get("images", [])) for app in full_apps.values())
downloaded_images = 0
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(download_screenshots, app): app["id"] for app in full_apps.values()}
    for future in as_completed(futures):
        app_id, filenames = future.result()
        screenshot_map[app_id] = filenames
        downloaded_images += len(filenames)
        print(f"  [{downloaded_images}/{total_images}] images downloaded", end="\r")

print(f"\n\nScreenshots saved to {SCREENSHOTS_DIR}/\n")

# ── Step 4: Build enhanced HTML ───────────────────────────────────────────────
apps_sorted = sorted(full_apps.values(), key=lambda x: x.get("owner", {}).get("name", "").lower())

# Slim for JS embedding
slim = []
for app in apps_sorted:
    owner = app.get("owner", {})
    images = app.get("images", [])
    safety = app.get("dataSafety", {})
    slim.append({
        "id": app.get("id", ""),
        "name": app.get("name", ""),
        "slug": app.get("slug", ""),
        "description": (app.get("description", "") or "").replace("**", "").replace("&#x20;", " ").strip(),
        "instructions": (app.get("instructions", "") or "").replace("**", "").replace("&#x20;", " ").strip(),
        "owner": owner.get("name", ""),
        "email": owner.get("email", ""),
        "hasApk": bool(app.get("apkFile")),
        "repo": app.get("repoLink", ""),
        "screenshots": [f"comp3130-screenshots/{fn}" for fn in screenshot_map.get(app.get("id"), [])],
        "imageCount": len(images),
        "dateCreated": app.get("dateCreated", ""),
        "collectsPersonalInfo": safety.get("personalInformation", {}).get("shared", False),
        "usesCamera": safety.get("camera", {}).get("shared", False),
        "usesLocation": safety.get("location", {}).get("shared", False),
    })

apps_json = json.dumps(slim, indent=2)
generated = datetime.now().strftime("%d %b %Y %H:%M")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>COMP3130 App Gallery — S1 2026</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet" />
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg: #0d0f14;
      --surface: #13161d;
      --border: #1e2330;
      --accent: #c8a84b;
      --accent2: #e05c3a;
      --text: #e8eaf0;
      --muted: #6b7280;
      --card-bg: #161921;
      --card-hover: #1a1e28;
    }}

    body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'DM Sans', sans-serif;
      min-height: 100vh;
    }}

    header {{
      border-bottom: 1px solid var(--border);
      padding: 2.5rem 2rem 2rem;
      position: relative;
      overflow: hidden;
    }}

    header::before {{
      content: '';
      position: absolute;
      top: -60px; left: -60px;
      width: 300px; height: 300px;
      background: radial-gradient(circle, rgba(200,168,75,0.12) 0%, transparent 70%);
      pointer-events: none;
    }}

    .header-label {{
      font-family: 'DM Mono', monospace;
      font-size: 0.7rem;
      letter-spacing: 0.15em;
      color: var(--accent);
      text-transform: uppercase;
      margin-bottom: 0.5rem;
    }}

    h1 {{
      font-family: 'Syne', sans-serif;
      font-size: clamp(2rem, 5vw, 3.5rem);
      font-weight: 800;
      line-height: 1;
      letter-spacing: -0.02em;
    }}

    h1 span {{ color: var(--accent); }}

    .header-meta {{
      margin-top: 0.75rem;
      font-family: 'DM Mono', monospace;
      font-size: 0.75rem;
      color: var(--muted);
    }}

    .header-links {{
      margin-top: 1rem;
      display: flex;
      gap: 1rem;
    }}

    .header-links a {{
      font-family: 'DM Mono', monospace;
      font-size: 0.72rem;
      color: var(--accent);
      text-decoration: none;
    }}

    .header-links a:hover {{ text-decoration: underline; }}

    .controls {{
      padding: 1.25rem 2rem;
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
      align-items: center;
      border-bottom: 1px solid var(--border);
      position: sticky;
      top: 0;
      background: rgba(13,15,20,0.95);
      backdrop-filter: blur(8px);
      z-index: 10;
    }}

    .search-wrap {{
      position: relative;
      flex: 1;
      min-width: 200px;
      max-width: 400px;
    }}

    .search-wrap svg {{
      position: absolute;
      left: 0.75rem;
      top: 50%;
      transform: translateY(-50%);
      color: var(--muted);
      pointer-events: none;
    }}

    input[type="text"] {{
      width: 100%;
      background: var(--surface);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 0.6rem 0.75rem 0.6rem 2.25rem;
      border-radius: 6px;
      font-family: 'DM Sans', sans-serif;
      font-size: 0.875rem;
      outline: none;
      transition: border-color 0.15s;
    }}

    input[type="text"]:focus {{ border-color: var(--accent); }}
    input[type="text"]::placeholder {{ color: var(--muted); }}

    .filter-btns {{
      display: flex;
      gap: 0.4rem;
      flex-wrap: wrap;
    }}

    .filter-btn {{
      background: var(--surface);
      border: 1px solid var(--border);
      color: var(--muted);
      padding: 0.45rem 0.85rem;
      border-radius: 6px;
      font-family: 'DM Mono', monospace;
      font-size: 0.68rem;
      letter-spacing: 0.05em;
      cursor: pointer;
      transition: all 0.15s;
      white-space: nowrap;
    }}

    .filter-btn:hover {{ border-color: var(--accent); color: var(--accent); }}
    .filter-btn.active {{ background: var(--accent); border-color: var(--accent); color: #000; font-weight: 500; }}

    .stats {{
      font-family: 'DM Mono', monospace;
      font-size: 0.72rem;
      color: var(--muted);
      margin-left: auto;
      white-space: nowrap;
    }}

    .stats span {{ color: var(--accent); }}

    /* ── Grid ── */
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1.25rem;
      padding: 1.5rem 2rem;
    }}

    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      overflow: hidden;
      cursor: pointer;
      transition: border-color 0.15s, background 0.15s, transform 0.15s;
      animation: fadeIn 0.3s ease both;
    }}

    .card:hover {{
      border-color: var(--accent);
      background: var(--card-hover);
      transform: translateY(-2px);
    }}

    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(6px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    .card-img {{
      width: 100%;
      aspect-ratio: 9/16;
      max-height: 220px;
      object-fit: cover;
      object-position: top;
      background: var(--surface);
      display: block;
    }}

    .card-img-placeholder {{
      width: 100%;
      height: 140px;
      background: var(--surface);
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--muted);
      font-family: 'DM Mono', monospace;
      font-size: 0.7rem;
    }}

    .card-body {{
      padding: 1rem;
    }}

    .card-name {{
      font-family: 'Syne', sans-serif;
      font-weight: 700;
      font-size: 1rem;
      margin-bottom: 0.25rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .card-owner {{
      font-size: 0.78rem;
      color: var(--muted);
      margin-bottom: 0.6rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .card-desc {{
      font-size: 0.78rem;
      color: var(--muted);
      line-height: 1.5;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
      margin-bottom: 0.75rem;
    }}

    .card-tags {{
      display: flex;
      gap: 0.4rem;
      flex-wrap: wrap;
      margin-bottom: 0.6rem;
    }}

    .card-actions {{
      display: flex;
      gap: 0.4rem;
      flex-wrap: wrap;
      margin-top: 0.5rem;
    }}

    .card-action-btn {{
      font-family: 'DM Mono', monospace;
      font-size: 0.62rem;
      padding: 0.25rem 0.6rem;
      border-radius: 4px;
      text-decoration: none;
      background: var(--surface);
      border: 1px solid var(--border);
      color: var(--accent);
      transition: all 0.15s;
    }}

    .card-action-btn:hover {{
      border-color: var(--accent);
      background: rgba(200,168,75,0.1);
    }}

    .gallery-nav {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 1rem;
      padding: 0.6rem 0 0.25rem;
    }}

    .gallery-btn {{
      background: none;
      border: 1px solid var(--border);
      color: var(--text);
      width: 2rem;
      height: 2rem;
      border-radius: 6px;
      cursor: pointer;
      font-size: 1.1rem;
      transition: all 0.15s;
    }}

    .gallery-btn:hover {{ border-color: var(--accent); color: var(--accent); }}

    .gallery-count {{
      font-family: 'DM Mono', monospace;
      font-size: 0.7rem;
      color: var(--muted);
    }}

    .tag {{
      font-family: 'DM Mono', monospace;
      font-size: 0.6rem;
      letter-spacing: 0.04em;
      padding: 0.15rem 0.5rem;
      border-radius: 3px;
    }}

    .tag-apk {{ background: rgba(74,188,120,0.12); color: #4abc78; border: 1px solid rgba(74,188,120,0.25); }}
    .tag-noapk {{ background: rgba(224,92,58,0.1); color: var(--accent2); border: 1px solid rgba(224,92,58,0.2); }}
    .tag-cam {{ background: rgba(200,168,75,0.1); color: var(--accent); border: 1px solid rgba(200,168,75,0.2); }}
    .tag-loc {{ background: rgba(100,160,255,0.1); color: #64a0ff; border: 1px solid rgba(100,160,255,0.2); }}

    /* ── Modal ── */
    .modal-overlay {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.75);
      z-index: 100;
      backdrop-filter: blur(4px);
      padding: 2rem;
      overflow-y: auto;
    }}

    .modal-overlay.open {{ display: flex; align-items: flex-start; justify-content: center; }}

    .modal {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      width: 100%;
      max-width: 760px;
      overflow: hidden;
      margin: auto;
    }}

    .modal-header {{
      padding: 1.5rem;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 1rem;
    }}

    .modal-title {{
      font-family: 'Syne', sans-serif;
      font-size: 1.5rem;
      font-weight: 800;
    }}

    .modal-close {{
      background: none;
      border: 1px solid var(--border);
      color: var(--muted);
      width: 2rem;
      height: 2rem;
      border-radius: 6px;
      cursor: pointer;
      font-size: 1rem;
      flex-shrink: 0;
      transition: all 0.15s;
    }}

    .modal-close:hover {{ border-color: var(--accent2); color: var(--accent2); }}

    .modal-body {{
      padding: 1.5rem;
      display: grid;
      grid-template-columns: 180px 1fr;
      gap: 1.5rem;
    }}

    @media (max-width: 560px) {{
      .modal-body {{ grid-template-columns: 1fr; }}
    }}

    .modal-img {{
      width: 100%;
      border-radius: 8px;
      border: 1px solid var(--border);
      object-fit: cover;
      object-position: top;
    }}

    .modal-img-placeholder {{
      width: 100%;
      aspect-ratio: 9/16;
      background: var(--card-bg);
      border-radius: 8px;
      border: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--muted);
      font-family: 'DM Mono', monospace;
      font-size: 0.7rem;
    }}

    .modal-info {{ display: flex; flex-direction: column; gap: 1rem; }}

    .modal-field label {{
      font-family: 'DM Mono', monospace;
      font-size: 0.62rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--muted);
      display: block;
      margin-bottom: 0.25rem;
    }}

    .modal-field p {{
      font-size: 0.875rem;
      line-height: 1.6;
      color: var(--text);
      white-space: pre-wrap;
    }}

    .modal-actions {{
      padding: 1.25rem 1.5rem;
      border-top: 1px solid var(--border);
      display: flex;
      gap: 0.75rem;
      flex-wrap: wrap;
    }}

    .btn {{
      font-family: 'DM Mono', monospace;
      font-size: 0.72rem;
      padding: 0.5rem 1rem;
      border-radius: 6px;
      text-decoration: none;
      cursor: pointer;
      transition: all 0.15s;
      border: 1px solid transparent;
    }}

    .btn-primary {{
      background: var(--accent);
      color: #000;
      font-weight: 500;
    }}

    .btn-primary:hover {{ background: #d4b55a; }}

    .btn-secondary {{
      background: none;
      border-color: var(--border);
      color: var(--muted);
    }}

    .btn-secondary:hover {{ border-color: var(--accent); color: var(--accent); }}

    .no-results {{
      text-align: center;
      padding: 5rem;
      color: var(--muted);
      font-family: 'DM Mono', monospace;
      font-size: 0.85rem;
    }}

    footer {{
      text-align: center;
      padding: 2rem;
      font-family: 'DM Mono', monospace;
      font-size: 0.7rem;
      color: var(--muted);
      border-top: 1px solid var(--border);
    }}
  </style>
</head>
<body>

  <header>
    <div class="header-label">COMP3130 · S1 2026 · Unofficial</div>
    <h1>App <span>Gallery</span></h1>
    <div class="header-meta">Generated {generated} · {len(slim)} submissions</div>
    <div class="header-links">
      <a href="index.html">← Table view</a>
    </div>
  </header>

  <div class="controls">
    <div class="search-wrap">
      <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
      </svg>
      <input type="text" id="search" placeholder="Search by name or owner..." />
    </div>
    <div class="filter-btns">
      <button class="filter-btn active" data-filter="all">All</button>
      <button class="filter-btn" data-filter="apk">APK Ready</button>
      <button class="filter-btn" data-filter="no-apk">No APK</button>
    </div>
    <div class="stats">Showing <span id="count">{len(slim)}</span> of {len(slim)}</div>
  </div>

  <div class="grid" id="grid"></div>
  <div class="no-results" id="no-results" style="display:none">No apps match your search.</div>

  <!-- Modal -->
  <div class="modal-overlay" id="modal-overlay">
    <div class="modal" id="modal">
      <div class="modal-header">
        <div class="modal-title" id="modal-title"></div>
        <button class="modal-close" onclick="closeModal()">✕</button>
      </div>
      <div class="modal-body">
        <div id="modal-img-wrap"></div>
        <div class="modal-info" id="modal-info"></div>
      </div>
      <div class="modal-actions" id="modal-actions"></div>
    </div>
  </div>

  <footer>Unofficial student-made directory · Not affiliated with or endorsed by Macquarie University</footer>

  <script>
    const APPS = {apps_json};

    let filter = 'all';
    let query = '';

    function filtered() {{
      return APPS.filter(app => {{
        const matchFilter = filter === 'all' || (filter === 'apk' && app.hasApk) || (filter === 'no-apk' && !app.hasApk);
        const q = query.toLowerCase();
        const matchQuery = !q || app.name.toLowerCase().includes(q) || app.owner.toLowerCase().includes(q) || app.email.toLowerCase().includes(q);
        return matchFilter && matchQuery;
      }});
    }}

    function cleanText(str) {{
      return (str || '').replace(/\*\*/g, '').replace(/#+\s/g, '').replace(/\\n/g, ' ').trim();
    }}

    function render() {{
      const results = filtered();
      const grid = document.getElementById('grid');
      const noResults = document.getElementById('no-results');
      document.getElementById('count').textContent = results.length;

      if (results.length === 0) {{
        grid.innerHTML = '';
        noResults.style.display = 'block';
        return;
      }}

      noResults.style.display = 'none';
      grid.innerHTML = results.map((app, i) => {{
        const img = app.screenshots && app.screenshots.length
          ? `<img class="card-img" src="${{app.screenshots[0]}}" alt="${{app.name}}" loading="lazy" onerror="this.parentElement.innerHTML='<div class=\'card-img-placeholder\'>no screenshot</div>'">`
          : `<div class="card-img-placeholder">no screenshot</div>`;
        const tags = [
          app.hasApk ? `<span class="tag tag-apk">APK</span>` : `<span class="tag tag-noapk">NO APK</span>`,
          app.usesCamera ? `<span class="tag tag-cam">📷 camera</span>` : '',
          app.usesLocation ? `<span class="tag tag-loc">📍 location</span>` : '',
        ].filter(Boolean).join('');
        const cardActions = [
          `<a class="card-action-btn" href="http://3.104.146.108/app/${{app.id}}" target="_blank" onclick="event.stopPropagation()">Listing ↗</a>`,
          app.hasApk ? `<a class="card-action-btn" href="comp3130-apks/${{app.slug}}.apk" download onclick="event.stopPropagation()">⬇ APK</a>` : '',
          app.repo ? `<a class="card-action-btn" href="${{app.repo}}" target="_blank" onclick="event.stopPropagation()">GitHub ↗</a>` : '',
        ].filter(Boolean).join('');
        return `
          <div class="card" style="animation-delay:${{i*0.03}}s" onclick="openModal(${{JSON.stringify(app).replace(/"/g, '&quot;')}})">
            ${{img}}
            <div class="card-body">
              <div class="card-name">${{app.name || '—'}}</div>
              <div class="card-owner">${{app.owner}}</div>
              <div class="card-desc">${{cleanText(app.description) || 'No description.'}}</div>
              <div class="card-tags">${{tags}}</div>
              <div class="card-actions">${{cardActions}}</div>
            </div>
          </div>`;
      }}).join('');
    }}

    function openModal(app) {{
      document.getElementById('modal-title').textContent = app.name;

      const imgWrap = document.getElementById('modal-img-wrap');
      if (app.screenshots && app.screenshots.length) {{
        const total = app.screenshots.length;
        let current = 0;
        function galleryHTML(idx) {{
          return `
            <img class="modal-img" src="${{app.screenshots[idx]}}" alt="${{app.name}} screenshot ${{idx+1}}">
            ${{total > 1 ? `
            <div class="gallery-nav">
              <button class="gallery-btn" onclick="(function(){{
                current = (current - 1 + ${{total}}) % ${{total}};
                document.getElementById('modal-img-wrap').innerHTML = galleryHTML(current);
              }})()" ${{idx === 0 ? 'style=\"opacity:0.3\"' : ''}}>‹</button>
              <span class="gallery-count">${{idx+1}} / ${{total}}</span>
              <button class="gallery-btn" onclick="(function(){{
                current = (current + 1) % ${{total}};
                document.getElementById('modal-img-wrap').innerHTML = galleryHTML(current);
              }})()" ${{idx === total-1 ? 'style=\"opacity:0.3\"' : ''}}>›</button>
            </div>` : ''}}
          `;
        }}
        imgWrap.innerHTML = galleryHTML(0);
        window.galleryHTML = galleryHTML;
        window.current = current;
      }} else {{
        imgWrap.innerHTML = `<div class="modal-img-placeholder">no screenshot</div>`;
      }}

      const info = document.getElementById('modal-info');
      info.innerHTML = `
        <div class="modal-field"><label>Owner</label><p>${{app.owner}} · ${{app.email}}</p></div>
        <div class="modal-field"><label>Description</label><p>${{cleanText(app.description) || '—'}}</p></div>
        ${{app.instructions ? `<div class="modal-field"><label>Test Instructions</label><p>${{cleanText(app.instructions)}}</p></div>` : ''}}
        <div class="modal-field"><label>Data &amp; Permissions</label><p>${{[
          app.collectsPersonalInfo ? '👤 Collects personal info' : '',
          app.usesCamera ? '📷 Uses camera' : '',
          app.usesLocation ? '📍 Uses location' : '',
        ].filter(Boolean).join(' · ') || 'None declared'}}</p></div>
        <div class="modal-field"><label>Screenshots</label><p>${{app.imageCount}} uploaded</p></div>
      `;

      const actions = document.getElementById('modal-actions');
      actions.innerHTML = `
        <a class="btn btn-secondary" href="http://3.104.146.108/app/${{app.id}}" target="_blank">Listing ↗</a>
        ${{app.hasApk ? `<a class="btn btn-secondary" href="comp3130-apks/${{app.slug}}.apk" download>⬇ Download APK</a>` : ''}}
        ${{app.repo ? `<a class="btn btn-secondary" href="${{app.repo}}" target="_blank">GitHub ↗</a>` : ''}}
      `;

      document.getElementById('modal-overlay').classList.add('open');
      document.body.style.overflow = 'hidden';
    }}

    function closeModal() {{
      document.getElementById('modal-overlay').classList.remove('open');
      document.body.style.overflow = '';
    }}

    document.getElementById('modal-overlay').addEventListener('click', e => {{
      if (e.target === document.getElementById('modal-overlay')) closeModal();
    }});

    document.addEventListener('keydown', e => {{
      if (e.key === 'Escape') closeModal();
    }});

    document.getElementById('search').addEventListener('input', e => {{
      query = e.target.value;
      render();
    }});

    document.querySelectorAll('.filter-btn').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        filter = btn.dataset.filter;
        render();
      }});
    }});

    render();
  </script>
</body>
</html>"""

with open("enhanced.html", "w") as f:
    f.write(html)

print("enhanced.html saved in current directory.")
