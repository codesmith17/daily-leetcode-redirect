package main

import (
	"crypto/tls"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
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

func newHTTPClient() *http.Client {
	return &http.Client{
		Timeout: 20 * time.Second,
		Transport: &http.Transport{
			TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
		},
	}
}

// saveJSONData persists the synced POTD data to JSON files in the data/ directory.
// The frontend dynamically reads data from these JSON files, keeping HTML files clean and static.
func saveJSONData(data *POTDData, platform, rootDir, syncedAt string) error {
	data.SyncedAt = syncedAt

	dataDir := filepath.Join(rootDir, "data")
	if err := os.MkdirAll(dataDir, 0755); err != nil {
		return fmt.Errorf("create data directory: %w", err)
	}

	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal %s json: %w", platform, err)
	}

	platformPath := filepath.Join(dataDir, fmt.Sprintf("%s.json", platform))
	if err := os.WriteFile(platformPath, jsonData, 0644); err != nil {
		return fmt.Errorf("write %s: %w", platformPath, err)
	}

	return nil
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

	// 3. Sync takeUforward (TUF) POTD
	_, errTUF := syncTUF(client, rootDir, syncedAt)
	if errTUF != nil {
		fmt.Fprintf(os.Stderr, "[TUF Error]: %v\n", errTUF)
	}

	fmt.Println("\n✓ Golang sync completed successfully.")
}
