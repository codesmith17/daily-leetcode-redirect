#!/usr/bin/env python3
"""
Syncs the active Daily Problem of the Day (POTD) challenges:
  1. LeetCode POTD        -> data/leetcode.json, data/daily.json, index.html, leetcode.html, leetcode/index.html
  2. GeeksforGeeks POTD  -> data/gfg.json, gfg.html, gfg/index.html
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
DATA_DIR = os.path.join(ROOT_DIR, "data")
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")

# File paths
TEMPLATE_LEETCODE = os.path.join(TEMPLATES_DIR, "leetcode.html")
TEMPLATE_GFG = os.path.join(TEMPLATES_DIR, "gfg.html")

DATA_LEETCODE_JSON = os.path.join(DATA_DIR, "leetcode.json")
DATA_DAILY_JSON = os.path.join(DATA_DIR, "daily.json")
DATA_GFG_JSON = os.path.join(DATA_DIR, "gfg.json")

INDEX_HTML = os.path.join(ROOT_DIR, "index.html")
LEETCODE_HTML = os.path.join(ROOT_DIR, "leetcode.html")
LEETCODE_DIR = os.path.join(ROOT_DIR, "leetcode")
LEETCODE_DIR_INDEX = os.path.join(LEETCODE_DIR, "index.html")

GFG_HTML = os.path.join(ROOT_DIR, "gfg.html")
GFG_DIR = os.path.join(ROOT_DIR, "gfg")
GFG_DIR_INDEX = os.path.join(GFG_DIR, "index.html")

LEETCODE_GRAPHQL_QUERY = """
query questionOfToday {
  activeDailyCodingChallengeQuestion {
    date
    link
    question {
      questionFrontendId
      title
      titleSlug
      difficulty
      topicTags {
        name
      }
    }
  }
}
"""

def create_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

# ----------------- LEETCODE SYNC -----------------

def fetch_leetcode_graphql():
    req = urllib.request.Request(
        "https://leetcode.com/graphql",
        headers={
            "Content-Type": "application/json",
            "Referer": "https://leetcode.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        },
        data=json.dumps({"query": LEETCODE_GRAPHQL_QUERY}).encode("utf-8")
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
        tags = [t["name"] for t in q.get("topicTags", [])]
        return {
            "platform": "leetcode",
            "id": str(q["questionFrontendId"]),
            "title": q["title"],
            "slug": q["titleSlug"],
            "difficulty": q["difficulty"],
            "difficultyClass": q["difficulty"].lower(),
            "url": f"https://leetcode.com/problems/{q['titleSlug']}/",
            "date": challenge["date"],
            "tags": tags
        }

def fetch_leetcode_mirror():
    req = urllib.request.Request(
        "https://alfa-leetcode-api.onrender.com/daily",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    ctx = create_ssl_context()
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} from mirror API")
        data = json.loads(resp.read().decode("utf-8"))
        tags = [t["name"] for t in data.get("topicTags", [])]
        diff = data.get("difficulty", "Medium")
        slug = data.get("titleSlug", "")
        return {
            "platform": "leetcode",
            "id": str(data.get("questionFrontendId") or data.get("questionId") or ""),
            "title": data.get("questionTitle", ""),
            "slug": slug,
            "difficulty": diff,
            "difficultyClass": diff.lower(),
            "url": data.get("questionLink") or f"https://leetcode.com/problems/{slug}/",
            "date": data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
            "tags": tags
        }

def sync_leetcode(synced_at):
    print("\n[LeetCode] Fetching Problem of the Day...")
    data = None
    try:
        data = fetch_leetcode_graphql()
        print("[LeetCode] OK - Fetched directly from LeetCode GraphQL.")
    except Exception as e:
        print(f"[LeetCode] Warning - Direct GraphQL query failed: {e}")
        print("[LeetCode] Trying mirror API fallback...")
        try:
            data = fetch_leetcode_mirror()
            print("[LeetCode] OK - Fetched from community mirror.")
        except Exception as e2:
            print(f"[LeetCode] Error - All LeetCode sources failed: {e2}", file=sys.stderr)
            return

    data["syncedAt"] = synced_at
    os.makedirs(DATA_DIR, exist_ok=True)

    # Save data/leetcode.json and alias data/daily.json
    with open(DATA_LEETCODE_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    with open(DATA_DAILY_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[LeetCode] Saved {DATA_LEETCODE_JSON}")

    # Render template
    if not os.path.exists(TEMPLATE_LEETCODE):
        print(f"[LeetCode] Error: Template not found at {TEMPLATE_LEETCODE}", file=sys.stderr)
        return

    with open(TEMPLATE_LEETCODE, "r", encoding="utf-8") as f:
        template = f.read()

    tags_html = "".join([f'<span class="pill tag">{html.escape(t)}</span>' for t in data.get("tags", [])[:3]])

    rendered = (
        template
        .replace("__ID__", html.escape(data["id"]))
        .replace("__TITLE__", html.escape(data["title"]))
        .replace("__SLUG__", data["slug"])
        .replace("__DIFFICULTY__", html.escape(data["difficulty"]))
        .replace("__DIFFICULTY_CLASS__", data["difficultyClass"])
        .replace("__URL__", data["url"])
        .replace("__DATE__", data["date"])
        .replace("__TAGS_HTML__", tags_html)
        .replace("__SYNCED_AT__", synced_at)
    )

    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(rendered)
    with open(LEETCODE_HTML, "w", encoding="utf-8") as f:
        f.write(rendered)

    os.makedirs(LEETCODE_DIR, exist_ok=True)
    shutil.copy2(INDEX_HTML, LEETCODE_DIR_INDEX)

    print(f"[LeetCode] Synced: {data['id']}. {data['title']} [{data['difficulty']}] -> {data['url']}")

# ----------------- GEEKSFORGEEKS SYNC -----------------

def fetch_gfg_api():
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
                    diff = data.get("difficulty", "Medium")
                    return {
                        "platform": "gfg",
                        "id": str(data.get("id") or data.get("problem_id") or ""),
                        "title": data.get("problem_name", "GeeksforGeeks POTD"),
                        "slug": data.get("problem_url", "").rstrip("/").split("/")[-1],
                        "difficulty": diff,
                        "difficultyClass": diff.lower(),
                        "url": data.get("problem_url", "https://www.geeksforgeeks.org/problem-of-the-day"),
                        "date": data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))[:10],
                        "tags": tags
                    }
        except Exception as e:
            print(f"[GFG] Warning: Endpoint {url} failed: {e}")
            continue
    raise RuntimeError("All GeeksforGeeks endpoints failed")

def sync_gfg(synced_at):
    print("\n[GFG] Fetching Problem of the Day...")
    data = None
    try:
        data = fetch_gfg_api()
        print("[GFG] OK - Fetched directly from GeeksforGeeks Practice API.")
    except Exception as e:
        print(f"[GFG] Error: Could not fetch GFG POTD: {e}", file=sys.stderr)
        return

    data["syncedAt"] = synced_at
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(DATA_GFG_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[GFG] Saved {DATA_GFG_JSON}")

    if not os.path.exists(TEMPLATE_GFG):
        print(f"[GFG] Error: Template not found at {TEMPLATE_GFG}", file=sys.stderr)
        return

    with open(TEMPLATE_GFG, "r", encoding="utf-8") as f:
        template = f.read()

    tags_html = "".join([f'<span class="pill tag">{html.escape(t)}</span>' for t in data.get("tags", [])[:3]])

    rendered = (
        template
        .replace("__ID__", html.escape(data["id"]))
        .replace("__TITLE__", html.escape(data["title"]))
        .replace("__SLUG__", data["slug"])
        .replace("__DIFFICULTY__", html.escape(data["difficulty"]))
        .replace("__DIFFICULTY_CLASS__", data["difficultyClass"])
        .replace("__URL__", data["url"])
        .replace("__DATE__", data["date"])
        .replace("__TAGS_HTML__", tags_html)
        .replace("__SYNCED_AT__", synced_at)
    )

    with open(GFG_HTML, "w", encoding="utf-8") as f:
        f.write(rendered)

    os.makedirs(GFG_DIR, exist_ok=True)
    shutil.copy2(GFG_HTML, GFG_DIR_INDEX)

    print(f"[GFG] Synced: {data['title']} [{data['difficulty']}] -> {data['url']}")

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
