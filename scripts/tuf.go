package main

import (
	"encoding/json"
	"fmt"
	"html"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

// ----------------- TAKEUFORWARD (TUF) SYNC -----------------

type TUFResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	Data    struct {
		DayID  int `json:"day_id"`
		Tracks []struct {
			PotdScheduleID int    `json:"potd_schedule_id"`
			TrackSlug      string `json:"track_slug"`
			DayID          int    `json:"day_id"`
			Problem        struct {
				ProblemID  int    `json:"problem_id"`
				Slug       string `json:"slug"`
				Name       string `json:"name"`
				Difficulty string `json:"difficulty"`
				Type       string `json:"type"`
			} `json:"problem"`
			RewardCoins int `json:"reward_coins"`
			Stats       struct {
				SolveCount     int     `json:"solve_count"`
				AttemptCount   int     `json:"attempt_count"`
				AcceptanceRate float64 `json:"acceptance_rate"`
			} `json:"stats"`
		} `json:"tracks"`
	} `json:"data"`
}

func fetchTUFAPI(client *http.Client) (*POTDData, error) {
	req, err := http.NewRequest("GET", "https://backend-go.takeuforward.org/api/v1/potd/today?track=dsa", nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
	req.Header.Set("Origin", "https://takeuforward.org")
	req.Header.Set("Referer", "https://takeuforward.org/")

	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("HTTP status %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var parsed TUFResponse
	if err := json.Unmarshal(body, &parsed); err != nil {
		return nil, fmt.Errorf("unmarshal TUF JSON: %w", err)
	}

	if len(parsed.Data.Tracks) == 0 || parsed.Data.Tracks[0].Problem.Slug == "" {
		return nil, fmt.Errorf("empty TUF tracks in response")
	}

	track := parsed.Data.Tracks[0]
	prob := track.Problem

	dayStr := fmt.Sprintf("%d", parsed.Data.DayID)
	formattedDate := ""
	if len(dayStr) == 8 {
		formattedDate = fmt.Sprintf("%s-%s-%s", dayStr[0:4], dayStr[4:6], dayStr[6:8])
	} else {
		formattedDate = dayStr
	}

	diffRaw := strings.ToLower(prob.Difficulty)
	diffLabel := "Core"
	diffClass := "medium"
	if strings.Contains(diffRaw, "basic") || strings.Contains(diffRaw, "easy") {
		diffLabel = "Basic"
		diffClass = "easy"
	} else if strings.Contains(diffRaw, "pro") || strings.Contains(diffRaw, "hard") {
		diffLabel = "Pro"
		diffClass = "hard"
	}

	url := fmt.Sprintf("https://takeuforward.org/practice/dsa/%s", prob.Slug)

	// Infer topic tags from title & track
	tags := []string{"DSA"}
	titleLower := strings.ToLower(prob.Name)
	topicKeywords := []string{
		"array", "string", "dynamic programming", "tree", "binary tree", "bst",
		"graph", "stack", "queue", "linked list", "bit manipulation", "binary search",
		"heap", "trie", "matrix", "greedy", "sorting", "recursion", "backtracking",
	}
	for _, kw := range topicKeywords {
		if strings.Contains(titleLower, kw) {
			tags = append(tags, strings.Title(kw))
		}
	}
	if strings.Contains(titleLower, "divide") && strings.Contains(titleLower, "multiplication") {
		tags = append(tags, "Bit Manipulation")
	}
	tags = append(tags, "TUF+ POTD")

	return &POTDData{
		Platform:        "tuf",
		ID:              fmt.Sprintf("#%d", prob.ProblemID),
		Title:           prob.Name,
		Slug:            prob.Slug,
		Difficulty:      diffLabel,
		DifficultyClass: diffClass,
		URL:             url,
		Date:            formattedDate,
		Tags:            tags,
	}, nil
}

func fetchTUFFallbackHTML(client *http.Client) (*POTDData, error) {
	req, err := http.NewRequest("GET", "https://takeuforward.org/potd", nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("HTTP status %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	htmlContent := string(body)

	// Regex search for today's title
	titleRe := regexp.MustCompile(`bannerLowerTitle">([^<]+)</div>`)
	match := titleRe.FindStringSubmatch(htmlContent)
	if len(match) < 2 {
		return nil, fmt.Errorf("could not extract title from TUF HTML")
	}
	title := html.UnescapeString(match[1])

	slugRe := regexp.MustCompile(`"slug":"([^"]+)"`)
	slugMatch := slugRe.FindStringSubmatch(htmlContent)
	slug := "divide-two-numbers-without-multiplication-and-division"
	if len(slugMatch) >= 2 {
		slug = slugMatch[1]
	}

	return &POTDData{
		Platform:        "tuf",
		ID:              "POTD",
		Title:           title,
		Slug:            slug,
		Difficulty:      "Core",
		DifficultyClass: "medium",
		URL:             fmt.Sprintf("https://takeuforward.org/practice/dsa/%s", slug),
		Date:            "",
		Tags:            []string{"DSA", "TUF+ POTD"},
	}, nil
}

func syncTUF(client *http.Client, rootDir, syncedAt string) (*POTDData, error) {
	fmt.Println("\n[TUF] Fetching Problem of the Day...")
	data, err := fetchTUFAPI(client)
	if err != nil {
		fmt.Printf("[TUF] Warning: API fetch failed (%v). Trying HTML fallback...\n", err)
		data, err = fetchTUFFallbackHTML(client)
		if err != nil {
			return nil, fmt.Errorf("all TUF sources failed: %w", err)
		}
		fmt.Println("[TUF] OK - Fetched via takeuforward.org HTML fallback.")
	} else {
		fmt.Println("[TUF] OK - Fetched directly from takeuforward.org backend API.")
	}

	data.SyncedAt = syncedAt

	dataDir := filepath.Join(rootDir, "data")
	_ = os.MkdirAll(dataDir, 0755)

	jsonData, _ := json.MarshalIndent(data, "", "  ")
	_ = os.WriteFile(filepath.Join(dataDir, "tuf.json"), jsonData, 0644)

	templatePath := filepath.Join(rootDir, "templates", "tuf.html")
	templateBytes, err := os.ReadFile(templatePath)
	if err != nil {
		return nil, fmt.Errorf("read template %s: %w", templatePath, err)
	}

	tagsHTML := renderTagsHTML(data.Tags)
	tagsJSON, _ := json.Marshal(data.Tags)

	rendered := string(templateBytes)
	rendered = strings.ReplaceAll(rendered, "__ID__", html.EscapeString(data.ID))
	rendered = strings.ReplaceAll(rendered, "__TITLE__", html.EscapeString(data.Title))
	rendered = strings.ReplaceAll(rendered, "__SLUG__", data.Slug)
	rendered = strings.ReplaceAll(rendered, "__DIFFICULTY__", html.EscapeString(data.Difficulty))
	rendered = strings.ReplaceAll(rendered, "__DIFFICULTY_CLASS__", data.DifficultyClass)
	rendered = strings.ReplaceAll(rendered, "__URL__", data.URL)
	rendered = strings.ReplaceAll(rendered, "__DATE__", data.Date)
	rendered = strings.ReplaceAll(rendered, "__TAGS_HTML__", tagsHTML)
	rendered = strings.ReplaceAll(rendered, "__TAGS_JSON__", string(tagsJSON))
	rendered = strings.ReplaceAll(rendered, "__SYNCED_AT__", syncedAt)

	tufDir := filepath.Join(rootDir, "tuf")
	_ = os.MkdirAll(tufDir, 0755)
	_ = os.WriteFile(filepath.Join(tufDir, "index.html"), []byte(rendered), 0644)

	fmt.Printf("[TUF] Synced: %s. %s [%s] -> %s\n", data.ID, data.Title, data.Difficulty, data.URL)
	return data, nil
}
