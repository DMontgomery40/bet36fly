# Circuit page acceptance — September 14, 2026

Mounting the retired neuron/connection viewer as the current application's Circuit page (`/#circuit`),
restyled to the light design system and reduced to anatomy only.

## Scope of the claim

This records that a frontend surface renders, reads the documented payload and keeps its stated limits.
It is not a scientific result. Nothing here measures neural activity, prediction or learning, and the page
itself displays none of those: it draws released MaleCNS v1.0 anatomy and nothing else.

## What ran

| Gate | Command | Result |
| --- | --- | --- |
| Python tests | `.venv/bin/python -m pytest -q` (via `make verify`) | 4,191 passed |
| Lint | `.venv/bin/ruff check bet36fly tests scripts` | clean |
| Frontend unit tests | `cd web && npm test` | 147 passed, 9 files |
| Production build | `cd web && npm run build` | built |
| Browser acceptance | `PLAYWRIGHT_PATH=... BET36FLY_BASE_URL=http://127.0.0.1:8766 node scripts/verify_circuit_browser.cjs` | 16 checks passed |
| Prior suite, regression | `node scripts/verify_sensory_browser.cjs` | 11 checks passed |

The browser suite ran against the guarded read-only verification server
(`make serve-verify QA_PORT=8766`), which the script confirms by its `X-BET36FLY-Verification: read-only`
marker and `/api/status` flag before launching Chromium. Playwright resolved from an external
`node_modules`; the package is not vendored in this repository.

## Browser checks that passed

1. The Circuit nav link opens `/#circuit`, the canvas renders, and a reload keeps the hash. This is the
   check that catches the duplicated valid-route list in `web/src/App.tsx`, which would otherwise rewrite
   the URL back to `/#overview`.
2. Displayed and retained counts match the live `/api/brain` payload: 2,500 displayed of 166,700 retained,
   and the neuron selector offers one option per displayed neuron.
3. The KC→MBON layer is named anatomically. The rendered page contains no occurrence of "plastic",
   "learned gain", "trained", "Recorded pick" or "replay".
4. Toggling the Kenyon-cell layer reduces the selectable neurons and restoring it returns the original
   count; toggling the KC→MBON edge layer leaves the canvas intact.
5. A grid walk finds a real node by hover, the preview appears, and clicking it opens the inspector dialog
   with the neuron identity and its displayed incident connections. Escape closes it.
6. Dragging the canvas rotates and tilts the camera, read from the canvas's `data-view` state rather than
   from pixels, with the tilt staying inside its clamp. Double-clicking empty canvas returns the camera to
   its default and opens no inspector.
7. A drag that starts and ends over the same neuron does **not** open the inspector. This is the regression
   the drag-slop flag exists to prevent.
8. The wheel zooms the canvas and `window.scrollY` stays 0, which is the non-passive `preventDefault`
   proving itself.
9. With the canvas focused, ArrowRight rotates, `=` zooms in and `0` returns to the default camera.
10. An explainer topic pins into the same inspector and closes with Escape.
11. Every element rendering text in the page computes to 11px or larger, and every legend swatch paints on
   the canvas ground `rgb(25, 34, 28)`.
12. `window.devicePixelRatio` is 1 when the desktop screenshot is taken.
13. No horizontal overflow at 320, 390, 720, 1024 or 1440 px, each at a real document load.
14. Only GET requests were issued, none to `/api/predict`, `/api/training` or `/api/associative/jobs`, and
    the page does not poll across a 6.5 s idle window.
15. A 503 from `/api/brain` shows the alert and an explicit "Retry connectome" control, draws no canvas,
    and recovers after retry.
16. Empty geometry states plainly that nothing can be drawn, rather than drawing an empty frame silently.

## Contrast decision

Every category color fails the 3:1 floor against the page paper `#f6f5ee`: ALPN cyan 2.11:1, Kenyon violet
2.14:1, MBON amber 2.06:1, other slate 1.36:1, unknown 2.35:1. The canvas therefore uses a dark inset
ground `#19221c`, where the same colorblind-safe palette reaches 6.36:1 to 10.99:1. The rest of the page
stays light. Legend swatches paint on that same ground so the legend shows each color exactly as drawn.
`web/src/BrainView.test.tsx` computes these ratios rather than asserting the colors merely exist.

## Screenshots

All captured at `deviceScaleFactor: 1`, matching the project legibility floor.

