---
doc: spec
status: approved
---

# Linux Health Copilot and Command Advisor — Technical Spec

## How This Works, In Plain Language
The CLI reads the request and asks Gemini to interpret it, but the AI never runs commands. Python accepts only a fixed, approved memory-check action, shows the exact diagnostic and asks permission, then runs the built-in `free` and `ps` checks separately. Any other or unclear action is shown as manual-only. The app sends the relevant diagnostic text to Gemini for a short explanation, then prints the results and explanation in the terminal. Nothing about process results is saved between runs.

This keeps the app to one Python file and uses the libraries the learner selected, while placing the execution decision in local code rather than in the AI response.

## The Core Journey Through the System
PRD ref: `prd.md > The Core Journey`.

1. `argparse` reads the `ask` subcommand and the user's request.
2. The app loads `.env`, checks for the API key, and asks Gemini to classify the request and prepare an explanation or manual suggestion.
3. Python accepts only the known `memory_process_check` action. The displayed command is mapped from a fixed local definition; model-generated command text is never passed to `subprocess`.
4. The app prints the explanation, exact safe command, green status label, and confirmation prompt. Only `y` or `yes` continues; every other answer cancels.
5. Python runs the fixed `free -h` and `ps` argument lists separately with `shell=False`, captures output, and displays the raw results. It selects the top three process rows locally.
6. The app sends the relevant memory/process output to Gemini and displays its 2–3 sentence interpretation beneath the raw output.
7. For a request to stop a process, an explicitly supplied PID can be used to form a manual suggestion. If no PID is supplied, the app offers the approved read-only process check and asks for confirmation to obtain a current PID. It then displays a yellow manual-only suggestion; it never runs `kill`.

## Stack
- **Python 3.10 or later** — required by the current Google GenAI SDK and `python-dotenv` packages.
- **Standard library:** `argparse` for CLI arguments, `subprocess` for the two fixed diagnostics, `os` for environment access, and `json` for interpreting the AI response.
- **`google-genai` Python package** — the learner-approved official Google GenAI client. Use `google-genai>=2.33.0,<3`; the upper bound avoids an unreviewed major-version change.
- **`python-dotenv`** — loads local `.env` values into the environment. Use `python-dotenv>=1.2.4,<2`.
- **Terminal colors** — ANSI escape codes, with plain-text labels when color output is unavailable; no extra color dependency.

