# Linux Health Copilot and Command Advisor

A small Python command-line proof of concept for checking memory use in Ubuntu/WSL. It explains a request, offers fixed read-only diagnostics, and asks before running them. AI-generated command text is never executed; only the local `free` and `ps` allowlist can run.

## Requirements

- Ubuntu or Ubuntu in WSL
- Python 3.10 or later
- A Gemini API key from Google AI Studio
- The Linux `free` and `ps` commands

## Install

From the project directory in Ubuntu/WSL:

```bash
python3 -m venv ~/.venvs/linux-health-copilot
source ~/.venvs/linux-health-copilot/bin/activate
python -m pip install -r requirements.txt
cp -n .env.example .env
```

Edit `.env` and add your Gemini key. If `.env` already exists, edit that file in place; do not overwrite it with the example:

```dotenv
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

Keep `.env` private. It is excluded from Git; `.env.example` contains placeholders only. The model can be changed by editing `GEMINI_MODEL` (for example, `gemini-2.5-flash`). Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/apikey).

## Run the memory check

```bash
python main.py ask "check my available memory and list the top 3 processes using the most RAM"
```

The tool shows its explanation and exact proposed read-only commands. It runs them only if you type `y` or `yes`; any other input cancels. The output includes the raw results and an AI-written plain-English interpretation.

## Get a manual-only stop suggestion

If you already know the process ID, include it in the request:

```bash
python main.py ask "how do I stop process 4242?"
```

To ask about the highest-memory process without supplying a PID:

```bash
python main.py ask "how do I stop the highest memory-consuming process?"
```

Without a PID, the tool offers to run the fixed, read-only `ps` check after confirmation, then suggests `kill <PID>` for the highest-memory process other than the copilot itself. It never suggests PID 1 or its own PID, and never runs `kill` or any other state-changing command.

## Safety

- The app uses a fixed local allowlist for `free -h` and `ps -eo pid,comm,%mem,rss --sort=-%mem`.
- If a stop-process request has no PID, only the allowlisted `ps` check can be run, and only after the same `y/N` confirmation.
- Commands run as argument lists with `shell=False`. Model-generated command text is never passed to the operating system.
- State-changing, ambiguous, or unverified requests are manual-only and are never executed by this tool.
- Process names and PIDs from the selected diagnostic output are sent to Gemini for interpretation. No files or logs are sent.
- Use only on a Linux/WSL environment you are authorized to inspect.

## Troubleshooting

- `[API ERROR]`: check that `.env` contains a valid `GEMINI_API_KEY`, your network is available, and your Google AI Studio project has quota and access to the selected model. Resolve quota or billing errors in Google AI Studio before retrying.
- `[COMMAND ERROR]`: read the displayed stderr; confirm Ubuntu provides `free` and `ps` and that they can run for your user.
- `[UNVERIFIED COMMAND - MANUAL ONLY]`: the app could not safely map the request to its fixed diagnostic action, so it did not execute anything.

## 60-second demo

1. Run the memory-check command above and type `y` at the confirmation prompt.
2. Show the raw `free` and top-process output followed by the plain-English explanation.
3. Ask how to stop a high-memory process and show that the command is presented as manual-only, never executed.

Disk checks, journal analysis, and additional diagnostics are outside this proof of concept.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
