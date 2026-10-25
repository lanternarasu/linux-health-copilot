"""Linux Health Copilot: a small, fail-closed Linux diagnostics CLI."""

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Any

from google import genai
from dotenv import load_dotenv
from google.genai import errors

DEFAULT_MODEL = "gemini-3.5-flash-lite"
MEMORY_ACTION = "memory_process_check"
STOP_PROCESS_ACTION = "stop_process"
STATE_CHANGE_ACTION = "state_changing_suggestion"
SAFETY_MESSAGE = (
    "The safety parser could not guarantee this command is read-only. "
    "For your security, auto-execution is disabled. Review and run manually if desired."
)

# Commands are fixed here. Never execute text returned by the model.
MEMORY_DIAGNOSTICS = (
    ("free -h", ["free", "-h"]),
    ("ps -eo pid,comm,%mem,rss --sort=-%mem", ["ps", "-eo", "pid,comm,%mem,rss", "--sort=-%mem"]),
)

COLORS = {"green": "\033[32m", "yellow": "\033[33m", "red": "\033[31m"}
RESET = "\033[0m"


def print_status(label: str, color: str) -> None:
    """Print a status label, retaining meaning when ANSI color is unavailable."""
    if "NO_COLOR" not in os.environ and sys.stdout.isatty():
        print(f"{COLORS[color]}{label}{RESET}")
    else:
        print(label)


def clean_terminal_text(value: str) -> str:
    """Remove control characters from text returned by an external service."""
    return re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", value)


def make_client() -> tuple[genai.Client | None, str]:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        return None, "GEMINI_API_KEY is missing. Add your key to the local .env file."

    try:
        client = genai.Client(api_key=api_key)
    except errors.APIError as exc:
        return None, str(exc)
    return client, ""


def call_model(client: genai.Client, model: str, instructions: str, content: str) -> str:
    response = client.models.generate_content(
        model=model,
        contents=content,
        config={
            "system_instruction": instructions,
            "response_mime_type": "application/json",
        },
    )
    return response.text or ""


