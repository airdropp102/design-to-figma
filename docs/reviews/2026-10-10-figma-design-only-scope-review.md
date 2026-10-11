# Review Notes — Figma Design Agent Only v3.1

**Status:** Scope approved; revised technical spec awaiting review. **Implementation code unchanged.**

## Corrected interpretation

- `./agent design` is a **Figma UI/UX design** workflow, not an application development lifecycle.
- Support scripts under `scripts/` are allowed solely to run the harness (`setup`, workflow, state, QA).
- APP_SPEC can name iOS/Android/web platform design conventions but must not cause product source-code generation.
- Brainstorming ends at an approved **design brief**, then resumes directly into Figma planning/rendering/QA.
- Completion requires verified P0 Figma screens, required UI states, P0 flows, structural and visual QA, and reporting.
- Prototype links are conditional on requested scope **and verified TalkToFigma capabilities**.

## Still unchanged

- Option A: TalkToFigma-only, no Official Figma MCP.
- Claude + Codex run against common MCP; one writer.
- Existing state v2, `intent.py`, assets workflow and recovery preserved.
- Draft implementation plan remains gated on approval of this revised written spec.

## Known changes required during implementation (not applied yet)

- Replace `Stack mục tiêu` field in `specs/APP_SPEC.template.md` with platform design guidelines.
- Remove `Figma channel ID` from APP_SPEC and move to local runtime settings.
- Add design-only invariant to AGENTS.md and CLAUDE.md.
- Build CLI bootstrap/controller/doctor and QA reporting per spec; no app-generation commands.
