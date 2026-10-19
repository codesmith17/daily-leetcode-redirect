# LeetCode POTD — Daily Challenge Redirect

A lightning-fast, timezone-aware terminal redirect page for the **LeetCode Problem of the Day (POTD)**.

Inspired by [Alberto Minetti's daily-leetcode-redirect](https://github.com/albertominetti/daily-leetcode-redirect), but rebuilt from the ground up to solve the critical staleness and timezone delay bugs that plague static redirect pages.

---

## ⚡ Why Did the Original Repo Open the Wrong Link?

If you opened Alberto Minetti's redirect link a few hours ago, you were redirected to **yesterday's** problem. Here is why:

1. **GitHub Actions Schedule Delays**:
   - The original repo relies solely on a single GitHub Actions cron job scheduled at `00:05 UTC`.
   - On GitHub's free runners, scheduled workflows are placed on a shared queue and are frequently delayed by **3 to 5 hours** during peak times.
   - For example, on Oct 19, 2026, the original repo's commit was delayed until **04:29 UTC** (09:59 AM IST). Anyone visiting between midnight UTC and 10:00 AM IST was redirected to the previous day's problem.
2. **Hardcoded Static Redirect**:
   - The original page had static `<meta http-equiv="refresh">` and `<script>window.location.replace</script>` baked into the HTML. If the GitHub Actions runner was delayed, the page blindly redirected to the stale question.
3. **Aggressive CDN & Browser Caching**:
   - GitHub Pages CDN and web browsers aggressively cache static `index.html` files unless dynamic cache-busting or live API validation is performed.
4. **Timezone Misalignment**:
   - LeetCode's daily question officially resets at **00:00:00 UTC** (05:30 AM IST). Users in timezones ahead of UTC were getting stale links due to the delayed cron.

---

## 🚀 How This Project Solves It

| Feature | Original Repo | This Project |
| :--- | :--- | :--- |
| **Architecture** | Purely static HTML | **Hybrid**: Fast pre-rendered HTML + client-side live validation |
| **Cron Reliability** | 1 daily run at 00:05 UTC (often delayed 4+ hrs) | Runs at 00:00, 00:15, 00:30 UTC, plus hourly fallbacks |
| **Stale Cache Protection** | ❌ None (blind redirect) | ✅ **Detects stale data in browser** & fetches fresh POTD before redirecting |
| **Local Time Awareness** | ❌ No awareness | ✅ **Displays visitor's local time** & countdown to 00:00 UTC reset |
| **User Controls** | ❌ Hard immediate redirect | ✅ Animated progress bar, Pause/Resume, & instant problem link |
| **Zero External UI Dependencies** | ✅ Pure CSS/JS | ✅ Pure CSS/JS (terminal aesthetic, responsive dark mode) |

---

## 📂 Project Structure

```
daily-leetcode-redirect/
├── .github/
│   └── workflows/
│       └── update-daily-challenge.yml   # Multi-schedule sync workflow
├── data/
│   └── daily.json                      # Machine-readable current POTD JSON
├── scripts/
│   └── sync-daily-challenge.py         # Resilient Python sync script
├── template.html                       # HTML template with live verification
├── index.html                          # Deployed page (auto-built & live-verified)
├── .gitignore
└── README.md
```

---

## 🌐 Live URL

👉 **[https://codesmith17.github.io/daily-leetcode-redirect/](https://codesmith17.github.io/daily-leetcode-redirect/)**

Bookmark this link in your browser to immediately open today's LeetCode Daily Challenge!

---

## 🛠️ GitHub Repository

- **Repository**: [https://github.com/codesmith17/daily-leetcode-redirect](https://github.com/codesmith17/daily-leetcode-redirect)
- **Live Pages**: [https://codesmith17.github.io/daily-leetcode-redirect/](https://codesmith17.github.io/daily-leetcode-redirect/)

That's it! GitHub Actions will now automatically keep your repository synced, and your frontend will always verify against the user's browser time to guarantee the correct question opens.

