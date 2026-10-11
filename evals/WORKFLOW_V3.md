# Workflow v3.1: Figma Design Agent Only QA

## Local tests

`python3 -m unittest discover -s tests -v` covers state v2 regressions, strict policy, APP_SPEC security, durable workflow transition, approval fingerprint, single-writer lock, project-scope MCP configs, pinned checkout, mock interactive CLI, socket ownership, doctor, WAL reconciliation and completion gates.

Local green is NOT equivalent to real Figma or runtime integration acceptance.

## Figma live acceptance matrix (I01–I12)

| ID | Live scenario | Evidence required |
|---|---|---|
| I01 | Setup Codex runtime + skills | CLI versions, successful skill invocations |
| I02 | Setup Claude runtime + skills | CLI versions, successful skill invocations |
| I03 | Setup repeat / preserve other MCPs | config diff and backups |
| I04 | Connect TalkToFigma plugin/channel | join_channel tool response |
| I05 | Figma file/page identity | get_document_info output |
| I06 | Brainstorm + one user approval | user session reference and brief hashes |
| I07 | Design system + components | Figma node IDs / screenshot |
| I08 | P0 screen & state coverage | state.json QA + exported frames |
| I09 | Crash after create timeout | no duplicated root after reconcile |
| I10 | MCP call count baseline vs v3.1 | same spec/model snapshot, 3 runs each |
| I11 | Resume after WebSocket/plugin disconnect | WAL and tool evidence |
| I12 | Delivery code-free + QA | report, state coverage, artifact inventory |

Only mark release G5 PASS after completing these against a disposable Figma file with one writer, and saving evidence. Do not use the unit-test count as live evidence.
