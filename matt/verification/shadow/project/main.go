package main

import (
	"fmt"
	"io"
	"os"
)

func main() {
	os.Exit(run(os.Args[1:], os.Stdout, os.Stderr))
}

func run(args []string, stdout, stderr io.Writer) int {
	configPath := "config.yaml"
	if len(args) == 2 && args[0] == "--config" {
		configPath = args[1]
	}

	if _, err := os.Stat(configPath); err != nil {
		if os.IsNotExist(err) {
			fmt.Fprintln(stderr, "configuration file not found")
			return 2
		}
		fmt.Fprintln(stderr, err)
		return 1
	}

	fmt.Fprintln(stdout, "configuration loaded")
	return 0
}
