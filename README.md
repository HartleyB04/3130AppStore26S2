# COMP3130 App Directory

An unofficial student-made directory of app submissions for COMP3130 Mobile Application Development (S1 2026).

> **Not affiliated with or endorsed by Macquarie University.**

## What it does

The official app store only returns a random subset of ~10 listings per request, making it hard to find a specific student's submission. This directory scrapes all available listings and presents them in a searchable, filterable table with direct links to each app's listing page.

- Search by app name, owner name, or email
- Filter by APK availability
- Direct links to each listing and GitHub repo

## Usage

### 1. Set up the environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install requests
```

### 2. Add your token

Open `fetch_apps.py` and replace `YOUR_TOKEN_HERE` with a valid Bearer token from the app store API.

### 3. Run the script

```bash
python3 fetch_apps.py
```

The script hammers the API endpoint and deduplicates results by ID, stopping automatically once no new apps have been found for 10 consecutive requests. An `index.html` is generated in the current directory.

### 4. Push to GitHub Pages

```bash
git add index.html
git commit -m "update listings"
git push
```

The site will be live at `https://yourusername.github.io/repo-name`.

## Notes

- Tokens expire after ~7 days — you'll need to refresh it from the app store before re-running
- Re-run after the submission deadline to capture any late submissions
- Listings without an APK are flagged in the table
