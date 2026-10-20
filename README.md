# Daily Coding Challenge Redirects (LeetCode, GFG & takeUforward TUF+)

Lightning-fast, timezone-aware terminal redirect pages for **LeetCode Problem of the Day**, **GeeksforGeeks Problem of the Day**, and **takeUforward (TUF+) Problem of the Day**.

---

## 🌐 Live URLs

| Platform | Live Redirect URL | Reset Time |
| :--- | :--- | :--- |
| **LeetCode POTD** | 👉 **[https://codesmith17.github.io/daily-potd-redirect/](https://codesmith17.github.io/daily-potd-redirect/)** | `00:00 UTC` (05:30 AM IST) |
| **GeeksforGeeks POTD** | 👉 **[https://codesmith17.github.io/daily-potd-redirect/gfg](https://codesmith17.github.io/daily-potd-redirect/gfg)** | `00:00 IST` (18:30 UTC) |
| **takeUforward (TUF+) POTD** | 👉 **[https://codesmith17.github.io/daily-potd-redirect/tuf](https://codesmith17.github.io/daily-potd-redirect/tuf)** | `00:00 IST` (18:30 UTC) |

Clean subpaths are also available:
- LeetCode: `/leetcode` or root `/`
- GeeksforGeeks: `/gfg`
- takeUforward (TUF+): `/tuf`

Bookmark either link in your browser to immediately jump into today's problem!

---

## ⌨️ Interactive Controls & Terminal Shortcuts

- `[Space]` or `[Enter]` : Launch and open challenge immediately
- `[C]` or `[Esc]` : Cancel auto-redirect countdown
- `[R]` : Refresh and check challenge status
- Live visual countdown timer with pulsing glow based on challenge difficulty (`Easy` = Emerald, `Medium` = Amber, `Hard` = Rose) and custom handcrafted SVG topic badges (DP, Stack, Queue, Graph, Tree, Array, Sorting, Greedy, Binary Search, DFS, BFS, Math, String, Hash).

---

## ⏱️ When Does the Data Update?

The `data/` directory and HTML pages are synced automatically:

1. **LeetCode POTD**:
   - Resets daily at **00:00:00 UTC** (05:30:00 AM IST).
   - Auto-sync triggers at `00:00 UTC`, `00:15 UTC`, and `00:30 UTC`.
2. **GeeksforGeeks & takeUforward (TUF+) POTD**:
   - Reset daily at **00:00:00 IST** (18:30:00 UTC).
   - Auto-sync triggers at `18:30 UTC` and `18:45 UTC`.
3. **Continuous Hourly Fallback**:
   - Runs every hour (`cron: "0 * * * *"`) to ensure zero stale links even if GitHub's shared runner queues experience delays.
4. **Client-Side Live Verification**:
   - When opened in a browser, the frontend compares the bundled date against your local date/time and fetches fresh data (`data/leetcode.json`, `data/gfg.json`, or `data/tuf.json`) with cache-busting so you are never redirected to stale data.

---

## 📁 Modular Golang Automation Architecture

The sync engine is built using standard library **Go (Golang)** with dedicated modules for each platform and zero external dependencies:

```
daily-potd-redirect/
├── .github/
│   └── workflows/
│       └── sync-potd.yml               # Multi-schedule sync workflow with Go 1.23
├── scripts/
│   ├── main.go                         # Entrypoint, topic SVG icon registry & CLI runner
│   ├── leetcode.go                     # LeetCode GraphQL & community mirror fetcher + compiler
│   ├── gfg.go                          # GeeksforGeeks Practice API fetcher + compiler
│   └── tuf.go                          # takeUforward (TUF+) API fetcher + compiler
├── go.mod                              # Go module definition (stdlib only)
├── data/
│   ├── leetcode.json                   # Standardized LeetCode POTD JSON
│   ├── gfg.json                        # Standardized GeeksforGeeks POTD JSON
│   ├── tuf.json                        # Standardized takeUforward POTD JSON
├── templates/
│   └── potd.html                       # Unified dynamic terminal template with auto-theme switching
├── leetcode/
│   └── index.html                      # Clean /leetcode path
├── gfg/
│   └── index.html                      # Clean /gfg path
├── tuf/
│   └── index.html                      # Clean /tuf path
├── index.html                          # Root redirect (LeetCode POTD)
├── .gitignore
└── README.md
```

---

## 📊 Standardized Data Schema

All platform JSON files (`data/leetcode.json`, `data/gfg.json`, `data/tuf.json`) strictly adhere to the same schema:

```json
{
  "platform": "leetcode",
  "id": "2089",
  "title": "Find Target Indices After Sorting Array",
  "slug": "find-target-indices-after-sorting-array",
  "difficulty": "Easy",
  "difficultyClass": "easy",
  "url": "https://leetcode.com/problems/find-target-indices-after-sorting-array/",
  "date": "2026-10-19",
  "tags": ["Array", "Binary Search", "Sorting"],
  "syncedAt": "2026-10-19 05:39 UTC"
}
```

---

## 🛠️ GitHub Repository & Pages

- **Repository**: [https://github.com/codesmith17/daily-potd-redirect](https://github.com/codesmith17/daily-potd-redirect)
- **Live Pages**: [https://codesmith17.github.io/daily-potd-redirect/](https://codesmith17.github.io/daily-potd-redirect/)
