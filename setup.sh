#!/usr/bin/env bash
set -euo pipefail

# Ensure we're in the script's directory (handles running `bash /path/to/setup.sh`)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  logtrim - Setup"
echo "========================================"
echo

# Check if Python 3 is available
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 not found."
    echo ""
    echo "Please install Python 3.9+ from https://python.org"
    echo "Make sure 'Add Python to PATH' is checked during installation."
    exit 1
fi

PYTHON_VER=$(python3 --version 2>&1)
echo "[OK] Found ${PYTHON_VER}"

# Try creating a virtual environment first (best practice, isolated from system)
if python3 -m venv .venv 2>/dev/null; then
    echo "[INFO] Virtual environment created at .venv/"
    # shellcheck disable=SC1091
    . .venv/bin/activate

    pip install --upgrade pip --quiet 2>/dev/null || true

    echo "[INFO] Installing logtrim..."
    if pip install -e . 2>&1; then
        :
    else
        # Fallback: try non-editable install inside venv
        echo "[INFO] Trying non-editable install instead..."
        if pip install . 2>&1; then
            echo ""
            echo "========================================"
            echo "  Setup complete!"
            echo "========================================"
            echo ""
            echo "Run: logtrim --input your-log.txt"
            echo ""
            echo "To activate the virtual environment later:"
            echo "  source .venv/bin/activate"
            exit 0
        else
            echo "[ERROR] Installation failed inside venv."
            exit 1
        fi
    fi

    # Verify inside venv
    if command -v logtrim &>/dev/null; then
        echo ""
        echo "========================================"
        echo "  Setup complete!"
        echo "========================================"
        echo ""
        echo "Run: logtrim --input your-log.txt"
        echo ""
        echo "To activate the virtual environment later:"
        echo "  source .venv/bin/activate"
    else
        echo "[ERROR] Installation verification failed."
        exit 1
    fi
else
    # No venv module — install directly. On Debian/Ubuntu Python 3.12+ with PEP 668,
    # both `pip install .` and `pip install --user .` are blocked; only
    # `--break-system-packages` bypasses this restriction. Since the target environment
    # typically has nothing else installed anyway, using --break-system-packages is safe.
    echo "[WARN] Virtual environment unavailable (ensurepip missing)."
    echo "       Installing directly..."
    echo ""

    pip_flags=""

    # Test if default pip install works (macOS stock Python often allows this)
    if python3 -m pip install . &>/dev/null; then
        echo "[OK] Installed via default pip"
        pip_flags="installed"
    else
        echo "[INFO] Default pip blocked (externally-managed environment). Using --break-system-packages..."
        if python3 -m pip install --break-system-packages . 2>&1; then
            pip_flags="--break-system-packages"
        else
            # Last-resort: try with --no-build-isolation (avoids downloading setuptools)
            echo "[INFO] Trying without build isolation..."
            if python3 -m pip install --break-system-packages --no-build-isolation . 2>&1; then
                pip_flags="--break-system-packages --no-build-isolation"
            else
                echo ""
                echo "[ERROR] Installation failed."
                echo ""
                echo "Troubleshooting steps:"
                echo "  1) Install the venv package and retry:"
                echo "     sudo apt install python3-venv"
                echo "     bash setup.sh"
                echo ""
                echo "  2) Or create a virtual environment manually:"
                echo "     python3 -m venv .venv"
                echo "     source .venv/bin/activate"
                echo "     pip install ."
                exit 1
            fi
        fi
    fi

    # Verify installation (check both command and module)
    echo ""
    if command -v logtrim &>/dev/null; then
        echo "========================================"
        echo "  Setup complete!"
        echo "========================================"
        echo ""
        echo "Run: logtrim --input your-log.txt"
    elif python3 -m logtrim --help &>/dev/null; then
        echo "========================================"
        echo "  Setup complete!"
        echo "========================================"
        echo ""
        echo "Run: python3 -m logtrim --input your-log.txt"
        echo ""
        echo "Note: The 'logtrim' command is not on PATH."
        echo "Use 'python3 -m logtrim' to run, or fix your Python PATH:"
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    else
        echo "[ERROR] Installation verification failed."
        exit 1
    fi
fi
