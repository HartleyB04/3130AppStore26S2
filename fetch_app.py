import requests
import time
import json
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.environ.get("COMP3130_TOKEN")
URL = "http://3.104.146.108/api/app/"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

seen = {}
attempts = 0
consecutive_no_new = 0
MAX_NO_NEW = 15

print("Fetching... (will stop automatically when no new apps are found)")

while consecutive_no_new < MAX_NO_NEW:
    try:
        r = requests.get(URL, headers=HEADERS, timeout=10)
        data = r.json()
        results = data.get("data", [])
        new_this_round = 0
        for item in results:
            if item and item.get("id") and item["id"] not in seen:
                seen[item["id"]] = item
                new_this_round += 1

        if new_this_round == 0:
            consecutive_no_new += 1
        else:
            consecutive_no_new = 0

        attempts += 1
        print(f"  Attempt {attempts}: {len(seen)} unique apps | {consecutive_no_new}/{MAX_NO_NEW} consecutive misses", end="\r")
        time.sleep(0.2)
    except Exception as e:
        print(f"\nError on attempt {attempts}: {e}")
        attempts += 1

print(f"\n\nDone. Found {len(seen)} unique apps after {attempts} attempts.\n")

apps = sorted(seen.values(), key=lambda x: x.get("owner", {}).get("name", "").lower())

# Slim down for embedding in HTML
slim = []
for app in apps:
    owner = app.get("owner", {})
    slim.append({
        "name": app.get("name", ""),
        "owner": owner.get("name", ""),
        "email": owner.get("email", ""),
        "id": app.get("id", ""),
        "slug": app.get("slug", ""),
        "hasApk": bool(app.get("apkFile")),
        "repo": app.get("repoLink", ""),
        "description": (app.get("description", "") or "")[:200],
    })

