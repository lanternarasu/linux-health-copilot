---
doc: checklist
status: approved
---

# Build Checklist

Build mode: learn

## Slices

- [x] **1. Confirm and run the fixed memory diagnostic**
  Becomes usable: In Ubuntu WSL, `python main.py ask "check my available memory and list the top 3 processes using the most RAM"` explains the request, shows the fixed read-only diagnostic and safety label, waits for explicit confirmation, then displays raw results and a plain-English interpretation. AI-generated command text is never executed.
  Why now: This delivers the unique kernel end to end and tests the API, allowlist, and local Linux commands before adding the manual-only follow-up.
  PRD ref: `prd.md > The Core Journey` (steps 1-4), `Features and Behavior > Request Explanation and Read-Only Diagnostics`, `Graceful Error Handling`.
  Spec ref: `spec.md > The Core Journey Through the System`, `Stack`, `Where It Runs and How Someone Tries It`, `Components > CLI and Configuration`, `Gemini Request and Response`, `Safety Gate and Confirmation`, `Diagnostic and Terminal Output`, `External Services and Dependencies`.
  Build: Create `main.py`, `requirements.txt`, `.env.example`, and the initial `README.md`; implement CLI/config loading, the Gemini `generate_content()` exchange, a local allowlist for `free` and `ps`, confirmation, output formatting, clean API/command errors, and fail-closed handling for unknown actions.
  Verify (mechanical): In Ubuntu WSL, run `python -m compileall -q main.py` and `python main.py --help`; with the learner's locally configured Gemini API key, run the memory request, confirm it, and verify the raw-output header and interpretation. Also run once without a configured key and verify a clean `[API ERROR]` instead of a traceback.
  Learner check: In WSL, try the memory request once with `n` and once with `y`; confirm the first run does not execute, and the second shows `free`/`ps` output and a short explanation. Share what feels clear or confusing before the follow-up slice.
  Commit: `Add confirmed read-only memory diagnosis`

- [x] **2. Add manual-only process advice and finish the demo guide**
  Becomes usable: A request to stop a high-memory process produces a yellow manual-only suggestion and never executes it. If no PID is included, the user may confirm a fresh read-only process check; the app then uses its result for the suggestion. The README explains setup, safety behavior, errors, and the 60-second demo.
  Why now: Once the core diagnostic works and has received early feedback, this completes the second half of the approved journey without expanding the allowlist.
  PRD ref: `prd.md > The Core Journey` (step 5), `Features and Behavior > State-Changing and Unverified Suggestions`, `States and Boundaries`, `Graceful Error Handling`.
  Spec ref: `spec.md > Components > Gemini Request and Response`, `Safety Gate and Confirmation`, `Diagnostic and Terminal Output`, `Data Model`, `Important Failure Modes`, `File Structure`, `Where It Runs and How Someone Tries It`.
  Build: Add the process-stop and unverified-command response paths, support a supplied PID or a confirmed fresh process check, preserve the never-execute boundary, and complete `README.md` with Ubuntu/WSL setup, `.env` configuration, examples, error guidance, and the recording sequence.
  Verify (mechanical): Run `python -m compileall -q main.py`, `python main.py --help`, and both demo requests in WSL. Confirm a process-stop suggestion shows the yellow manual-only tag and no prompt to execute it; verify an ambiguous/unrecognized action cannot invoke a command. Follow the README setup and demo commands.
  Learner check: Run the two-step 60-second demo in WSL, including the refreshed-PID confirmation when needed. Try one unfamiliar request and check that it remains manual-only; report any confusing output or needed changes.
  Commit: `Add manual-only process guidance and demo docs`

## Hands-on Checkpoints

- [x] Early usable behavior explored after slice 1. Feedback: the `n` default is clear and fail-closed; raw `free`/`ps` output before interpretation is transparent; the local allowlist is distinct from Gemini's role. The exact commands are already listed before the confirmation prompt, so the suggested preview is present.
- [x] Final kick-the-tires exploration and feedback completed after slice 2. The learner confirmed the read-only `ps` refresh, manual-only `kill <PID>` suggestion, and fail-closed boundary were clear.

## Final Review

- [ ] Final review complete — feedback resolved and learner confirms ready to ship

## Code Tour and App Map

- [ ] Learning activity complete — guided route, focused alternative, prior practice connected, or brief recap
- [ ] Optional edit and transfer reflection addressed — offered/declined/already covered/not applicable as appropriate
- [ ] `devpost/app-map.html` generated from finished code, checked, and shown, including a project-grounded practice to reuse

Activity and evidence: [what actually happened; real document/test/code references; unfinished work if interrupted]
Route and stops: [actual paths and symbols; guided stops completed, or reference-only route]
Edit outcome: [tried/kept/reverted/declined/not applicable; verification if changed]
Reflection: [offered/answered/declined/already covered — personal answer belongs only in the ignored profile]
Activity mode: [live app and editor, explicit static fallback, focused alternative, prior practice, or recap]

## Revisions
- The prior OpenAI key returned HTTP 429 `insufficient_quota` / `credit_balance_exhausted`, prompting the learner-approved switch to Gemini. After configuring Gemini, the WSL learner check verified that `n` cancels without running commands and `y` runs only the fixed `free`/`ps` diagnostics, showing raw output followed by Gemini's interpretation. The WSL venv stays under the Linux home directory to avoid colliding with the Windows venv in the shared workspace.
