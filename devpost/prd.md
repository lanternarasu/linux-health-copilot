---
doc: prd
status: approved
---

# Linux Health Copilot and Command Advisor — Product Requirements

A lightweight command-line copilot for developers and system administrators troubleshooting memory use in Linux or WSL. It explains a proposed diagnostic, requires confirmation before running read-only checks, and never executes state-changing or unverified commands.
Source: `scope.md > The Unique Kernel`, `Who It's For`, `The Core Loop`, and `The POC Boundary`.

## The Core Journey
1. The user runs `python main.py ask "check my available memory and list the top 3 processes using the most RAM"` in a local Linux or WSL terminal.
2. Before running anything, the tool shows a 1–2 sentence explanation of its interpretation, the exact suggested command, a green `[READ-ONLY DIAGNOSTIC]` label, and `Execute command on system? [y/N]:`.
3. Only `y` or `yes` proceeds. Any other response, including an empty response, does not execute the command.
4. On success, the tool shows `--- RAW DIAGNOSTIC OUTPUT ---` and the raw results from the memory and process checks, followed by a 2–3 sentence plain-English interpretation.
5. If the user asks how to stop a high-memory process, the tool shows the suggested command with a yellow `[STATE-CHANGING SUGGESTION - MANUAL ONLY]` label, explains that it changes system state, and tells the user to run it manually if desired. It never offers to execute it.

## Screens and Layout
One text-only command-line interaction surface using the `ask` command. Each response is organized into clearly labeled explanation, command, safety status, prompt, output, or error sections as applicable. Safety labels use green for verified read-only diagnostics, yellow for manual-only or unverified suggestions, and red for errors.

## Features and Behavior

### Request Explanation and Read-Only Diagnostics
Source: `scope.md > The Core Loop` and `What "Working" Looks Like`.

- The tool explains the user's request in 1–2 plain-English sentences and displays the exact command it proposes to run.
- A verified read-only diagnostic is labeled `[READ-ONLY DIAGNOSTIC]` in green and requires the explicit `y/N` prompt before execution.
- Only `y` or `yes` authorizes execution. `n`, an empty response, or any other input must not execute the command.
- The memory demo checks available memory and lists the top three RAM-consuming processes, using diagnostics such as `free -h` and `ps`.
- After a successful run, the tool displays the raw command output under `--- RAW DIAGNOSTIC OUTPUT ---`, then a 2–3 sentence interpretation in plain English. The interpretation explains memory use and identifies the highest-RAM process and its PID when available.

### State-Changing and Unverified Suggestions
Source: `scope.md > The Unique Kernel`, `The Core Loop`, and `The POC Boundary`.

- A state-changing request, such as stopping a process, receives a suggested command and a yellow `[STATE-CHANGING SUGGESTION - MANUAL ONLY]` label. If no PID is supplied, the tool offers a confirmed, read-only process refresh and suggests the highest-memory process other than the copilot itself. PID 1 and the copilot's own PID never receive a stop suggestion. The tool explains that the action changes system state and may be run manually by the user if desired.
- The tool never executes state-changing or high-risk commands, including `kill`, `chmod`, or service restarts, and does not offer an execution prompt for them.
- If command parsing is ambiguous or the tool cannot guarantee that a proposed command is strictly read-only, it blocks execution and shows a yellow `[UNVERIFIED COMMAND - MANUAL ONLY]` label, the proposed command, and this explanation: “The safety parser could not guarantee this command is read-only. For your security, auto-execution is disabled. Review and run manually if desired.”

### Graceful Error Handling
Source: `scope.md > The POC Boundary`.

- If the AI API cannot be reached or the request fails due to API configuration, the tool displays a red `[API ERROR]` label, says the AI service could not be reached, suggests checking network connectivity or the `.env` API key, and exits without a raw traceback.
- If a confirmed read-only command fails, the tool displays a red `[COMMAND ERROR]` label, prints the system's raw stderr, and exits cleanly.

## States and Boundaries
- **Before confirmation:** No diagnostic command has run; the user sees the explanation, proposed command, safety label, and prompt.
- **Declined or unrecognized confirmation:** The command does not run unless the response is `y` or `yes`.
- **Successful diagnostic:** Raw output is followed by a short plain-English interpretation.
- **State-changing request:** The command is shown as manual-only and is never executed.
- **Unverified command:** Execution is blocked; the yellow warning and the specified safety explanation are shown.
- **API or network error:** A red API error and configuration/network hint are shown, followed by a clean exit.
- **Operating-system command error:** A red command error and raw stderr are shown, followed by a clean exit.
- **Supported environment:** Local Linux or WSL terminal; disk and broader log diagnosis are outside this proof of concept.

## Product Decisions
- The first demo focuses on memory availability and the top three RAM-consuming processes; disk checks are deferred to keep the workflow small.
- Read-only diagnostics require an explicit `y` or `yes` confirmation. All other responses leave the system unchanged.
- State-changing commands are suggestions only. Ambiguous or unverified commands are also blocked from execution.
- Stop-process advice must not target PID 1 or the running copilot process; when discovering a target, select the highest-memory process other than the copilot itself.
- Successful diagnostic output includes both raw system results and a short plain-English interpretation.
- Safety and error labels are color-coded in the terminal: green for verified read-only, yellow for manual-only or unverified, and red for errors.
- API/network and OS command failures produce helpful messages and clean exits rather than raw tracebacks.

## What We're Building
A Python CLI `ask` flow for the local Linux/WSL memory troubleshooting demo: explain and display a verified read-only memory/process command, require confirmation, show raw output plus an AI interpretation, and keep state-changing or unverified commands manual-only. Handle the specified API/network and command execution errors cleanly.

## Deferred From the POC
- Disk-space checks, because the learner chose to keep the first workflow focused on memory.
- Broader system health and log analysis, including `journalctl`, `/proc/meminfo`, and uptime.
- A separate `diagnose` command and support for a broad catalog of requests.

## Possible Later Enhancements
Add disk-space and log diagnosis, then consider a dedicated `diagnose` command after the memory workflow is working.

## Non-Goals
- Executing commands that modify system state, change permissions, or stop/restart processes.
- Executing a command whose read-only safety cannot be guaranteed.
- Building a complete Linux administration product or supporting every distribution and command.

## Open Questions
- None that block the proof-of-concept product definition. Implementation details and any remaining environment assumptions should be settled in `4-spec`.
