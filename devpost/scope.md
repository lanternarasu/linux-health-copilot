---
doc: scope
status: approved
---

# Linux Health Copilot and Command Advisor

A lightweight Python CLI that translates Linux troubleshooting requests into understandable command suggestions, runs only approved read-only diagnostics after confirmation, and explains risky actions without running them.

## The Unique Kernel
Natural-language command help is paired with a visible safety boundary: read-only diagnostics can run only after the user confirms, while state-changing commands are presented as manual suggestions and are never executed by the tool.

## Who It's For
Developers and system administrators working in Linux or WSL who need to investigate local performance problems without losing focus to command syntax or raw output.

## The Core Loop
The user asks how to check available memory and find the top RAM-consuming processes. The tool explains and offers a read-only check using `free -h` and `ps`, then runs it only after a `y/N` confirmation. If asked how to stop a high-memory process, it identifies the suggested command and warns that it changes system state; the user must run it manually if desired.

## Inspiration & Identity
Fast, lightweight, and terminal-native. Output should be clear and practical, with readable summaries and direct safety warnings.

## Why This Matters to the Learner
The learner wants to build practical Linux confidence and create a project that demonstrates those skills.

## What "Working" Looks Like
In a short local Linux/WSL demo, a user confirms a read-only memory and process check, sees the results explained, then asks how to stop a high-RAM process and receives a manual command suggestion with a clear warning. The tool does not execute the state-changing command.

## The POC Boundary
A Python CLI with an `ask` flow for the memory-check demo. It may execute only the scoped read-only memory and process diagnostics after explicit confirmation. State-changing or high-risk commands, including `kill`, `chmod`, and service restarts, are suggestions only and can never be executed. The tool uses an AI API for request interpretation and plain-English explanations, with the API key loaded from a local `.env` file.

## Later
Disk-space diagnosis; broader system-health and log analysis such as `journalctl`, `/proc/meminfo`, or uptime; a separate `diagnose` command; support for additional troubleshooting requests.

## Explicitly Cut
- Executing state-changing or high-risk commands, even after confirmation, to keep the proof of concept non-destructive.
- Disk and general log diagnosis in this first demo, to keep the workflow focused on memory.
- A complete system-administration product or broad command catalog, beyond the small local proof of concept.
