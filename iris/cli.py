import argparse
import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()

CONFIG_DIR = Path.home() / ".iris"
HISTORY_FILE = CONFIG_DIR / "history"
DEFAULT_ONLINE_MODEL = os.environ.get("IRIS_ONLINE_MODEL", "gemini/gemini-2.5-flash")
DEFAULT_OFFLINE_MODEL = os.environ.get("IRIS_OFFLINE_MODEL", "gemma4")

SYSTEM_PROMPT = (
    "You are Iris, a helpful AI assistant living in the user's terminal. "
    "You can answer questions directly or propose shell commands to inspect files, "
    "run scripts, or manage the system. "
    "When you need to run a shell command on the user's laptop, respond with a "
    "fenced bash block marked `run_shell`, like this:\n"
    "```run_shell\nls -la\n```\n"
    "Wait for the command output before drawing conclusions. Keep responses concise."
)


def is_online(timeout: float = 1.5) -> bool:
    """Check if internet connectivity is available."""
    try:
        with socket.create_connection(("1.1.1.1", 443), timeout=timeout):
            return True
    except OSError:
        return False


def has_online_api_key() -> bool:
    """Check if a common cloud LLM API key is configured."""
    keys = ("GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY")
    return any(bool(os.environ.get(k)) for k in keys)


def call_offline_ollama(messages: list[dict[str, str]], model: str) -> str:
    """Query local Ollama server."""
    import ollama

    response = ollama.chat(model=model, messages=messages)
    return response["message"]["content"]


def call_online_litellm(messages: list[dict[str, str]], model: str) -> str:
    """Query online LLM via LiteLLM."""
    from litellm import completion

    response = completion(model=model, messages=messages)
    return response.choices[0].message.content


def generate_reply(
    messages: list[dict[str, str]],
    mode: str,
    online_model: str,
    offline_model: str,
) -> tuple[str, str]:
    """Route between online (LiteLLM) and offline (Ollama) models."""
    use_online = False
    if mode == "online":
        use_online = True
    elif mode == "auto":
        use_online = is_online() and has_online_api_key()

    if use_online:
        try:
            return call_online_litellm(messages, online_model), f"online:{online_model}"
        except Exception as exc:
            console.print(f"[yellow]Online call failed ({exc}); falling back to offline Ollama...[/yellow]")

    return call_offline_ollama(messages, offline_model), f"offline:{offline_model}"


def extract_shell_commands(text: str) -> list[str]:
    """Extract ```run_shell ... ``` blocks from model output."""
    return [m.strip() for m in re.findall(r"```run_shell\s*(.*?)```", text, re.DOTALL) if m.strip()]


def run_command_with_confirmation(cmd: str) -> str:
    """Prompt the user before running a shell command. Uses native sudo TTY if needed."""
    console.print(Panel(cmd, title="Proposed Terminal Command", border_style="yellow"))
    try:
        answer = input("Run this command? [y/N]: ").strip().lower()
    except EOFError:
        return "Command cancelled (no input)."

    if answer not in ("y", "yes"):
        return "User declined to run the command."

    try:
        # Runs directly in the user's terminal environment so native `sudo` prompts
        # work seamlessly with the user's current OS password without storing it.
        proc = subprocess.run(
            cmd,
            shell=True,
            text=True,
            capture_output=True,
        )
        output = ""
        if proc.stdout:
            output += f"STDOUT:\n{proc.stdout}\n"
        if proc.stderr:
            output += f"STDERR:\n{proc.stderr}\n"
        output += f"EXIT_CODE: {proc.returncode}"
        return output.strip()
    except Exception as exc:
        return f"Execution error: {exc}"


def handle_turn(
    user_input: str,
    messages: list[dict[str, str]],
    mode: str,
    online_model: str,
    offline_model: str,
) -> None:
    messages.append({"role": "user", "content": user_input})

    for _ in range(5):  # Max 5 tool-use iterations per turn
        try:
            reply, active_model = generate_reply(messages, mode, online_model, offline_model)
        except Exception as exc:
            console.print(
                f"[red]Error contacting model:[/red] {exc}\n"
                "[dim]Tip: For offline mode, ensure Ollama is running (`ollama serve`) "
                f"and the model is pulled (`ollama pull {offline_model}`).[/dim]"
            )
            messages.pop()
            return

        messages.append({"role": "assistant", "content": reply})
        console.print(f"[dim][{active_model}][/dim]")
        console.print(Markdown(reply))

        commands = extract_shell_commands(reply)
        if not commands:
            break

        outputs = []
        for cmd in commands:
            result = run_command_with_confirmation(cmd)
            outputs.append(f"$ {cmd}\n{result}")

        combined = "\n\n".join(outputs)
        messages.append({"role": "user", "content": f"Command output:\n{combined}"})


def main() -> None:
    parser = argparse.ArgumentParser(description="Iris: Terminal AI Assistant (Online + Offline)")
    parser.add_argument("prompt", nargs="*", help="Optional one-shot prompt")
    parser.add_argument(
        "--mode",
        choices=("auto", "online", "offline"),
        default="auto",
        help="Force online, offline, or auto-detect (default: auto)",
    )
    parser.add_argument("--online-model", default=DEFAULT_ONLINE_MODEL)
    parser.add_argument("--offline-model", default=DEFAULT_OFFLINE_MODEL)
    args = parser.parse_args()

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    if args.prompt:
        handle_turn(" ".join(args.prompt), messages, args.mode, args.online_model, args.offline_model)
        return

    console.print(
        Panel(
            "Iris is online. Type your request, or `/exit` to quit. "
            "Commands proposed by Iris always ask for `[y/N]` confirmation.",
            title="Iris Terminal AI",
            border_style="cyan",
        )
    )
    session = PromptSession(history=FileHistory(str(HISTORY_FILE)))

    while True:
        try:
            user_input = session.prompt("iris> ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input in ("/exit", "exit", "quit"):
            console.print("Goodbye!")
            break
        if user_input == "/clear":
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            console.print("[dim]Conversation cleared.[/dim]")
            continue

        handle_turn(user_input, messages, args.mode, args.online_model, args.offline_model)


if __name__ == "__main__":
    main()
