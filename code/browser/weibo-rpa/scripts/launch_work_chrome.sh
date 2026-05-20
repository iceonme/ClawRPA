#!/bin/bash

# Default values
PORT=9222
NEW_WINDOW=false
USER_DATA_DIR=""

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --port|-Port|-port) PORT="$2"; shift ;;
        --user-data-dir|-UserDataDir|-userdata-dir) USER_DATA_DIR="$2"; shift ;;
        --new-window|-NewWindow|-new-window) NEW_WINDOW=true ;;
    esac
    shift
done

# Resolve directories
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

if [ -z "$USER_DATA_DIR" ]; then
    USER_DATA_DIR="$PROJECT_ROOT/runtime/chrome-workbench/profile"
fi

mkdir -p "$USER_DATA_DIR"

# Check if CDP is already running
VERSION_URL="http://127.0.0.1:$PORT/json/version"
if python3 -c "import urllib.request; urllib.request.urlopen('$VERSION_URL', timeout=1)" &>/dev/null; then
    echo "CDP already available at $VERSION_URL"
    echo "UserDataDir: $USER_DATA_DIR"
    exit 0
fi

# Find Chrome executable on Linux
CHROME_PATH=""
for cmd in google-chrome google-chrome-stable chromium chromium-browser; do
    if command -v "$cmd" &>/dev/null; then
        CHROME_PATH="$cmd"
        break
    fi
done

if [ -z "$CHROME_PATH" ]; then
    echo "Error: Chrome or Chromium executable not found on this system." >&2
    exit 1
fi

ARGS=(
    "--remote-debugging-port=$PORT"
    "--user-data-dir=$USER_DATA_DIR"
    "--no-first-run"
    "--no-default-browser-check"
)

if [ "$NEW_WINDOW" = true ]; then
    ARGS+=("--new-window")
fi

echo "Launching Chrome using command: $CHROME_PATH ${ARGS[@]}"
nohup "$CHROME_PATH" "${ARGS[@]}" > /dev/null 2>&1 &

# Wait up to 5 seconds for Chrome to start and CDP to respond
for i in {1..10}; do
    if python3 -c "import urllib.request; urllib.request.urlopen('$VERSION_URL', timeout=0.5)" &>/dev/null; then
        echo "Chrome launched successfully."
        echo "CDP endpoint: $VERSION_URL"
        echo "UserDataDir: $USER_DATA_DIR"
        exit 0
    fi
    sleep 0.5
done

echo "Error: Chrome launched but CDP did not become ready at $VERSION_URL within 5 seconds." >&2
exit 1