def classify_request(client: genai.Client, model: str, request: str) -> dict[str, Any] | None:
    instructions = (
        "You classify Linux troubleshooting requests and write concise explanations. "
        "Return only a JSON object with keys action_id, explanation, suggested_command, "
        "and reason. Use memory_process_check only for checking available memory or "
        "top RAM-consuming processes. Use stop_process when the user asks how to stop "
        "a high-memory process or free memory by stopping one. Use "
        "state_changing_suggestion for other requests to change system state, such as "
        "restarting services or changing permissions. Use manual_only for requests that "
        "do not fit these categories or whose safety is unclear. Never suggest that the "
        "application execute a command. For state_changing_suggestion, include a manual "
        "command and explain why it is restricted. Do not invent a PID or claim you "
        "inspected the user's system."
    )
    try:
        response_text = call_model(client, model, instructions, request)
        result = json.loads(response_text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None

    if not isinstance(result, dict):
        return None
    return result


def interpret_diagnostics(
    client: genai.Client, model: str, request: str, diagnostic_text: str
) -> str | None:
    instructions = (
        "Explain Linux memory and process diagnostic output in plain English in 2-3 "
        "sentences. Use only the supplied output. Do not claim a diagnosis beyond the "
        "evidence, and do not recommend killing or changing processes. Return a JSON "
        "object with one string key, interpretation."
    )
    try:
        response_text = call_model(
            client,
            model,
            instructions,
            f"User request: {request}\n\nDiagnostic output:\n{diagnostic_text}",
        )
        result = json.loads(response_text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None

    interpretation = result.get("interpretation") if isinstance(result, dict) else None
    return clean_terminal_text(interpretation) if isinstance(interpretation, str) else None


def top_process_output(output: str) -> str:
    """Keep the ps header and the three highest-memory process rows."""
    lines = output.splitlines()
    return "\n".join(lines[:4])


def requested_pid(request: str) -> int | None:
    match = re.search(
        r"\b(?:pid|process(?:\s+id)?)\s*[:#]?\s*(\d+)\b",
        request,
        re.IGNORECASE,
    )
    if match is None:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def top_process_pid(output: str) -> int | None:
    lines = output.splitlines()
    for line in lines[1:]:
        fields = line.split()
        if not fields:
            continue
        try:
            pid = int(fields[0])
        except ValueError:
            continue
        if pid > 1 and pid != os.getpid():
            return pid
    return None


def confirm_read_only(commands: list[tuple[str, list[str]]]) -> bool:
    print("\nProposed read-only commands:")
    for display_command, _ in commands:
        print(f"  {display_command}")
    print_status("[READ-ONLY DIAGNOSTIC]", "green")

    try:
        confirmation = input("Execute command on system? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled; no command was run.")
        return False

    if confirmation not in {"y", "yes"}:
        print("Cancelled; no command was run.")
        return False
    return True


def show_state_change_suggestion(command: str, reason: str = "") -> None:
    print_status("[STATE-CHANGING SUGGESTION - MANUAL ONLY]", "yellow")
    print(f"Suggested command: {clean_terminal_text(command)}")
    print("This is a state-changing command. Run this manually in your terminal if desired.")
    if reason.strip():
        print(clean_terminal_text(reason.strip()))
    print("Review the command and target process before running it.")


def run_diagnostic(label: str, arguments: list[str]) -> str | None:
    try:
        result = subprocess.run(
            arguments,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )
    except OSError as exc:
        print_status("[COMMAND ERROR]", "red")
        print(f"{label}: {exc}", file=sys.stderr)
        return None

    if result.returncode != 0:
        print_status("[COMMAND ERROR]", "red")
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
        else:
            print(f"{label} exited with status {result.returncode}.", file=sys.stderr)
        return None

    output = result.stdout.strip()
    return top_process_output(output) if label.startswith("ps ") else output


def ask(request: str) -> int:
    client, error = make_client()
    if client is None:
        print_status("[API ERROR]", "red")
        print(f"The AI service could not be reached: {error}")
        print("Check your network connection, GEMINI_API_KEY in .env, API quota, and model access.")
        return 1

    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    try:
        action = classify_request(client, model, request)
    except errors.APIError:
        print_status("[API ERROR]", "red")
        print("The AI service could not be reached while interpreting your request.")
        print("Check your network connection, GEMINI_API_KEY in .env, API quota, and model access.")
        return 1

    if action is None:
        print_status("[UNVERIFIED COMMAND - MANUAL ONLY]", "yellow")
        print(SAFETY_MESSAGE)
        return 0

    explanation = action.get("explanation")
    if isinstance(explanation, str) and explanation.strip():
        print(clean_terminal_text(explanation.strip()))

    action_id = action.get("action_id")

    if action_id == STOP_PROCESS_ACTION:
        pid = requested_pid(request)
        pid_was_discovered = pid is None
        if pid is None:
            process_check = [MEMORY_DIAGNOSTICS[1]]
            if not confirm_read_only(process_check):
                return 0

            display_command, arguments = process_check[0]
            process_output = run_diagnostic(display_command, arguments)
            if process_output is None:
                return 1

            print("\n--- RAW DIAGNOSTIC OUTPUT ---")
            print(f"\n$ {display_command}")
            print(process_output or "(no output)")
            pid = top_process_pid(process_output)

        if pid is None:
            print_status("[STATE-CHANGING SUGGESTION - MANUAL ONLY]", "yellow")
            print("No process ID was available, so no stop command was suggested.")
            print("No state-changing command was run.")
            return 0
        if pid <= 1 or pid == os.getpid():
            print_status("[STATE-CHANGING SUGGESTION - MANUAL ONLY]", "yellow")
            print(f"PID {pid} is protected or belongs to this copilot; no stop command was suggested.")
            print("No state-changing command was run.")
            return 0

        reason = "The default kill signal asks the process to shut down cleanly."
        if pid_was_discovered:
            reason = (
                "This is the highest-memory process other than this copilot. " + reason
            )
        show_state_change_suggestion(
            f"kill {pid}", reason,
        )
        return 0

    if action_id == STATE_CHANGE_ACTION:
        suggested_command = action.get("suggested_command")
        reason = action.get("reason")
        if isinstance(suggested_command, str) and suggested_command.strip():
            show_state_change_suggestion(
                suggested_command.strip(), reason if isinstance(reason, str) else ""
            )
        else:
            print_status("[UNVERIFIED COMMAND - MANUAL ONLY]", "yellow")
            print(SAFETY_MESSAGE)
        return 0

    # The model can select only this fixed local action; its command text is ignored.
    if action_id != MEMORY_ACTION:
        print_status("[UNVERIFIED COMMAND - MANUAL ONLY]", "yellow")
        suggested_command = action.get("suggested_command")
        reason = action.get("reason")
        if isinstance(suggested_command, str) and suggested_command.strip():
            print(f"Suggested command (manual only): {clean_terminal_text(suggested_command.strip())}")
        if isinstance(reason, str) and reason.strip():
            print(clean_terminal_text(reason.strip()))
        print(SAFETY_MESSAGE)
        return 0

    if not confirm_read_only(list(MEMORY_DIAGNOSTICS)):
        return 0

    outputs: list[tuple[str, str]] = []
    for display_command, arguments in MEMORY_DIAGNOSTICS:
        output = run_diagnostic(display_command, arguments)
        if output is None:
            return 1
        outputs.append((display_command, output))

    print("\n--- RAW DIAGNOSTIC OUTPUT ---")
    for display_command, output in outputs:
        print(f"\n$ {display_command}")
        print(output or "(no output)")

    diagnostic_text = "\n\n".join(f"$ {command}\n{output}" for command, output in outputs)
    try:
        interpretation = interpret_diagnostics(client, model, request, diagnostic_text)
    except errors.APIError:
        interpretation = None

    if interpretation is None:
        print_status("[API ERROR]", "red")
        print("The AI service could not be reached while interpreting the diagnostic output.")
        print("Check your network connection, GEMINI_API_KEY in .env, API quota, and model access.")
        return 1

    print("\n--- PLAIN-ENGLISH INTERPRETATION ---")
    print(interpretation)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Get safe Linux command guidance and run approved read-only diagnostics."
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)
    ask_parser = subparsers.add_parser("ask", help="Ask a Linux troubleshooting question")
    ask_parser.add_argument("request", help="Describe the Linux task or issue")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.subcommand == "ask":
        return ask(args.request)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
