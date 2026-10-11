# Fashion v2 — Motion / prototype request

## Prototype applied — channel oy9qymp2
Verified live prototypePluginVersion1.0.0, exact file/page and all131 owned nodes before begin-update. Applied22 source reactions using generated TalkToFigma MCP over stdio with writer lock; a separate read-only MCP call verified every trigger/action/destination/transition/duration. Home/detail now1440×900 with vertical scrolling and clipsContent=true. Live evidence: `.agent/runtime/prototype-live-read.json`; screenshots: `design/previews/S28-prototype-viewport.png` through S31. All four viewport exports inspected; homepage's first export timed out, identity reconciled and one sequential retry succeeded.

Play URL: https://www.figma.com/proto/rXrX1FHInMsxbejkvSP9Wl/Untitled?page-id=0%3A1&node-id=69-204&starting-point-node-id=69%3A204&scaling=scale-down&content-scaling=fixed

Try: homepage Áo dài scrolls to product cards → An Nhiên opens detail → Đặt lịch thử opens demo form → Xem xác nhận navigates to success → Quay lại trang chủ. Overlay Đóng closes. Other product cards open the generic consultation demo, not separate product details. Color selectors remain static; fields are sample content. Light dissolve/scroll animation configured. No true3D/hover/parallax or actual data submission. Player click-through was not independently observed by the agent; user playback test remains pending. This is a4-screen prototype demonstration, not full P0/state coverage of the original spec.

## Editable rebuild + local extension prepared
S28 homepage `69:204` (81 editable child nodes), S29 detail `69:286` (23), S30 appointment demo `69:310` (17), S31 confirmation demo `69:328` (6). All read live and exported/visually checked before state done. Four screens total131 nodes including roots. Existing approved raster S27 preserved. Gallery palette and Inter retained; separate generated photos recorded in manifest.

Isolated local plugin: `.agent/plugins/talktofigma-prototype/manifest.json`; generated MCP: `.agent/mcp/talktofigma-prototype/server.ts`. Source handlers/generator under scripts; pinned vendor and original identity plugin untouched. apply_prototype supports click/hover/press, navigate/overlay/scroll/back/close, dissolve/Smart Animate/scroll animation, async readback, read-only reconciliation, and scroll viewport configuration. Unit tests verify identity/ownership rejection before writes, async reaction replacement, multiple triggers, read-only behavior and viewport validation. MCP tools/list verified initial schema; current generated schema also includes readOnly and viewportHeights.

Pending interaction payload: `design/PROTOTYPE_INTENT.json` (22 source reactions, four owned roots, home/detail900px scroll viewports). No interaction has been applied yet. Waiting for user to load new local plugin and provide channel. Then reconcile live; add prototype style intents to recipes; begin-update each affected screen; apply through TalkToFigma MCP; verify live reaction readback and viewport export before done-update. Figma Presentation playback still requires click-through testing; no real3D model or garment renderer.

User visually accepted Fashion v2 direction on 2026-10-11 and requested movement/3D plus a playable prototype. Acceptance is visual direction only; interactive delivery remains incomplete.

## Proposed interaction scope
- Hero entry: subtle opacity/vertical reveal, 400–600 ms; avoid distracting repeated animation.
- Product hover: restrained image scale and CTA feedback, 150–250 ms; retain a click/touch path.
- Collection/product navigation: short dissolve or Smart Animate, 250–350 ms, preserving spatial continuity.
- Appointment CTA: open consultation overlay, 250 ms; close/back routes required.
- 3D direction: simulated depth/parallax proposal only. No real 3D garment/model asset exists; do not claim a 360-degree garment viewer.
- Reduced-motion alternative: instant state changes or short fades, no parallax.

## Verified blocker
Joined rvu4uiiw and verified Untitled / rXrX1FHInMsxbejkvSP9Wl / Page 1 0:1. Current MCP exposes get_reactions (read existing prototype reactions) and create_connections (draw connector lines), but no tool to write reactions, transitions, flow starting points, or animation. Connector lines do not create a playable prototype.

S27 root 69:202 is one raster preview image in a child frame. Its heading, photos and buttons cannot animate independently or receive semantic prototype interactions without rebuilding editable layers and hotspots. No playable prototype was created and no interaction QA passed. Need manual Figma prototype authoring or a deliberate TalkToFigma MCP/plugin extension with verifiable reaction write support; real 3D requires suitable assets and an appropriate renderer outside the current Figma-only product scope.

Operation metrics:20 Figma MCP calls for reconnect/reconcile/apply/readback/export,1 failed export,7 bulk read/write calls. Shared operation charged once to S28 metrics, not duplicated across screens.


## Completed An Nhiên image turntable

16 editable states, 2 colors × 8 approximate angles, all exported and visually inspected. 81 prototype reactions applied and freshly read back via TalkToFigma. Color changes retain angle; previous/next wrap. Selected color has no self-navigation. Existing detail entry now opens S32; appointment overlay and home remain connected. Original flow is preserved. AI inferred views, not continuous3D or verified garment geometry. Browser Play was not independently click-tested. State:23 done,40 original-scope pending; current trial complete, full APP_SPEC remains incomplete. Export recovered without a proven root-cause fix; diagnostics retained.

Play: https://www.figma.com/proto/rXrX1FHInMsxbejkvSP9Wl/Untitled?page-id=0%3A1&node-id=81-2&starting-point-node-id=81%3A2&scaling=scale-down&content-scaling=fixed

| Screen | Root ID |
|---|---|
| S32 | 81:2 |
| S33 | 81:24 |
| S34 | 81:46 |
| S35 | 81:68 |
| S36 | 81:90 |
| S37 | 81:112 |
| S38 | 81:134 |
| S39 | 81:156 |
| S40 | 81:178 |
| S41 | 81:200 |
| S42 | 81:222 |
| S43 | 81:244 |
| S44 | 81:266 |
| S45 | 81:288 |
| S46 | 81:310 |
| S47 | 81:332 |

Evidence: ROTATION_LIVE_REACTIONS.json; ROTATION_VISUAL_QA.json; previews/S32..S47-rotation.png; S29-rotation.png.
