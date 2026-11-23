# Iris Package — story_time.md: The Python Files, Line by Line

This document is written so you can read it and then write the code yourself, without help. It
walks every Python file of the iris package line by line: `iris/cli.py` and `iris/__init__.py`.
(The project-root `story_time.md` already contains the full walkthrough of the main program
`iris/cli.py`; per the rule, that existing file is left untouched.)

---

## 1. `iris/cli.py` — the program, line by line

The file has 213 lines.

### L1: `import argparse`
Import the standard-library module `argparse`. Later, `main()` builds a command-line parser with it
(L163–173): it lets you run `iris` with an optional prompt word and flags like `--mode`,
`--online-model`, `--offline-model`. `argparse` also prints usage help when you run `iris --help`.

### L2: `import json`
Import `json` — Python's JSON (JavaScript Object Notation) handling. Honest note: I searched the
file; `json` is never used afterwards in this version. It is harmless; you can delete this import
when you re-type the program.

### L3: `import os`
Import `os` — the operating system interface. Used for `os.environ.get(...)` (reading environment
variables) at L21–22 and in `has_online_api_key` at L47.

### L4: `import re`
Import `re` — the regular-expression module. Used once, in `extract_shell_commands` (L90): a regex
finds text blocks that look like ` ```run_shell ... ``` ` inside the model's reply.

### L5: `import socket`
Import `socket` — used by `is_online` (L38) to open a TCP connection to `1.1.1.1:443` with a
timeout, which tells whether the machine has internet.

### L6: `import subprocess`
Import `subprocess` — used by `run_command_with_confirmation` (L107–112) to actually run a shell
command on your machine with `subprocess.run`.

### L7: `import sys`
Import `sys`. Honest note: `sys` is not used anywhere in this version of `cli.py`.

### L8: `from pathlib import Path`
Import `Path` from `pathlib` — the modern way to work with filesystem paths. Used for `Path.home()`
(L19) and building `Path` objects for the config files (L19–20).

### L9: `from typing import Any`
Import `Any` from `typing` — used as a type annotation meaning "any type of value". Honest note:
`Any` is not actually used anywhere in this version of the file (like `sys` and `json`, it can be
dropped).

### L11: `from prompt_toolkit import PromptSession`
Import `PromptSession` — a library for building interactive command-line prompts. `main()` uses it
at L190 to get the user's typed input at the `iris> ` prompt, with history recall (up-arrow)
because of `FileHistory` (L12, L190).

### L12: `from prompt_toolkit.history import FileHistory`
Import `FileHistory` — stores the prompt history on disk in `~/.iris/history` so you can press ↑ and
see earlier prompts.

### L13: `from rich.console import Console`
Import `Console` — `rich` is a library for beautiful terminal output. `console = Console()` at L17
creates the output object used everywhere via `console.print(...)`.

### L14: `from rich.markdown import Markdown`
Import `Markdown` — used at L147 (`console.print(Markdown(reply))`) to render the model's replies as
formatted Markdown.

### L15: `from rich.panel import Panel`
Import `Panel` — a boxed container. Used for the startup banner (L183–188) and the
"Proposed Terminal Command" box (L95).

### L17: `console = Console()`
Create the `Console` object — the program's "screen writer". Every `console.print(...)` call prints
to your terminal with rich formatting (colors, boxes, Markdown).

### L19: `CONFIG_DIR = Path.home() / ".iris"`
`Path.home()` is your home directory; `/ ".iris"` joins the path, so `CONFIG_DIR` becomes `~/.iris`.
This is the folder where iris keeps its data (L20: history file). It does not need to exist at
import time; `main()` creates it with `mkdir` at L175.

### L20: `HISTORY_FILE = CONFIG_DIR / "history"`
The full path of the prompt-history file: `~/.iris/history`.