| File | Viewport | What it shows |
| --- | --- | --- |
| `circuit-desktop-1920.png` | 1920x1200 | Full page: heading, dark canvas with the sampled projection, anatomy layer legend, view-angle control, neuron search and inspect controls, explainer topics, "About this view" and the scope note. |
| `circuit-inspector-desktop.png` | 1920x1200 | A neuron open in the inspector with its released annotations, the category explainer control and its displayed incident connection count. |
| `circuit-rotated-desktop.png` | 1920x1200 | After a pointer drag: the projection turned to show the brain lobes with the ventral nerve cord extending away, which the resting view foreshortens. |
| `circuit-zoomed-desktop.png` | 1920x1200 | Wheel-zoomed to 2.5x, where the rose KC-to-MBON fans converging on individual MBONs become legible. |
| `circuit-mobile-320.png` | 320x844 | The same page stacked to one column with no horizontal overflow. |
| `circuit-error.png` | 1920x1200 | Synthetic 503: page alert, "Connectome unavailable" on the canvas, explicit retry, no stale drawing. |
| `circuit-empty.png` | 1920x1200 | Synthetic empty geometry: both the page-level and canvas-level empty statements. |

`evidence.json` records the base URL, the read-only guard result, the check list, every API request
observed, console output and the screenshot filenames.

## Interaction findings worth recording

- **Capturing the pointer on every press breaks double-click.** The first implementation called
  `setPointerCapture` in `pointerdown`; the browser then dropped the second click of a double-click and
  never fired `dblclick`. Capture is now taken lazily, only once a drag passes the slop threshold, which is
  also the only moment it is needed. This affected real users, not only the test harness.
- **Click-to-inspect wins over double-click, by construction.** Opening the inspector changes page layout,
  so the second click of a double-click over a neuron lands elsewhere. Double-click-to-reset therefore only
  ever reaches empty canvas. That is the wanted precedence, the hint copy says "double-click empty space",
  and the browser check asserts the corner it uses is empty.
- **A constant screen offset breaks zoom-about-the-pointer.** The original projection added a fixed 4px
  vertical nudge after scaling, which left the anchor point drifting 4px per zoom step. The nudge is gone
  and a unit test asserts the anchored point is preserved to six decimal places.
- **Navigating to an identical URL does not reload.** Two checks were silently reusing prior React state
  and focus because `page.goto` to the same hash is a same-document navigation. Both now use a distinct
  query, which is also what keeps the responsive screenshots free of leftover tooltips.

## Limits and judgment calls

- The displayed sample is 93% "other" annotated neurons (2,323 of 2,500, against 100 Kenyon cells,
  45 ALPNs and 32 MBONs). Background categories are drawn in a first pass so the sparse circuit
  populations are not overdrawn. This is a drawing-order choice; it changes no data.
- `plastic` in the payload means only "presynaptic neuron is a Kenyon cell and postsynaptic is an MBON".
  The page states that and labels the layer accordingly. No learning claim is made on this page.
- Explainer copy lost the topics that described the retired workflow (recorded replay, firing activity and
  shared training gains) along with counts that traced only to a diagram label rather than to the model
  card or the dataset. What remains separates fly biology, released dataset facts and simulator mechanisms.
- The legend, camera controls, hint and neuron selector render only when there is a drawing. The error and
  empty states show the canvas panel and its message alone, with no inert controls beside them.
- The browser check synthesizes the 503 with a route fulfillment, which proves only that the frontend
  handles it. The real server path is covered separately by
  `tests/test_api.py::test_brain_geometry_reports_an_unprepared_connectome_as_503`, which asserts the
  documented message for an absent, empty and partially prepared `data/brain`.
- Playwright is not vendored in this repository. Both browser scripts now resolve it through
  `scripts/playwright.cjs`: a normal require first, then `PLAYWRIGHT_PATH`, and otherwise an error naming
  both ways to supply it instead of a bare `MODULE_NOT_FOUND`.
- `useResource` now accepts a null URL, and `web/src/App.tsx` passes null on the learning and circuit
  pages, so neither requests the sensory confirmation any more. `LearningView.test.tsx` asserts that
  absence directly rather than asserting the page survives a failed summary.
- On touch screens `touch-action: pan-y` keeps vertical page scrolling, so a horizontal drag rotates while
  tilt and zoom stay on the sliders, buttons and keyboard. The hint copy says so.
- The page is a soma projection of a sample, not a neuropil reconstruction, and display filters never
  change any computation. Both statements appear in the page copy and in the API contract.
