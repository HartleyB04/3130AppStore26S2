# COMP3130 App Directory

An unofficial student-made directory of app submissions for COMP3130 Mobile Application Development (S1 2026).

> **Not affiliated with or endorsed by Macquarie University.**

**Live site:** https://hartleyB04.github.io/3130AppStore26S2

## What it does

The official app store only returns a random subset of ~10 listings per request, making it hard to find a specific student's submission. This directory scrapes all available listings and presents them in a searchable, filterable table with direct links to each app's listing page.

- Search by app name, owner name, or email
- Filter by APK availability
- Direct links to each listing and GitHub repo

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/hartleyB04/3130AppStore26S2.git
cd 3130AppStore26S2
```

### 2. Create a virtual environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Get your Bearer token

1. Go to the COMP3130 App Store and log in
2. Open DevTools (`Cmd+Option+I` on Mac, `F12` on Windows)
3. Go to the **Network** tab
4. Refresh the page
5. Find the request to `api/app`
6. Click it and open the **Headers** tab
7. Copy the value after `Authorization: Bearer`

### 4. Create a `.env` file

```
COMP3130_TOKEN=your_token_here
```

> Never commit or share this file — it's already in `.gitignore`

---

## Scripts

### `fetch_app.py` — builds the searchable table

```bash
python3 fetch_app.py
```

Scrapes all app listings and generates `index.html`. Run this first. Re-run after the submission deadline to catch late submissions.

### `fetch_full.py` — builds the enhanced gallery

```bash
python3 fetch_full.py
```

Fetches full details for every app, downloads all screenshots into `comp3130-screenshots/`, and generates `enhanced.html`. Requires `index.html` to exist first.

### `download_apks.py` — downloads all APKs

```bash
python3 download_apks.py
```

Downloads all APKs into `comp3130-apks/`. Requires `index.html` to exist first. Skips files already downloaded.

---

## Viewing locally

Open `index.html` or `enhanced.html` with Live Server in VS Code, or run:

```bash
python3 -m http.server 8080
```

Then go to `http://localhost:8080` or `http://localhost:8080/enhanced.html`.

Anyone on the same network can access it at `http://your-ip:8080`. Find your IP with:

```bash
ipconfig getifaddr en0
```

> APK downloads and screenshot previews only work when serving locally — they are not available on the GitHub Pages site.

---

## Notes

- `comp3130-screenshots/` and `comp3130-apks/` are gitignored — local only
- The GitHub Pages site serves `index.html` only (table view, no screenshots or APK downloads)