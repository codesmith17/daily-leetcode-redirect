package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
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

	if err := saveJSONData(data, "leetcode", rootDir, syncedAt); err != nil {
		return nil, fmt.Errorf("render LeetCode: %w", err)
	}

	fmt.Printf("[LeetCode] Synced: %s. %s [%s] -> %s\n", data.ID, data.Title, data.Difficulty, data.URL)
	return data, nil
}
