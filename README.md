# Iris — Always-Available Terminal AI (Online & Offline)

Iris is a lightweight Python terminal AI assistant that launches anywhere with `iris`—no manual virtual environment activation required after the one-time install.

## Built On Open-Source Tools
- **Offline LLM Runtime**: [Ollama](https://github.com/ollama/ollama) & [ollama-python](https://github.com/ollama/ollama-python)
- **Online Multi-Provider Gateway**: [LiteLLM](https://github.com/BerriAI/litellm)
- *(Alternative all-in-one pre-built agent: [Open Interpreter](https://github.com/openinterpreter/openinterpreter))*

## One-Time Setup (macOS / Linux)

1. Unzip this folder and `cd iris`.
2. Run the installer once:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
   This creates `.venv/` inside `iris/` and symlinks `~/.local/bin/iris`, so typing `iris` in any terminal window boots it immediately without activating an environment.

3. **Offline setup** (optional, recommended):
   Install [Ollama](https://github.com/ollama/ollama) and pull a local model:
   ```bash
   ollama pull gemma4
   ```

4. **Online setup** (optional):
   Export an API key in your `~/.bashrc` or `~/.zshrc`, for example:
   ```bash
   export GEMINI_API_KEY="your-key-here"
   ```
   In `auto` mode (default), Iris uses the online model when internet + an API key are present, and automatically falls back to local Ollama when offline.

## Usage
- Interactive mode:
  ```bash
  iris
  ```
- One-shot command:
  ```bash
  iris "find the largest files in my Downloads folder"
  ```
- Force offline or online mode:
  ```bash
  iris --mode offline
  iris --mode online
  ```

## Security & System Password Note
Iris **never** stores your system password on disk or intercepts OS password changes. Whenever a confirmed command uses `sudo`, your operating system's native `sudo` prompt handles authentication in memory—so if you change your system password, `sudo` automatically uses the new password with zero configuration updates needed.
