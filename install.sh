#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
BIN_DIR="$HOME/.local/bin"

echo "[1/4] Creating isolated virtual environment in $VENV_DIR (one-time setup)..."
python3 -m venv "$VENV_DIR"

echo "[2/4] Installing Iris and dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -e "$SCRIPT_DIR"

echo "[3/4] Linking 'iris' command to $BIN_DIR/iris..."
mkdir -p "$BIN_DIR"
ln -sf "$VENV_DIR/bin/iris" "$BIN_DIR/iris"

echo "[4/4] Checking PATH..."
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  SHELL_RC="$HOME/.bashrc"
  if [[ "${SHELL:-}" == *"zsh"* ]]; then
    SHELL_RC="$HOME/.zshrc"
  fi
  echo "export PATH=\"$HOME/.local/bin:\$PATH\"" >> "$SHELL_RC"
  echo "Added $BIN_DIR to $SHELL_RC. Run 'source $SHELL_RC' or open a new terminal."
fi

echo ""
echo "Done! Type 'iris' anywhere in your terminal to start."
echo "For offline mode: install Ollama (https://ollama.com) and run 'ollama pull gemma4'."
