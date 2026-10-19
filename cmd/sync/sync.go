package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"html"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
)

// ----------------- LEETCODE SYNC -----------------

func fetchLeetCodeGraphQL(client *http.Client) (*POTDData, error) {
	query := `query questionOfToday {
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
	}`
	payload, _ := json.Marshal(map[string]string{"query": query})

	req, err := http.NewRequest("POST", "https://leetcode.com/graphql", bytes.NewBuffer(payload))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Referer", "https://leetcode.com")
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

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

	var parsed struct {
		Data struct {
			ActiveDailyCodingChallengeQuestion struct {
				Date     string `json:"date"`
				Question struct {
					QuestionFrontendID string `json:"questionFrontendId"`
					Title              string `json:"title"`
					TitleSlug          string `json:"titleSlug"`
					Difficulty         string `json:"difficulty"`
					TopicTags          []struct {
						Name string `json:"name"`
					} `json:"topicTags"`
				} `json:"question"`
			} `json:"activeDailyCodingChallengeQuestion"`
		} `json:"data"`
	}

	if err := json.Unmarshal(body, &parsed); err != nil {
		return nil, err
	}

	q := parsed.Data.ActiveDailyCodingChallengeQuestion.Question
	if q.TitleSlug == "" {
		return nil, fmt.Errorf("empty titleSlug in response")
	}

	var tags []string
	for _, t := range q.TopicTags {
		tags = append(tags, t.Name)
	}

	return &POTDData{
		Platform:        "leetcode",
		ID:              q.QuestionFrontendID,
		Title:           q.Title,
		Slug:            q.TitleSlug,
		Difficulty:      q.Difficulty,
		DifficultyClass: strings.ToLower(q.Difficulty),
		URL:             fmt.Sprintf("https://leetcode.com/problems/%s/", q.TitleSlug),
		Date:            parsed.Data.ActiveDailyCodingChallengeQuestion.Date,
		Tags:            tags,
	}, nil
}

func fetchLeetCodeMirror(client *http.Client) (*POTDData, error) {
	req, err := http.NewRequest("GET", "https://alfa-leetcode-api.onrender.com/daily", nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", "Mozilla/5.0")

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

	var parsed struct {
		Date               string `json:"date"`
		QuestionFrontendID string `json:"questionFrontendId"`
		QuestionID         string `json:"questionId"`
		QuestionTitle      string `json:"questionTitle"`
		TitleSlug          string `json:"titleSlug"`
		Difficulty         string `json:"difficulty"`
		QuestionLink       string `json:"questionLink"`
		TopicTags          []struct {
			Name string `json:"name"`
		} `json:"topicTags"`
	}

	if err := json.Unmarshal(body, &parsed); err != nil {
		return nil, err
	}

	id := parsed.QuestionFrontendID
	if id == "" {
		id = parsed.QuestionID
	}

	var tags []string
	for _, t := range parsed.TopicTags {
		tags = append(tags, t.Name)
	}

	diff := parsed.Difficulty
	if diff == "" {
		diff = "Medium"
	}

	return &POTDData{
		Platform:        "leetcode",
		ID:              id,
		Title:           parsed.QuestionTitle,
		Slug:            parsed.TitleSlug,
		Difficulty:      diff,
		DifficultyClass: strings.ToLower(diff),
		URL:             parsed.QuestionLink,
		Date:            parsed.Date,
		Tags:            tags,
	}, nil
}

func syncLeetCode(client *http.Client, rootDir, syncedAt string) (*POTDData, error) {
	fmt.Println("\n[LeetCode] Fetching Problem of the Day...")
	data, err := fetchLeetCodeGraphQL(client)
	if err != nil {
		fmt.Printf("[LeetCode] Warning: GraphQL fetch failed (%v). Trying mirror...\n", err)
		data, err = fetchLeetCodeMirror(client)
		if err != nil {
			return nil, fmt.Errorf("all LeetCode sources failed: %w", err)
		}
		fmt.Println("[LeetCode] OK - Fetched from community mirror.")
	} else {
		fmt.Println("[LeetCode] OK - Fetched directly from LeetCode GraphQL.")
	}

	data.SyncedAt = syncedAt

	dataDir := filepath.Join(rootDir, "data")
	_ = os.MkdirAll(dataDir, 0755)

	jsonData, _ := json.MarshalIndent(data, "", "  ")
	_ = os.WriteFile(filepath.Join(dataDir, "leetcode.json"), jsonData, 0644)
	_ = os.WriteFile(filepath.Join(dataDir, "daily.json"), jsonData, 0644)

	templatePath := filepath.Join(rootDir, "templates", "leetcode.html")
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

	// Write root index.html, leetcode.html, leetcode/index.html, leetocde/index.html
	_ = os.WriteFile(filepath.Join(rootDir, "index.html"), []byte(rendered), 0644)
	_ = os.WriteFile(filepath.Join(rootDir, "leetcode.html"), []byte(rendered), 0644)

	leetcodeDir := filepath.Join(rootDir, "leetcode")
	_ = os.MkdirAll(leetcodeDir, 0755)
	_ = os.WriteFile(filepath.Join(leetcodeDir, "index.html"), []byte(rendered), 0644)

	leetocdeDir := filepath.Join(rootDir, "leetocde")
	_ = os.MkdirAll(leetocdeDir, 0755)
	_ = os.WriteFile(filepath.Join(leetocdeDir, "index.html"), []byte(rendered), 0644)

	fmt.Printf("[LeetCode] Synced: %s. %s [%s] -> %s\n", data.ID, data.Title, data.Difficulty, data.URL)
	return data, nil
}

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

	data.SyncedAt = syncedAt

	dataDir := filepath.Join(rootDir, "data")
	_ = os.MkdirAll(dataDir, 0755)

	jsonData, _ := json.MarshalIndent(data, "", "  ")
	_ = os.WriteFile(filepath.Join(dataDir, "gfg.json"), jsonData, 0644)

	templatePath := filepath.Join(rootDir, "templates", "gfg.html")
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

	_ = os.WriteFile(filepath.Join(rootDir, "gfg.html"), []byte(rendered), 0644)

	gfgDir := filepath.Join(rootDir, "gfg")
	_ = os.MkdirAll(gfgDir, 0755)
	_ = os.WriteFile(filepath.Join(gfgDir, "index.html"), []byte(rendered), 0644)

	fmt.Printf("[GFG] Synced: %s [%s] -> %s\n", data.Title, data.Difficulty, data.URL)
	return data, nil
}