apps_json = json.dumps(slim, indent=2)
generated = datetime.now().strftime("%d %b %Y %H:%M")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>COMP3130 App Store — S1 2026</title>
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

    header::after {{
      content: '';
      position: absolute;
      bottom: -80px; right: 10%;
      width: 250px; height: 250px;
      background: radial-gradient(circle, rgba(224,92,58,0.08) 0%, transparent 70%);
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
    }}

    .enhanced-btn {{
      display: inline-block;
      font-family: 'DM Mono', monospace;
      font-size: 0.72rem;
      letter-spacing: 0.05em;
      color: var(--accent);
      text-decoration: none;
      border: 1px solid rgba(200,168,75,0.3);
      background: rgba(200,168,75,0.08);
      padding: 0.55rem 0.9rem;
      border-radius: 6px;
      transition: all 0.15s;
    }}

    .enhanced-btn:hover {{
      background: rgba(200,168,75,0.16);
      border-color: var(--accent);
    }}

    .header-links {{
      margin-top: 1rem;
    }}

    .enhanced-btn {{
      display: inline-block;
      font-family: 'DM Mono', monospace;
      font-size: 0.72rem;
      letter-spacing: 0.05em;
      color: var(--accent);
      text-decoration: none;
      border: 1px solid rgba(200,168,75,0.3);
      background: rgba(200,168,75,0.08);
      padding: 0.55rem 0.9rem;
      border-radius: 6px;
      transition: all 0.15s;
    }}

    .enhanced-btn:hover {{
      background: rgba(200,168,75,0.16);
      border-color: var(--accent);
    }}

    .controls {{
      padding: 1.5rem 2rem;
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
      font-size: 0.9rem;
      outline: none;
      transition: border-color 0.15s;
    }}

    input[type="text"]:focus {{ border-color: var(--accent); }}
    input[type="text"]::placeholder {{ color: var(--muted); }}

    .filter-btns {{
      display: flex;
      gap: 0.5rem;
    }}

    .filter-btn {{
      background: var(--surface);
      border: 1px solid var(--border);
      color: var(--muted);
      padding: 0.5rem 1rem;
      border-radius: 6px;
      font-family: 'DM Mono', monospace;
      font-size: 0.72rem;
      letter-spacing: 0.05em;
      cursor: pointer;
      transition: all 0.15s;
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

    main {{
      padding: 1.5rem 2rem;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
    }}

    thead th {{
      font-family: 'DM Mono', monospace;
      font-size: 0.65rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
      text-align: left;
      padding: 0 1rem 0.75rem;
      border-bottom: 1px solid var(--border);
    }}

    thead th:first-child {{ padding-left: 0; width: 2.5rem; }}

    tbody tr {{
      border-bottom: 1px solid var(--border);
      transition: background 0.1s;
      animation: fadeIn 0.3s ease both;
    }}

    tbody tr:hover {{ background: var(--card-bg); }}

    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(4px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    td {{
      padding: 0.9rem 1rem;
      font-size: 0.875rem;
      vertical-align: middle;
    }}

    td:first-child {{
      padding-left: 0;
      font-family: 'DM Mono', monospace;
      font-size: 0.7rem;
      color: var(--muted);
      width: 2.5rem;
    }}

    .app-desc {{
      font-size: 0.75rem;
      color: var(--muted);
      margin-top: 0.25rem;
      max-width: 380px;
      line-height: 1.4;
    }}

    .app-name {{
      font-weight: 500;
      color: var(--text);
    }}

    .owner-name {{ color: var(--text); }}
    .owner-email {{
      font-family: 'DM Mono', monospace;
      font-size: 0.72rem;
      color: var(--muted);
      margin-top: 0.15rem;
    }}

    .apk-yes {{
      display: inline-block;
      background: rgba(74,188,120,0.12);
      color: #4abc78;
      border: 1px solid rgba(74,188,120,0.25);
      padding: 0.2rem 0.6rem;
      border-radius: 4px;
      font-family: 'DM Mono', monospace;
      font-size: 0.65rem;
      letter-spacing: 0.05em;
    }}

    .apk-no {{
      display: inline-block;
      background: rgba(224,92,58,0.1);
      color: var(--accent2);
      border: 1px solid rgba(224,92,58,0.2);
      padding: 0.2rem 0.6rem;
      border-radius: 4px;
      font-family: 'DM Mono', monospace;
      font-size: 0.65rem;
      letter-spacing: 0.05em;
    }}

    .id-cell {{
      font-family: 'DM Mono', monospace;
      font-size: 0.7rem;
      color: var(--muted);
    }}

    .copy-btn {{
      background: none;
      border: 1px solid var(--border);
      color: var(--muted);
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      font-family: 'DM Mono', monospace;
      font-size: 0.65rem;
      cursor: pointer;
      margin-left: 0.4rem;
      transition: all 0.15s;
    }}

    .copy-btn:hover {{ border-color: var(--accent); color: var(--accent); }}
    .copy-btn.copied {{ border-color: #4abc78; color: #4abc78; }}

    .download-btn {{
      display: inline-block;
      background: rgba(200,168,75,0.1);
      color: var(--accent);
      border: 1px solid rgba(200,168,75,0.3);
      padding: 0.2rem 0.6rem;
      border-radius: 4px;
      font-family: 'DM Mono', monospace;
      font-size: 0.68rem;
      text-decoration: none;
      transition: all 0.15s;
    }}

    .download-btn:hover {{
      background: rgba(200,168,75,0.2);
      border-color: var(--accent);
    }}

    .repo-link {{
      color: var(--accent);
      text-decoration: none;
      font-family: 'DM Mono', monospace;
      font-size: 0.7rem;
    }}

    .repo-link:hover {{ text-decoration: underline; }}

    .no-results {{
      text-align: center;
      padding: 4rem;
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
    <h1>App <span>Store</span></h1>
    <div class="header-meta">Generated {generated} · {len(slim)} submissions</div>
    <div class="header-links">
      <a class="enhanced-btn" href="enhanced.html">Gallery view →</a>
    </div>
  </header>

  <div class="controls">
    <div class="search-wrap">
      <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
      </svg>
      <input type="text" id="search" placeholder="Search by name, owner, email..." />
    </div>
    <div class="filter-btns">
      <button class="filter-btn active" data-filter="all">All</button>
      <button class="filter-btn" data-filter="apk">APK Only</button>
      <button class="filter-btn" data-filter="no-apk">No APK</button>
    </div>
    <div class="stats">Showing <span id="count">{len(slim)}</span> of {len(slim)}</div>
  </div>

  <main>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>App Name</th>
          <th>Owner</th>
          <th>APK</th>
          <th>Listing</th>
          <th>Download</th>
          <th>Repo</th>
        </tr>
      </thead>
      <tbody id="table-body"></tbody>
    </table>
    <div class="no-results" id="no-results" style="display:none">No apps match your search.</div>
  </main>

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

    function render() {{
      const results = filtered();
      const tbody = document.getElementById('table-body');
      const noResults = document.getElementById('no-results');
      document.getElementById('count').textContent = results.length;

      if (results.length === 0) {{
        tbody.innerHTML = '';
        noResults.style.display = 'block';
        return;
      }}

      noResults.style.display = 'none';
      tbody.innerHTML = results.map((app, i) => `
        <tr style="animation-delay: ${{i * 0.02}}s">
          <td>${{i + 1}}</td>
          <td>
            <div class="app-name">${{app.name || '—'}}</div>
            ${{app.description ? `<div class="app-desc">${{app.description.replace(/\*\*/g, '').replace(/#+\s/g, '').trim()}}...</div>` : ''}}
          </td>
          <td>
            <div class="owner-name">${{app.owner || '—'}}</div>
            <div class="owner-email">${{app.email || ''}}</div>
          </td>
          <td>${{app.hasApk ? '<span class="apk-yes">YES</span>' : '<span class="apk-no">NO</span>'}}</td>
          <td>
            <a class="repo-link" href="http://3.104.146.108/app/${{app.id}}" target="_blank">${{app.id.slice(-8)}} ↗</a>
          </td>
          <td>${{app.hasApk ? `<a class="download-btn" href="comp3130-apks/${{app.slug}}.apk" download>⬇ APK</a>` : '—'}}</td>
          <td>${{app.repo ? `<a class="repo-link" href="${{app.repo}}" target="_blank">GitHub ↗</a>` : '—'}}</td>
        </tr>
      `).join('');
    }}

    function copyId(btn, id) {{
      navigator.clipboard.writeText(id);
      btn.textContent = 'copied!';
      btn.classList.add('copied');
      setTimeout(() => {{ btn.textContent = 'copy'; btn.classList.remove('copied'); }}, 1500);
    }}

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

with open("index.html", "w") as f:
    f.write(html)

print("index.html saved in current directory.")