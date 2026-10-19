#!/usr/bin/env python3
"""
Syncs the active Daily Coding Challenges for:
  1. LeetCode POTD -> data/daily.json, index.html
  2. GeeksforGeeks POTD -> data/gfg.json, gfg.html, gfg/index.html
"""

import html
import json
import os
import shutil
import ssl
import sys
import urllib.request
from datetime import datetime, timezone

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATE_PATH = os.path.join(ROOT_DIR, "template.html")
INDEX_PATH = os.path.join(ROOT_DIR, "index.html")
DATA_PATH = os.path.join(ROOT_DIR, "data", "daily.json")

TEMPLATE_GFG_PATH = os.path.join(ROOT_DIR, "template-gfg.html")
GFG_HTML_PATH = os.path.join(ROOT_DIR, "gfg.html")
GFG_DIR = os.path.join(ROOT_DIR, "gfg")
GFG_DIR_INDEX = os.path.join(GFG_DIR, "index.html")
GFG_DATA_PATH = os.path.join(ROOT_DIR, "data", "gfg.json")

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

# ----------------- LEETCODE -----------------

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

def sync_leetcode(synced_at):
    print("\n--- Syncing LeetCode POTD ---")
    data = None
    try:
        data = fetch_from_leetcode()
        print("[OK] Fetched from LeetCode GraphQL API.")
    except Exception as e:
        print(f"Warning: LeetCode direct fetch failed: {e}")
        print("Attempting fallback mirror...")
        try:
            data = fetch_from_mirror()
            print("[OK] Fetched from mirror API.")
        except Exception as e2:
            print(f"Error: Fallback mirror also failed: {e2}", file=sys.stderr)
            return

    data["syncedAt"] = synced_at
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved {DATA_PATH}")

    if os.path.exists(TEMPLATE_PATH):
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
        print(f"LeetCode Synced: {data['frontendId']}. {data['title']} [{data['difficulty']}] -> {data['url']}")

# ----------------- GEEKSFORGEEKS -----------------

def fetch_from_gfg():
    endpoints = [
        "https://practiceapi.geeksforgeeks.org/api/vr/problems-of-day/problem/today/",
        "https://practiceapi.geeksforgeeks.org/api/v1/problems-of-day/problem/today/",
        "https://practiceapi.geeksforgeeks.org/api/latest/problems-of-day/problem/today/"
    ]
    ctx = create_ssl_context()
    for url in endpoints:
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "Referer": "https://www.geeksforgeeks.org/"
                }
            )
            with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    tags = data.get("tags", {}).get("topic_tags", [])
                    return {
                        "date": data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
                        "id": data.get("id"),
                        "problemId": data.get("problem_id"),
                        "title": data.get("problem_name", "GeeksforGeeks POTD"),
                        "url": data.get("problem_url", "https://www.geeksforgeeks.org/problem-of-the-day"),
                        "difficulty": data.get("difficulty", "Medium"),
                        "tags": tags
                    }
        except Exception as e:
            print(f"Warning: GFG fetch from {url} failed: {e}")
            continue
    raise RuntimeError("All GFG endpoints failed")

def sync_gfg(synced_at):
    print("\n--- Syncing GeeksforGeeks POTD ---")
    data = None
    try:
        data = fetch_from_gfg()
        print("[OK] Fetched from GeeksforGeeks Practice API.")
    except Exception as e:
        print(f"Error: Could not fetch GFG POTD: {e}", file=sys.stderr)
        return

    data["syncedAt"] = synced_at
    os.makedirs(os.path.dirname(GFG_DATA_PATH), exist_ok=True)

    with open(GFG_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved {GFG_DATA_PATH}")

    if os.path.exists(TEMPLATE_GFG_PATH):
        with open(TEMPLATE_GFG_PATH, "r", encoding="utf-8") as f:
            template = f.read()

        diff_class = data["difficulty"].lower()
        escaped_title = html.escape(data["title"])

        tags_html = "".join([f'<span class="pill tag">{html.escape(t)}</span>' for t in data.get("tags", [])[:3]])

        rendered = (
            template
            .replace("__TITLE__", escaped_title)
            .replace("__DIFFICULTY__", html.escape(data["difficulty"]))
            .replace("__DIFFICULTY_CLASS__", diff_class)
            .replace("__URL__", data["url"])
            .replace("__DATE__", data["date"][:10])
            .replace("__TAGS_HTML__", tags_html)
            .replace("__SYNCED_AT__", synced_at)
        )

        with open(GFG_HTML_PATH, "w", encoding="utf-8") as f:
            f.write(rendered)
        print(f"[OK] Generated {GFG_HTML_PATH}")

        # Also write to gfg/index.html so /gfg works cleanly
        os.makedirs(GFG_DIR, exist_ok=True)
        shutil.copy2(GFG_HTML_PATH, GFG_DIR_INDEX)
        print(f"[OK] Copied to {GFG_DIR_INDEX}")
        print(f"GFG Synced: {data['title']} [{data['difficulty']}] -> {data['url']}")

# ----------------- MAIN -----------------

def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    now_utc = datetime.now(timezone.utc)
    synced_at = now_utc.strftime("%Y-%m-%d %H:%M UTC")

    sync_leetcode(synced_at)
    sync_gfg(synced_at)

if __name__ == "__main__":
    main()