Docs: [Google GenAI Python SDK](https://github.com/googleapis/python-genai), [Gemini API quickstart](https://ai.google.dev/gemini-api/docs/quickstart?lang=python), [Gemini generateContent API](https://ai.google.dev/api/generate-content), [Gemini models](https://ai.google.dev/gemini-api/docs/models), [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing), [Google AI Studio API keys](https://aistudio.google.com/api-keys), [python-dotenv](https://pypi.org/project/python-dotenv/), [argparse](https://docs.python.org/3/library/argparse.html), [subprocess](https://docs.python.org/3/library/subprocess.html).

## Where It Runs and How Someone Tries It
- Runtime: local Ubuntu in WSL; no server or deployment.
- Requires Python 3.10+, `free`, `ps`, network access, and a Gemini API key with available quota for the selected model.
- Install and run from the project directory:

```bash
python3 -m venv ~/.venvs/linux-health-copilot
source ~/.venvs/linux-health-copilot/bin/activate
python -m pip install -r requirements.txt
cp -n .env.example .env
# Add the key to .env, then run:
python main.py ask "check my available memory and list the top 3 processes using the most RAM"
```

For the 60-second video, show the confirmed memory/process check, then a state-changing request that returns a manual-only suggestion. Deployment is optional; the local WSL terminal is the demo surface.

## Look and Feel
Terminal-native and concise: readable section labels, raw output in a distinct block, short plain-English explanations, and green/yellow/red safety and error labels. Respect `NO_COLOR` by retaining labels without ANSI color.

## Components

### CLI and Configuration
Implements `prd.md > The Core Journey` and `Graceful Error Handling`. Parse `ask`, load `.env`, select `GEMINI_MODEL` (default `gemini-3.5-flash-lite`), and fail clearly if `GEMINI_API_KEY` is missing.

### Gemini Request and Response
Implements `prd.md > Request Explanation and Read-Only Diagnostics` and `State-Changing and Unverified Suggestions`. Use one synchronous Google GenAI client and `client.models.generate_content(model=model, contents=content, config={"system_instruction": instructions, "response_mime_type": "application/json"})`. Classify requests as the approved memory check, a stop-process request, another state-changing suggestion, or unverified/manual-only. For successful diagnostics, send only the relevant captured output for interpretation. Parse JSON from `response.text`; missing, malformed, or unknown action data is unverified and cannot trigger execution. A process-stop command is constructed locally from a user-supplied PID or the highest-memory PID from the confirmed read-only process check, excluding the copilot's own process and PID 1. No Gemini tools or function calls are enabled.

### Safety Gate and Confirmation
Implements `prd.md > Request Explanation and Read-Only Diagnostics` and `State-Changing and Unverified Suggestions`. The only commands the app can run are fixed `free` and `ps` argument arrays with `shell=False`: the memory check uses both, while a stop-process request without a PID can use only `ps`. Each run requires `y` or `yes`. `top_process_pid()` skips the copilot's PID and PID 1; explicitly supplied self/system PIDs are also blocked from suggestions. Ignore model-provided command strings for execution. State-changing suggestions, including the locally constructed `kill <PID>`, never get an execution prompt and are never run by the app.

### Diagnostic and Terminal Output
Implements `prd.md > Request Explanation and Read-Only Diagnostics` and `States and Boundaries`. Capture stdout/stderr and return codes for `free` and `ps`, select the top three process rows in Python, print raw output under the required header, and print the AI interpretation afterward. Use ANSI colors when supported, retaining visible labels without color otherwise.

## Data Model
All app data lives in memory for one CLI invocation: user request, parsed action, captured diagnostic output, and any PID supplied or discovered during that run. There is no saved history or background process. `.env` is local configuration containing `GEMINI_API_KEY` and optional `GEMINI_MODEL`; the model default is `gemini-3.5-flash-lite`. The request and selected memory/process output, which may include process names and PIDs, are sent to Gemini for interpretation. No files, logs, or other system data are sent.

## File Structure

```text
project/
|-- main.py             # CLI, API calls, safety gate, diagnostics, and output
|-- requirements.txt    # google-genai and python-dotenv
|-- .env.example        # secret-free API/model settings template
|-- .gitignore          # excludes .env files and learner profile
|-- README.md           # Ubuntu/WSL installation, setup, usage, and demo
`-- devpost/
    |-- learner-profile.md  # ignored by git; personal learning context
    |-- scope.md
    |-- prd.md
    `-- spec.md
```

## External Services and Dependencies
- **Gemini Developer API:** `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`, called through `client.models.generate_content(...)`. Authentication uses `GEMINI_API_KEY` loaded by `python-dotenv`. JSON output is read from `response.text`; API exceptions use `google.genai.errors.APIError`. The input contains the natural-language request and, for result interpretation, only the selected diagnostic output. No Gemini tools or function calls are enabled. [API reference](https://ai.google.dev/api/generate-content).
- **Model:** `gemini-3.5-flash-lite` by default, overridable via `GEMINI_MODEL`; the learner also named `gemini-2.5-flash` as an option. The current pricing page lists Gemini 3.5 Flash-Lite as free on the free tier; rate limits and availability may change, so check before the demo. [Model details](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite) and [pricing](https://ai.google.dev/gemini-api/docs/pricing).
- **Local environment:** `free` and `ps` are provided by Ubuntu/WSL; they are not Python packages or remote services.

## Important Failure Modes
- **Missing API key or API/network/quota failure** -> red `[API ERROR]`, a hint to check connectivity, `GEMINI_API_KEY`, available quota, and model access, then clean exit. If interpretation fails after diagnostics ran, preserve the raw output and show the API error.
- **Malformed or unverified AI response** -> yellow `[UNVERIFIED COMMAND - MANUAL ONLY]`; display the safety explanation and do not execute anything.
- **Diagnostic unavailable or nonzero exit** -> red `[COMMAND ERROR]`, include raw stderr, and exit cleanly. If no eligible process rows remain after excluding PID 1 and the copilot itself, say so and do not suggest a PID-based command.
- **User declines confirmation** -> do not run the diagnostic; return without executing anything.

## What Was Simplified and Why
- One `main.py` file with small functions instead of a package — fewer moving pieces for a first Python project.
- One fixed memory/process allowlist action instead of arbitrary command execution — it demonstrates the safety boundary without pretending an AI-generated command is safe.
- No history or persistent PID cache — a missing PID is refreshed through the approved read-only process check, avoiding stale process information.
- No disk, journal, or general diagnostics — they are outside the approved memory-focused proof of concept.

## Decisions and Open Issues
- **Learner-approved:** official Google GenAI Python library, `python-dotenv`, `gemini-3.5-flash-lite` default with `GEMINI_MODEL` override (`gemini-2.5-flash` also named as an option), `GEMINI_API_KEY`, fixed allowlist, and local Ubuntu in WSL for testing and recording.
- **Environment adjustment:** keep the WSL virtual environment under `~/.venvs/linux-health-copilot`, outside the Windows-mounted project, so its Linux executables do not conflict with the Windows `.venv` already present in the shared workspace.
- **Safety uncertainty clarified:** an AI label cannot authorize shell execution. Only a locally defined action ID maps to fixed read-only argument arrays; all other, malformed, or ambiguous responses are manual-only.
- **Derived implementation detail:** use `shell=False` and separate `free`/`ps` argument lists, so pipes or generated shell syntax are never executed.
- **Verify early in the build:** confirm the API key has quota and access to the selected model; model availability and free-tier limits can change.
- **Provider revision:** replace OpenAI with the Gemini Developer API and `google-genai`; the learner approved the switch after OpenAI returned an insufficient-quota error. Product behavior and the local command safety boundary are unchanged.
- **Environment verification:** Ubuntu WSL 2 and Python 3.14.4 are available. The `google-genai` SDK is installed in the WSL venv; syntax parsing, CLI help, missing-key handling, and the live memory-check flow pass. The no-PID stop flow excludes the copilot and PID 1; explicit `process 158` wording is parsed locally and yields a manual-only suggestion without refreshing `ps` or executing `kill`. The learner verified the corrected behavior in WSL.
