#!/usr/bin/env python3
"""
Syncs the active LeetCode Daily Challenge.
Fetches from LeetCode GraphQL with automatic fallback to community mirror.
Generates:
  - data/daily.json
  - index.html (from template.html)
"""

import html
import json
import os
import ssl
import sys
import urllib.request
from datetime import datetime, timezone

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATE_PATH = os.path.join(ROOT_DIR, "template.html")
INDEX_PATH = os.path.join(ROOT_DIR, "index.html")
DATA_PATH = os.path.join(ROOT_DIR, "data", "daily.json")

GRAPHQL_QUERY = """
query questionOfToday {
  activeDailyCodingChallengeQuestion {
    date
    link
    question {
      questionFrontendId
      title
      titleSlug
      difficulty
    }
  }
}
"""

def create_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def fetch_from_leetcode():
    req = urllib.request.Request(
        "https://leetcode.com/graphql",
        headers={
            "Content-Type": "application/json",
            "Referer": "https://leetcode.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        },
        data=json.dumps({"query": GRAPHQL_QUERY}).encode("utf-8")
    )
    ctx = create_ssl_context()
    with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} from leetcode.com/graphql")
        body = json.loads(resp.read().decode("utf-8"))
        challenge = body.get("data", {}).get("activeDailyCodingChallengeQuestion")
        if not challenge or "question" not in challenge:
            raise ValueError("Invalid response structure from LeetCode GraphQL")
        q = challenge["question"]
        return {
            "date": challenge["date"],
            "frontendId": q["questionFrontendId"],
            "title": q["title"],
            "titleSlug": q["titleSlug"],
            "difficulty": q["difficulty"],
            "url": f"https://leetcode.com/problems/{q['titleSlug']}/"
        }

def fetch_from_mirror():
    req = urllib.request.Request(
        "https://alfa-leetcode-api.onrender.com/daily",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    ctx = create_ssl_context()
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} from mirror API")
        data = json.loads(resp.read().decode("utf-8"))
        return {
            "date": data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
            "frontendId": str(data.get("questionFrontendId") or data.get("questionId")),
            "title": data.get("questionTitle", ""),
            "titleSlug": data.get("titleSlug", ""),
            "difficulty": data.get("difficulty", "Medium"),
            "url": data.get("questionLink") or f"https://leetcode.com/problems/{data.get('titleSlug')}/"
        }

def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("Fetching today's LeetCode Daily Challenge...")
    data = None
    try:
        data = fetch_from_leetcode()
        print("[OK] Successfully fetched from LeetCode GraphQL API.")
    except Exception as e:
        print(f"Warning: LeetCode direct fetch failed: {e}")
        print("Attempting fallback mirror...")
        try:
            data = fetch_from_mirror()
            print("[OK] Successfully fetched from mirror API.")
        except Exception as e2:
            print(f"Error: Fallback mirror also failed: {e2}", file=sys.stderr)
            sys.exit(1)

    now_utc = datetime.now(timezone.utc)
    synced_at = now_utc.strftime("%Y-%m-%d %H:%M UTC")
    data["syncedAt"] = synced_at

    # Ensure data directory exists
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)

    # 1. Write data/daily.json
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved {DATA_PATH}")

    # 2. Render index.html from template.html
    if not os.path.exists(TEMPLATE_PATH):
        print(f"Error: Template not found at {TEMPLATE_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    diff_class = data["difficulty"].lower()
    escaped_title = html.escape(data["title"])

    rendered = (
        template
        .replace("__FRONTEND_ID__", html.escape(data["frontendId"]))
        .replace("__TITLE__", escaped_title)
        .replace("__SLUG__", data["titleSlug"])
        .replace("__DIFFICULTY__", html.escape(data["difficulty"]))
        .replace("__DIFFICULTY_CLASS__", diff_class)
        .replace("__URL__", data["url"])
        .replace("__DATE__", data["date"])
        .replace("__SYNCED_AT__", synced_at)
    )

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(rendered)
    print(f"[OK] Generated {INDEX_PATH}")
    print(f"\nSynced Challenge: {data['frontendId']}. {data['title']} [{data['difficulty']}] -> {data['url']}")

if __name__ == "__main__":
    main()
