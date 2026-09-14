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
| Browser acceptance | `BET36FLY_BASE_URL=http://127.0.0.1:8766 node scripts/verify_circuit_browser.cjs` | 12 checks passed |

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
6. An explainer topic pins into the same inspector and closes with Escape.
7. Every element rendering text in the page computes to 11px or larger, and every legend swatch paints on
   the canvas ground `rgb(25, 34, 28)`.
8. `window.devicePixelRatio` is 1 when the desktop screenshot is taken.
9. No horizontal overflow at 320, 390, 720, 1024 or 1440 px.
10. Only GET requests were issued, none to `/api/predict`, `/api/training` or `/api/associative/jobs`, and
    the page does not poll across a 6.5 s idle window.
11. A 503 from `/api/brain` shows the alert and an explicit "Retry connectome" control, draws no canvas,
    and recovers after retry.
12. Empty geometry states plainly that nothing can be drawn, rather than drawing an empty frame silently.

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
| `circuit-inspector-desktop.png` | 1920x1200 | Neuron 814531 (IN13A061) open in the inspector with its released annotations, the category explainer control and its displayed incident connection count. |
| `circuit-mobile-320.png` | 320x844 | The same page stacked to one column with no horizontal overflow. |
| `circuit-error.png` | 1920x1200 | Synthetic 503: page alert, "Connectome unavailable" on the canvas, explicit retry, no stale drawing. |
| `circuit-empty.png` | 1920x1200 | Synthetic empty geometry: both the page-level and canvas-level empty statements. |

`evidence.json` records the base URL, the read-only guard result, the check list, every API request
observed, console output and the screenshot filenames.

## Limits and judgment calls

- The displayed sample is 93% "other" annotated neurons (2,323 of 2,500, against 100 Kenyon cells,
  45 ALPNs and 32 MBONs). Background categories are drawn in a first pass so the sparse circuit
  populations are not overdrawn. This is a drawing-order choice; it changes no data.
- `plastic` in the payload means only "presynaptic neuron is a Kenyon cell and postsynaptic is an MBON".
  The page states that and labels the layer accordingly. No learning claim is made on this page.
- Explainer copy lost the topics that described the retired workflow (recorded replay, firing activity and
  shared training gains) along with counts that traced only to a diagram label rather than to the model
  card or the dataset. What remains separates fly biology, released dataset facts and simulator mechanisms.
- The anatomy layer legend and the view-angle control stay rendered in the error and empty states, inert
  but visible, matching the retired layout. The neuron search and inspect controls are hidden there,
  because they need a loaded graph. This is a layout choice worth a second opinion, not a defect.
- The browser check synthesizes the 503 with a route fulfillment, which proves only that the frontend
  handles it. The real server path is covered separately by
  `tests/test_api.py::test_brain_geometry_reports_an_unprepared_connectome_as_503`, which asserts the
  documented message for an absent, empty and partially prepared `data/brain`.
- Playwright is not vendored in this repository. The command above resolved it from an external
  `node_modules` via `NODE_PATH`; a checkout without Playwright available cannot run the script as written.
- `evidence.json` shows `/api/sensory/summary` fetched while on the Circuit page. That is pre-existing:
  `web/src/App.tsx` mounts that resource once for the whole application regardless of the active page, as
  the contract already describes. The Circuit page itself adds only the single `/api/brain` GET.
- The page is a soma projection of a sample, not a neuropil reconstruction, and display filters never
  change any computation. Both statements appear in the page copy and in the API contract.
