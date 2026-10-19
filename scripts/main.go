package main

import (
	"crypto/tls"
	"fmt"
	"html"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// POTDData represents the standardized Problem of the Day schema
type POTDData struct {
	Platform        string   `json:"platform"`
	ID              string   `json:"id"`
	Title           string   `json:"title"`
	Slug            string   `json:"slug"`
	Difficulty      string   `json:"difficulty"`
	DifficultyClass string   `json:"difficultyClass"`
	URL             string   `json:"url"`
	Date            string   `json:"date"`
	Tags            []string `json:"tags"`
	SyncedAt        string   `json:"syncedAt"`
}

// TopicStyle holds the accent color and SVG vector icon for algorithmic topics
type TopicStyle struct {
	Color string
	Icon  string
}

var topicRegistry = map[string]TopicStyle{
	"dynamic programming": {Color: "#c084fc", Icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/><path d="M15 21V9"/></svg>`},
	"dp":                  {Color: "#c084fc", Icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/><path d="M15 21V9"/></svg>`},
	"stack":               {Color: "#38bdf8", Icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>`},
	"queue":               {Color: "#2dd4bf", Icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/><path d="M12 5l7 7-7 7"/><circle cx="5" cy="12" r="2"/></svg>`},
	"graph":               {Color: "#f472b6", Icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="6" cy="6" r="3"/><circle cx="18" cy="8" r="3"/><circle cx="12" cy="18" r="3"/><line x1="8.5" y1="7" x2="15.5" y2="7.5"/><line x1="7.5" y1="8.5" x2="10.5" y2="15.5"/><line x1="16.5" y1="10" x2="13.5" y2="16"/></svg>`},
	"tree":                {Color: "#4ade80", Icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="5" r="3"/><circle cx="6" cy="19" r="3"/><circle cx="18" cy="19" r="3"/><path d="M12 8v4"/><path d="M12 12l-4 4"/><path d="M12 12l4 4"/></svg>`},
	"binary tree":         {Color: "#4ade80", Icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="5" r="3"/><circle cx="6" cy="19" r="3"/><circle cx="18" cy="19" r="3"/><path d="M12 8v4"/><path d="M12 12l-4 4"/><path d="M12 12l4 4"/></svg>`},
	"array":               {Color: "#60a5fa", Icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="6" width="20" height="12" rx="2"/><line x1="8" y1="6" x2="8" y2="18"/><line x1="14" y1="6" x2="14" y2="18"/><line x1="20" y1="6" x2="20" y2="18"/></svg>`},
	"sorting":             {Color: "#a78bfa", Icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`},
	"greedy":              {Color: "#e879f9", Icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 3h12l4 6-10 12L2 9l4-6z"/><path d="M2 9h20"/></svg>`},
	"binary search":       {Color: "#34d399", Icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`},
	"dfs":                 {Color: "#38bdf8", Icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v18"/><path d="M18 15l-6 6-6-6"/></svg>`},
	"bfs":                 {Color: "#38bdf8", Icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3a9 9 0 0 0 0 18"/><path d="M12 7a5 5 0 0 0 0 10"/><path d="M12 11a1 1 0 0 0 0 2"/></svg>`},
	"string":              {Color: "#fbbf24", Icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>`},
	"hash":                {Color: "#fb7185", Icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/></svg>`},
	"two pointers":        {Color: "#818cf8", Icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8L22 12L18 16"/><path d="M2 12H22"/><path d="M6 16L2 12L6 8"/></svg>`},
	"math":                {Color: "#facc15", Icon: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="12" x2="20" y2="12"/><line x1="12" y1="4" x2="12" y2="20"/></svg>`},
}

func renderTagsHTML(tags []string) string {
	var b strings.Builder
	limit := 4
	if len(tags) < limit {
		limit = len(tags)
	}
	for i := 0; i < limit; i++ {
		tagName := tags[i]
		tLower := strings.ToLower(tagName)
		color := "#94a3b8"
		icon := `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/></svg>`
		for key, style := range topicRegistry {
			if strings.Contains(tLower, key) {
				color = style.Color
				icon = style.Icon
				break
			}
		}
		b.WriteString(fmt.Sprintf(`<span class="pill topic-tag" style="--tag-color:%s">%s<span>%s</span></span>`, color, icon, html.EscapeString(tagName)))
	}
	return b.String()
}

func newHTTPClient() *http.Client {
	return &http.Client{
		Timeout: 20 * time.Second,
		Transport: &http.Transport{
			TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
		},
	}
}

// ----------------- ENTRYPOINT -----------------

func main() {
	rootDir, err := os.Getwd()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error getting working directory: %v\n", err)
		os.Exit(1)
	}

	// Navigate to repo root if run from inside scripts/
	if filepath.Base(rootDir) == "scripts" {
		rootDir = filepath.Dir(rootDir)
	}

	nowUTC := time.Now().UTC()
	syncedAt := nowUTC.Format("2006-01-02 15:04 UTC")

	client := newHTTPClient()

	// 1. Sync LeetCode POTD
	_, errLC := syncLeetCode(client, rootDir, syncedAt)
	if errLC != nil {
		fmt.Fprintf(os.Stderr, "[LeetCode Error]: %v\n", errLC)
	}

	// 2. Sync GeeksforGeeks POTD
	_, errGFG := syncGFG(client, rootDir, syncedAt)
	if errGFG != nil {
		fmt.Fprintf(os.Stderr, "[GFG Error]: %v\n", errGFG)
	}

	fmt.Println("\n✓ Golang sync completed successfully.")
}
