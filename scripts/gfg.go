package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
)

// ----------------- GEEKSFORGEEKS SYNC -----------------

func fetchGFGAPI(client *http.Client) (*POTDData, error) {
	endpoints := []string{
		"https://practiceapi.geeksforgeeks.org/api/vr/problems-of-day/problem/today/",
		"https://practiceapi.geeksforgeeks.org/api/v1/problems-of-day/problem/today/",
		"https://practiceapi.geeksforgeeks.org/api/latest/problems-of-day/problem/today/",
	}

	for _, endpoint := range endpoints {
		req, err := http.NewRequest("GET", endpoint, nil)
		if err != nil {
			continue
		}
		req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
		req.Header.Set("Referer", "https://www.geeksforgeeks.org/")

		resp, err := client.Do(req)
		if err != nil {
			continue
		}

		if resp.StatusCode != http.StatusOK {
			resp.Body.Close()
			continue
		}

		body, err := io.ReadAll(resp.Body)
		resp.Body.Close()
		if err != nil {
			continue
		}

		var parsed struct {
			ID          int    `json:"id"`
			ProblemID   int    `json:"problem_id"`
			Date        string `json:"date"`
			ProblemName string `json:"problem_name"`
			ProblemURL  string `json:"problem_url"`
			Difficulty  string `json:"difficulty"`
			Tags        struct {
				TopicTags []string `json:"topic_tags"`
			} `json:"tags"`
		}

		if err := json.Unmarshal(body, &parsed); err != nil {
			continue
		}

		diff := parsed.Difficulty
		if diff == "" {
			diff = "Medium"
		}

		dateStr := parsed.Date
		if len(dateStr) >= 10 {
			dateStr = dateStr[:10]
		}

		idStr := fmt.Sprintf("%d", parsed.ID)
		if idStr == "0" && parsed.ProblemID != 0 {
			idStr = fmt.Sprintf("%d", parsed.ProblemID)
		}

		slug := parsed.ProblemURL
		parts := strings.Split(strings.TrimRight(parsed.ProblemURL, "/"), "/")
		if len(parts) > 0 {
			slug = parts[len(parts)-1]
		}

		return &POTDData{
			Platform:        "gfg",
			ID:              idStr,
			Title:           parsed.ProblemName,
			Slug:            slug,
			Difficulty:      diff,
			DifficultyClass: strings.ToLower(diff),
			URL:             parsed.ProblemURL,
			Date:            dateStr,
			Tags:            parsed.Tags.TopicTags,
		}, nil
	}

	return nil, fmt.Errorf("all GeeksforGeeks endpoints failed")
}

func syncGFG(client *http.Client, rootDir, syncedAt string) (*POTDData, error) {
	fmt.Println("\n[GFG] Fetching Problem of the Day...")
	data, err := fetchGFGAPI(client)
	if err != nil {
		return nil, fmt.Errorf("fetch GFG: %w", err)
	}
	fmt.Println("[GFG] OK - Fetched directly from GeeksforGeeks Practice API.")

	if err := renderPage(data, "gfg", rootDir, syncedAt, false); err != nil {
		return nil, fmt.Errorf("render GFG: %w", err)
	}

	fmt.Printf("[GFG] Synced: %s [%s] -> %s\n", data.Title, data.Difficulty, data.URL)
	return data, nil
}
