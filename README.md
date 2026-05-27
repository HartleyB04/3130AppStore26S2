# COMP3130 App Directory

An unofficial student-made directory of app submissions for COMP3130 Mobile Application Development (S1 2026).

> **Not affiliated with or endorsed by Macquarie University.**

**Live site:** https://hartleyB04.github.io/3130AppStore26S2

## What it does

The official app store only returns a random subset of ~10 listings per request, making it hard to find a specific student's submission. This directory scrapes all available listings and presents them in a searchable, filterable table with direct links to each app's listing page.

- Search by app name, owner name, or email
- Filter by APK availability
- Direct links to each listing and GitHub repo

## Usage

### 1. Clone the repo

```bash
git clone https://github.com/hartleyB04/3130AppStore26S2.git
cd 3130AppStore26S2
```

### 2. Set up the environment

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
7. Copy the value after `Authorization: Bearer` — this is your token

### 4. Add your token

Create a `.env` file in the same folder as the script:

```
COMP3130_TOKEN=your_token_here
```

> Never commit this file — it's already in `.gitignore`.

### 5. Run the script

```bash
python3 fetch_app.py
```

The script hammers the API endpoint and deduplicates results by ID, stopping automatically once no new apps have been found for 10 consecutive requests. An `index.html` is generated in the current directory.

## Notes

- Tokens expire after ~7 days — you'll need to refresh it from the app store before re-running
- Re-run after the submission deadline to capture any late submissions
- Listings without an APK are flagged in the table

## Local APK Server

To serve APKs locally over the network:

1. Download the APKs first:
```bash
   python3 download_apks.py
```
2. Start the local server from the `App Store` folder:
```bash
   python3 -m http.server 8080
```
3. Find your local IP:
```bash
   ipconfig getifaddr en0
```
4. Anyone on the same network can go to `http://your-ip:8080` and use the directory — the ⬇ APK buttons will work as direct downloads.

> Download buttons only work when the local server is running. They will not work on the GitHub Pages site.
