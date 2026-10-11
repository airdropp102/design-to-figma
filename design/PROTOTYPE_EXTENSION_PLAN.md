# TalkToFigma prototype extension implementation plan

Goal: editable Fashion v2 screens and real Figma prototype reactions; no product application code.
Architecture: generated local TalkToFigma server/plugin copies, leaving pinned vendor and existing identity plugin intact. A constrained prototype tool verifies file/page, declared owned roots, all sources and destinations before writing. Use Figma setReactionsAsync and return live reaction readback. Preserve unrelated nodes and reactions.

- [ ] Write failing tests for async reactions, foreign-page/root rejection before any write, replace semantics and live readback.
- [ ] Implement handler and MCP schema; deterministic generator builds isolated local plugin/server.
- [ ] Verify tests, generated syntax and real MCP tools/list.
- [ ] Reconcile canvas and build editable homepage, detail, booking and confirmation through state transactions, with asset references and visual exports.
- [ ] Request plugin restart and MCP reload only after files and editable screens are concrete.
- [ ] On reconnect, apply transitions and scrolling to owned screens; verify live reactions and provide Play link. Do not claim playback verification without actual evidence.

Sources: https://developers.figma.com/docs/plugins/api/Reaction/ ; https://developers.figma.com/docs/plugins/api/Action/ ; https://developers.figma.com/docs/plugins/api/Transition/
