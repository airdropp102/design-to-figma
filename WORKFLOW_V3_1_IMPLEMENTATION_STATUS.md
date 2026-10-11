# Workflow v3.1 Native Execution — Implementation Status

Date: 2026-10-10
Scope: Figma Design Agent Only; Claude/Codex + shared TalkToFigma MCP; no mobile/web application source code.

## Implemented and verified locally

- `./agent` CLI shell entrypoint + JSON result envelope and exit codes.
- Strict YAML policy; backend fixed to TalkToFigma.
- APP_SPEC validator: workspace path containment, goal/roles/P0/language/constraints, legacy channel warning, up to 25 explicitly listed screens; untrusted spec never executed as shell.
- Durable `design/WORKFLOW.json` checkpoint and journal, approval record tied to spec/brief hashes.
- OS file-lock Figma writer isolation in interactive session (conservatively held across full session).
- TalkToFigma pinned checkout verification + project-scope MCP registration (without removing unrelated servers).
- Read-only doctor, Bun socket lifecycle with owner PID identity; no claim that socket proves Figma readiness.
- Typed design-only phase prompts, state v2 bridge for WAL reconciliation, QA and delivery gates.
- Local mock tests for version-gated interactive prompt argument, artifact checks, unexpected states, legacy state v2.

## Not yet live verified / known incomplete integration

- Lockfile contains `null` for unverified Git SHAs and runtime versions; setup intentionally returns `ACTION_REQUIRED` until maintainers validate and pin exact versions.
- Full auto-install/smoke of Superpowers and UI UX Pro Max inside both real CLI runtimes is not verified; actual GUI/plugin installation may require operator interaction. `doctor` is conservative and cannot infer skills from a file path alone.
- A complete design session on Figma has **not** been executed. Session bootstrap and MCP registration syntax still require real-machine smoke testing against the pinned CLI versions.
- Figma connection, write permission, screen screenshots, plugin reconnect, 12 live acceptance cases, and MCP call reduction benchmark are **NOT_VERIFIED**.
- Checkpoint evidence is a local audit log and cannot cryptographically attest to real user approval/tool calls. Trust boundaries are clearly stated in spec.
- Full workflow concurrency of controller checkpoint files relies on atomic replace but controller-wide cross-process transitions are not yet protected by a process-level journal lock; no claim of distributed workflow concurrency safety.
- Socket port check probes TCP availability; it is **not** a WebSocket protocol or plugin handshake validation.
- Real Figma component/variant/prototype capabilities depend on installed TalkToFigma schema; unsupported prototype requirements must be reported, not marked complete.

## Verification evidence

- Local command: `python3 -m unittest discover -s tests -v`
- Result: 47 tests, 0 failures (includes 14 legacy state v2 tests).
- `python3 -m compileall -q scripts` exit 0.
- `./agent doctor --json` exit 3, returns `FIGMA_NOT_VERIFIED` (expected on this execution host).
- `./agent status --json` exit 0 and `NOT_STARTED` in clean bundle.

## Release gate

`G5_EndToEnd: NOT_VERIFIED` — do not deploy or claim unattended Figma design success until pinned CLI/skill smoke and I01–I12 are recorded in `evals/LIVE_RESULTS.md`.