### L21: `DEFAULT_ONLINE_MODEL = os.environ.get("IRIS_ONLINE_MODEL", "gemini/gemini-2.5-flash")`
Read the environment variable `IRIS_ONLINE_MODEL`; if it is not set, use the default string
`"gemini/gemini-2.5-flash"` (LiteLLM's name for Gemini 2.5 Flash). The variable is read once, at
import time.

### L22: `DEFAULT_OFFLINE_MODEL = os.environ.get("IRIS_OFFLINE_MODEL", "gemma4")`
Same pattern for the local model: `IRIS_OFFLINE_MODEL`, default `"gemma4"` (a local Ollama model
name).

### L24–32: `SYSTEM_PROMPT = ( ... )`
The text that defines who Iris is: it lives in your terminal, can answer questions or propose shell
commands, should output fenced ` ```run_shell ` blocks for commands it wants to run, should wait for
command output before drawing conclusions, and should keep responses concise. It is one long string
built by putting several quoted string literals next to each other on consecutive lines (adjacent
string literals concatenate). The `\n` sequences inside the string become real newlines, so the
model sees the fenced-code example formatted as intended. This string is sent to the model as its
system prompt at L176 and again on `/clear` at L205.

### L35–41: `def is_online(timeout: float = 1.5) -> bool:`
A function definition: `def` + name + parameter list (`timeout` has a default of `1.5`) + return
type `-> bool` (it returns True or False). The string on L36 is a docstring — just documentation.
Body:
- L37: `try:` — start of a try/except block.
- L38: `with socket.create_connection(("1.1.1.1", 443), timeout=timeout):` — open a TCP connection
  to `1.1.1.1` (Cloudflare's DNS server) on port 443 with the given timeout. `("1.1.1.1", 443)` is a
  tuple: address, port. `with` guarantees the connection is closed when the block ends.
- L39: `return True` — if the connection succeeded, you have internet → return True.
- L40–41: `except OSError:` / `return False` — if the connection raised an `OSError` (no network /
  blocked), return False. Only `OSError` is caught; other exceptions would propagate.

### L44–47: `def has_online_api_key() -> bool:`
Returns True if any of the common cloud LLM API keys is present in the environment.
- L46: `keys = ("GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY")` — build a
  tuple of the four variable names.
- L47: `return any(bool(os.environ.get(k)) for k in keys)` — a generator expression: for each name
  `k` in `keys`, get its value with `os.environ.get(k)` (returns `None` if unset), `bool(...)` turns
  it into True/False (any non-empty string is truthy), and `any(...)` returns True if at least one
  key is set.

### L50–55: `def call_offline_ollama(messages: list[dict[str, str]], model: str) -> str:`
Query the local Ollama server.
- L52: `import ollama` — the `ollama` package is imported lazily, inside the function. This matters:
  the module is only needed when offline mode is actually used.
- L54: `response = ollama.chat(model=model, messages=messages)` — ask Ollama's chat API for a reply;
  `model=` is the model name (e.g. `"gemma4"`), `messages=` is the whole conversation so far.
- L55: `return response["message"]["content"]` — `response` is a dict; `["message"]` gets the
  message dict; `["content"]` gets the reply text.

### L58–63: `def call_online_litellm(messages: list[dict[str, str]], model: str) -> str:`
Query an online LLM via LiteLLM.
- L60: `from litellm import completion` — lazy import of the `completion` function from `litellm`
  (again inside the function, because it is only needed for online mode).
- L62: `response = completion(model=model, messages=messages)` — same shape as Ollama's call;
  LiteLLM gives a uniform API for many providers.
- L63: `return response.choices[0].message.content` — OpenAI-style response object: `choices[0]`
  is the first choice, `.message` the message, `.content` the reply text.

### L66–85: `def generate_reply(messages, mode, online_model, offline_model) -> tuple[str, str]:`
The router: decide which backend to use, call it, and report which backend actually answered.
- L72: docstring — "Route between online (LiteLLM) and offline (Ollama) models."
- L73: `use_online = False` — default: do not use the online backend.
- L74–75: `if mode == "online": use_online = True` — if the user forced `--mode online`, go online.
- L76–77: `elif mode == "auto": use_online = is_online() and has_online_api_key()` — in `auto`
  mode, go online only if the machine has internet AND an API key.
- L79–83:
  - `if use_online:` — only if we decided to use the online backend.
  - L80–81: `try: return call_online_litellm(messages, online_model), f"online:{online_model}"` —
    call the online function and return the tuple (reply text, label like
    `online:gemini/gemini-2.5-flash`).
  - L82: `except Exception as exc:` — if the online call raised anything, print the yellow warning at
    L83: `Online call failed (...); falling back to offline Ollama...` — and execution continues
    past the `if` block to L85.
- L85: `return call_offline_ollama(messages, offline_model), f"offline:{offline_model}"` — the
  offline call always runs when we get here (mode was offline, or online was tried and failed, or
  auto found nothing online). Returns the tuple (reply text, label like `offline:gemma4`).
- Why the label? `handle_turn` prints it at L146 so you can see which backend answered.
- The `-> tuple[str, str]` annotation means it returns a tuple of two strings.

### L88–90: `def extract_shell_commands(text: str) -> list[str]:`
Pull out any ` ```run_shell ... ``` ` blocks from the model's reply.
- L89: docstring — "Extract ```run_shell ... ``` blocks from model output."
- L90: `return [m.strip() for m in re.findall(r"```run_shell\s*(.*?)```", text, re.DOTALL) if m.strip()]`
  - `re.findall(pattern, text, re.DOTALL)`: finds all matches of the regex in `text`; `re.DOTALL`
    makes `.` match newlines so multi-line blocks are found.
  - The regex `r"```run_shell\s*(.*?)```"`: literal triple backtick + the word `run_shell`, then
    `\s*` (any whitespace), then a capturing group `(.*?)` — non-greedy any characters — then the
    closing triple backtick. Because `(.*?)` is non-greedy, the match ends at the first closing
    backticks after the content.
  - With `findall` and exactly one capturing group, findall returns the captured strings (the
    command text), not the whole match.
  - `[m.strip() for m in ...]`: list comprehension — for each match string `m`, append `m.strip()`.
  - `if m.strip()` — filter: skip matches whose stripped text is empty.
  - Result: a list of the commands, e.g. `["ls -la"]`.

### L93–121: `def run_command_with_confirmation(cmd: str) -> str:`
Ask the user before running a proposed shell command.
- L95: `console.print(Panel(cmd, title="Proposed Terminal Command", border_style="yellow"))` —
  show the proposed command inside a yellow box.
- L96–99:
  - `try: answer = input("Run this command? [y/N]: ").strip().lower()` — `input` prints the prompt
    and waits for a line of terminal input; `.strip()` removes surrounding whitespace; `.lower()`
    lowercases it, so "Y" or "YES" also work.
  - `except EOFError: return "Command cancelled (no input)."` — if there is no input (e.g. stdin
    closed), treat it as cancelled.
- L101–102: `if answer not in ("y", "yes"): return "User declined to run the command."` — anything
  other than `y` or `yes` (including empty, `n`, or anything else) means: do not run, and tell the
  model the user declined.
- L104–112: the actual run:
  - `proc = subprocess.run(cmd, shell=True, text=True, capture_output=True)`
  - `cmd`: the command string to run.
  - `shell=True`: run it through the shell (`/bin/sh`), so redirects and pipes behave like typing
    the command yourself. (This is also why the confirmation gate matters.)
  - `text=True`: make `proc.stdout` / `proc.stderr` be strings rather than bytes.
  - `capture_output=True`: capture stdout and stderr instead of letting them go straight to the
    terminal, so they can be shown to the user and fed back to the model.
- L113–119: build the result text:
  - L113: `output = ""` — start with an empty string.
  - L114–115: `if proc.stdout: output += f"STDOUT:\n{proc.stdout}\n"` — if there was standard
    output, append the line `STDOUT:` followed by the output followed by a newline.
  - L116–117: same for `STDERR`.
  - L118: `output += f"EXIT_CODE: {proc.returncode}"` — append the exit code (0 means success).
  - L119: `return output.strip()` — strip surrounding whitespace and return the result string.
- L120–121: `except Exception as exc: return f"Execution error: {exc}"` — if anything goes wrong
  while running, return an error message so the model can see and react to it.

### L124–159: `def handle_turn(user_input: str, messages: list[dict[str, str]], mode: str, online_model: str, offline_model: str) -> None:`
One round of conversation: get the reply, show it, run any proposed commands, feed the outputs back,
and repeat — the "tool loop".
- L131: `messages.append({"role": "user", "content": user_input})` — append the new user message to
  the shared conversation list. A message is a dict with keys `role` (`"user"`, `"assistant"`, or
  `"system"`) and `content` (the text). `messages` is passed in and mutated, so the conversation
  grows across turns.
- L133: `for _ in range(5):  # Max 5 tool-use iterations per turn` — a `for` loop over a range of
  5; `_` is the throwaway loop variable (by convention). So there are at most 5 iterations of the
  loop: at most 5 model replies per turn.
- L134–143: error handling around the model call:
  - L135: `reply, active_model = generate_reply(messages, mode, online_model, offline_model)` —
    call the router (section above). Tuple unpacking: `reply` gets the text, `active_model` the
    label.
  - L136–143: `except Exception as exc:` — if the model call raised, print an error in red with a
    dim tip telling the user to ensure Ollama is running and the model is pulled, then
    `messages.pop()` — remove the just-appended user message so the conversation is not left
    dangling — and `return`.
- L145: `messages.append({"role": "assistant", "content": reply})` — append the model's reply as an
  assistant message.
- L146: `console.print(f"[dim][{active_model}][/dim]")` — print the backend label in dim style,
  e.g. `[offline:gemma4]`.
- L147: `console.print(Markdown(reply))` — render the reply with rich Markdown so formatting shows
  nicely in the terminal.
- L149: `commands = extract_shell_commands(reply)` — pull any `run_shell` blocks out of the reply.
- L150–151: `if not commands: break` — if there were none, this turn is done → `break` out of the
  loop.
- L153–156: `outputs = []`, then a loop:
  - L154: `for cmd in commands:`
  - L155: `result = run_command_with_confirmation(cmd)` — show the box, ask, run each command.
  - L156: `outputs.append(f"$ {cmd}\n{result}")` — remember `$ cmd` plus the command's result.
- L158: `combined = "\n\n".join(outputs)` — join the per-command records with blank lines between
  them.
- L159: `messages.append({"role": "user", "content": f"Command output:\n{combined}"})` — append a new
  user message carrying the command outputs so the model can read them and continue reasoning; the
  loop then goes back to the model (up to 5 times total).

### L162–209: `def main() -> None:`
Program entry point.
- L163: `parser = argparse.ArgumentParser(description="Iris: Terminal AI Assistant (Online + Offline)")`
  — create the argument parser.
- L164: `parser.add_argument("prompt", nargs="*", help="Optional one-shot prompt")` — positional
  argument: zero or more words of a prompt. `nargs="*"` means "as many as you provide"; later
  L179 does `" ".join(args.prompt)` to turn the words back into one string.
- L165–170: `parser.add_argument("--mode", choices=("auto", "online", "offline"), default="auto", help="Force online, offline, or auto-detect (default: auto)")`
  — the `--mode` flag; you can only pass auto/online/offline; default is auto.
- L171–172: `--online-model` and `--offline-model` flags, defaulting to the values computed at
  L21–22.
- L173: `args = parser.parse_args()` — parse the actual command-line arguments.
- L175: `CONFIG_DIR.mkdir(parents=True, exist_ok=True)` — create `~/.iris/` if it does not exist
  (`parents=True` also creates missing parent directories; `exist_ok=True` means "fine if it
  already exists").
- L176: `messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]` —
  initialize the conversation: a single system message holding the system prompt. (The `messages`
  variable is explicitly typed as `list[dict[str, str]]`: a list of dicts whose keys and values are
  strings.)
- L178–180: one-shot mode: `if args.prompt:` — if the user typed a prompt on the command line, run
  `handle_turn(" ".join(args.prompt), messages, args.mode, args.online_model, args.offline_model)`
  and then `return` (the program ends after this turn).
- L182–189: interactive banner: `console.print(Panel(...))` — print a cyan panel: "Iris is online.
  Type your request, or `/exit` to quit. Commands proposed by Iris always ask for `[y/N]`
  confirmation." (A small wording quirk: it says "Iris is online" even in offline mode.)
- L190: `session = PromptSession(history=FileHistory(str(HISTORY_FILE)))` — create the interactive
  prompt session; the prompt-history file is `~/.iris/history` (`str()` converts the `Path` to a
  string, which `FileHistory` expects).
- L192–197: the main interactive loop:
  - L194: `user_input = session.prompt("iris> ").strip()` — display the prompt `iris> ` and wait for
    the user to type; `.strip()` removes surrounding whitespace.
  - L195–197: `except (KeyboardInterrupt, EOFError): console.print("\nGoodbye!"); break` — Ctrl+C or
    Ctrl+D (EOF) → print "Goodbye!" and exit the loop (end the program).
- L199–200: `if not user_input: continue` — empty input: loop again (nothing to do).
- L201–203: `if user_input in ("/exit", "exit", "quit"): console.print("Goodbye!"); break` — quit
  commands → print Goodbye and end.
- L204–207: `if user_input == "/clear": messages = [{"role": "system", "content": SYSTEM_PROMPT}];
  console.print("[dim]Conversation cleared.[/dim]"); continue` — reset the conversation to just
  the system prompt and continue to the next prompt.
- L209: `handle_turn(user_input, messages, args.mode, args.online_model, args.offline_model)` — the
  normal path: send the user's line through the whole turn machinery described above.

### L212–213: the entry-point idiom
```
if __name__ == "__main__":
    main()
```
Classic Python entry-point idiom: when the file is run directly as a script, `__name__` is
`"__main__"`, so call `main()`. If the file is imported as part of the package (as it is via
`iris = "iris.cli:main"` in pyproject.toml), this block does not run — `main()` is only called
because the entry point references it.

---

## 2. `iris/__init__.py` — package init, line by line

The file has 3 lines.

### L1: `"""Iris: Always-available terminal AI assistant."""`
Module docstring (a string literal placed at the top of a module, used as documentation).

### L2: (blank line)
Just separates the docstring from the rest of the file.

### L3: `__version__ = "0.1.0"`
Module-level assignment that defines the package's version attribute: after `import iris`,
`iris.__version__` reads `"0.1.0"`. Tools and docs can read this to know the version.
