# Daily Coding Challenge Redirects (LeetCode + GeeksforGeeks POTD)

Lightning-fast, timezone-aware terminal redirect pages for both **LeetCode Problem of the Day** and **GeeksforGeeks Problem of the Day**.

---

## 🌐 Live URLs

| Platform | Live Redirect URL | Reset Time |
| :--- | :--- | :--- |
| **LeetCode POTD** | 👉 **[https://codesmith17.github.io/daily-leetcode-redirect/](https://codesmith17.github.io/daily-leetcode-redirect/)** | `00:00 UTC` (05:30 AM IST) |
| **GeeksforGeeks POTD** | 👉 **[https://codesmith17.github.io/daily-leetcode-redirect/gfg](https://codesmith17.github.io/daily-leetcode-redirect/gfg)** | `00:00 IST` (18:30 UTC) |

Bookmark either link in your browser to immediately jump into today's problem!

---

## ⚡ Why Other Static Redirects Open the Wrong Link

1. **GitHub Actions Schedule Delays**:
   - Single-schedule cron jobs on GitHub's free runners are placed on a shared public queue and frequently delayed by **3 to 5 hours** during peak traffic.
2. **Hardcoded Static Redirects**:
   - Other redirect sites bake static `<meta http-equiv="refresh">` and `<script>window.location.replace</script>` into the HTML without client-side date checks. If the cron was delayed, visitors were redirected to yesterday's problem.
3. **Timezone Misalignment**:
   - LeetCode resets at **00:00 UTC**, while GeeksforGeeks resets at **00:00 IST**.
   - These pages detect your **local browser time**, track time remaining until reset for each platform, and dynamically verify the challenge before redirecting.

---

## 🚀 Key Features

- **Dual Platform Support**: Both LeetCode and GeeksforGeeks POTD in one repository.
- **Timezone & Reset Aware**:
  - LeetCode page tracks countdown to `00:00 UTC`.
  - GeeksforGeeks page tracks countdown to `00:00 IST`.
- **Hybrid Verification**:
  - Instant page load using pre-rendered fallback.
  - Client-side live verification with cache-busting to ensure fresh links.
- **Interactive Controls**:
  - Animated progress bar before redirecting.
  - **Pause / Resume** button to examine the problem title, difficulty, and tags.
  - One-click navigation switcher between LeetCode and GeeksforGeeks.
- **Zero External UI Dependencies**: Pure CSS/JS with a terminal dark-mode theme.

---

## 📂 Project Structure

```
daily-leetcode-redirect/
├── .github/
│   └── workflows/
│       └── update-daily-challenge.yml   # Auto-sync at 00:00 IST & 00:00 UTC
├── data/
│   ├── daily.json                      # Current LeetCode POTD data
│   └── gfg.json                        # Current GeeksforGeeks POTD data
├── scripts/
│   └── sync-daily-challenge.py         # Multi-platform sync script
├── template.html                       # LeetCode template
├── template-gfg.html                   # GeeksforGeeks template
├── index.html                          # Deployed LeetCode redirect page
├── gfg.html                            # Deployed GeeksforGeeks redirect page
├── gfg/index.html                      # Clean URL support (/gfg)
├── .gitignore
└── README.md
```
