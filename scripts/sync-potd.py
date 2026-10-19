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

TOPIC_ICONS = {
    "dynamic programming": ("#c084fc", '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/><path d="M15 21V9"/></svg>'),
    "dp": ("#c084fc", '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/><path d="M15 21V9"/></svg>'),
    "stack": ("#38bdf8", '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>'),
    "queue": ("#2dd4bf", '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/><path d="M12 5l7 7-7 7"/><circle cx="5" cy="12" r="2"/></svg>'),
    "graph": ("#f472b6", '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="6" cy="6" r="3"/><circle cx="18" cy="8" r="3"/><circle cx="12" cy="18" r="3"/><line x1="8.5" y1="7" x2="15.5" y2="7.5"/><line x1="7.5" y1="8.5" x2="10.5" y2="15.5"/><line x1="16.5" y1="10" x2="13.5" y2="16"/></svg>'),
    "tree": ("#4ade80", '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="5" r="3"/><circle cx="6" cy="19" r="3"/><circle cx="18" cy="19" r="3"/><path d="M12 8v4"/><path d="M12 12l-4 4"/><path d="M12 12l4 4"/></svg>'),
    "array": ("#60a5fa", '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="6" width="20" height="12" rx="2"/><line x1="8" y1="6" x2="8" y2="18"/><line x1="14" y1="6" x2="14" y2="18"/><line x1="20" y1="6" x2="20" y2="18"/></svg>'),
    "sorting": ("#a78bfa", '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>'),
    "greedy": ("#e879f9", '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 3h12l4 6-10 12L2 9l4-6z"/><path d="M2 9h20"/></svg>'),
    "binary search": ("#34d399", '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>'),
    "dfs": ("#38bdf8", '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v18"/><path d="M18 15l-6 6-6-6"/></svg>'),
    "bfs": ("#38bdf8", '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3a9 9 0 0 0 0 18"/><path d="M12 7a5 5 0 0 0 0 10"/><path d="M12 11a1 1 0 0 0 0 2"/></svg>'),
    "string": ("#fbbf24", '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>'),
    "hash": ("#fb7185", '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/></svg>'),
    "two pointers": ("#818cf8", '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8L22 12L18 16"/><path d="M2 12H22"/><path d="M6 16L2 12L6 8"/></svg>'),
    "math": ("#facc15", '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="12" x2="20" y2="12"/><line x1="12" y1="4" x2="12" y2="20"/></svg>')
}

def render_tags_html(tags):
    html_out = []
    for tag in tags[:4]:
        name = tag if isinstance(tag, str) else tag.get("name", "")
        t_lower = name.lower()
        color = "#94a3b8"
        icon = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/></svg>'
        for k, v in TOPIC_ICONS.items():
            if k in t_lower:
                color, icon = v
                break
        html_out.append(f'<span class="pill topic-tag" style="--tag-color:{color}">{icon}<span>{html.escape(name)}</span></span>')
    return "".join(html_out)

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

    with open(DATA_LEETCODE_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    with open(DATA_DAILY_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[LeetCode] Saved {DATA_LEETCODE_JSON}")

    if not os.path.exists(TEMPLATE_LEETCODE):
        print(f"[LeetCode] Error: Template not found at {TEMPLATE_LEETCODE}", file=sys.stderr)
        return

    with open(TEMPLATE_LEETCODE, "r", encoding="utf-8") as f:
        template = f.read()

    tags_html = render_tags_html(data.get("tags", []))
    tags_json = json.dumps(data.get("tags", []))

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
        .replace("__TAGS_JSON__", tags_json)
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

    tags_html = render_tags_html(data.get("tags", []))
    tags_json = json.dumps(data.get("tags", []))

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
        .replace("__TAGS_JSON__", tags_json)
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
