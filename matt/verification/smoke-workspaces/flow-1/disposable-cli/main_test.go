package main

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"
)

func TestRun(t *testing.T) {
	t.Run("missing config reports the current error and succeeds", func(t *testing.T) {
		var stdout bytes.Buffer
		var stderr bytes.Buffer
		missingPath := filepath.Join(t.TempDir(), "missing.yaml")

		if got := run([]string{"--config", missingPath}, &stdout, &stderr); got != 0 {
			t.Fatalf("run() exit code = %d, want 0", got)
		}
		if got, want := stderr.String(), "configuration file not found\n"; got != want {
			t.Fatalf("stderr = %q, want %q", got, want)
		}
		if got := stdout.String(); got != "" {
			t.Fatalf("stdout = %q, want empty", got)
		}
	})

	t.Run("existing config keeps the success path", func(t *testing.T) {
		configPath := filepath.Join(t.TempDir(), "config.yaml")
		if err := os.WriteFile(configPath, []byte("enabled: true\n"), 0o600); err != nil {
			t.Fatal(err)
		}

		var stdout bytes.Buffer
		var stderr bytes.Buffer
		if got := run([]string{"--config", configPath}, &stdout, &stderr); got != 0 {
			t.Fatalf("run() exit code = %d, want 0", got)
		}
		if got, want := stdout.String(), "configuration loaded\n"; got != want {
			t.Fatalf("stdout = %q, want %q", got, want)
		}
		if got := stderr.String(); got != "" {
			t.Fatalf("stderr = %q, want empty", got)
		}
	})
}
