# Fly’s desk — implementation and verification

Implemented September 10–11, 2026. Open the fourth tab at [Fly’s desk](http://127.0.0.1:8765/#desk).

The rendered character is illustrative. All games, probabilities, recordings and progress values come from the running app. The first valid pregame pick for each current fixture revision is scored; reruns never replace it. All model versions are included. Final outcomes are matched to public score data, with unresolved and cancelled fixtures excluded from scored accuracy. No money or bet-settlement record is inferred from prediction accuracy.

## Visual references and assets

- [Generated layout concept](fly-desk-concept.png): a design reference, containing illustrative metadata that must not be used as evidence.
- [Implemented desktop screenshot](fly-desk-desktop.png), 1440-pixel viewport.
- [Implemented mobile screenshot](fly-desk-mobile.png), 390-pixel viewport. The table scrolls horizontally, with an explicit hint.
- Fly artwork: `web/public/images/fly-desk.png`, generated locally with the built-in ImageGen tool; a red-eyed fruit fly in a lime tie at a miniature desk, laptop, lamp, mug, books and banana. Its plaque reads “Chief of questionable decisions.” No external stock asset or hotlinked artwork is required.

The image-generation direction was a dark forest-green observatory with a humorous, realistic 3D fly at a miniature analyst’s desk; lime highlights, a prominent fly at left, three real pick cards at right, and a forward-record section below. The asset refinement isolated the fly scene from the dashboard so that native HTML supplies every control and data label. The original generated outputs are `exec-db4f34a0-3398-41c3-a032-20b150571d9a.png` (concept) and `exec-c64ed10b-48db-4323-ac81-02625a3cd4f2.png` (character), copied into this project.

## Fidelity ledger

| Reference element | Implemented result |
| --- | --- |
| Large fly at a desk, tie and banana | Preserved with an isolated generated asset; the figure remains the visual focus. |
| Dark green background, lime highlights and white type | Preserved and matched to the existing three tabs. |
| Fly at left, three picks at right | Preserved on desktop; stacked on mobile. |
| “Small brain. Big weekend.” heading | Preserved as selectable HTML with responsive wrapping. |
| Highlighted primary pick and Watch action | Preserved; Watch makes an actual neural inference request. |
| Neural activity strip | Replaced the concept’s decorative waveform with measured population spike bins, replay and scrub controls. No trace appears before a recording exists. |
| Forward-record metrics and table | Preserved; actual original-pick timestamps and confirmed scores replace the concept’s illustrative counts. Added result filters, pagination and a cumulative accuracy/confidence chart. |
| Mock team logos, team records, year and incorrect league labels | Intentionally omitted or replaced with verified fixture data. Simple sport symbols do not imply sourced team branding. |
| Existing app navigation and provenance | Preserved; added the fourth tab, original-record inspection, source links, and short explanations of scoring. |
| Humorous presentation | Nameplate and state-dependent scripted banter; neither is presented as a neural explanation. |

## Functional acceptance

The browser check exercises the served production build, not a seeded UI. Its output is [browser evidence](fly-desk-browser-evidence.json). It verifies the direct fourth-tab route, actual neural POST, unchanged original prediction ID after a rerun, spike-bar count, replay and scrubbing, both sport filters, result inspection, pagination, the other tabs, reduced-motion behavior, and absence of JavaScript errors. Layout checks cover 1440, 1024, 768, 390 and 320 CSS pixels with no page-level horizontal overflow.

At the recorded check, the desk contained **125 upcoming picks and one completed prediction: 0 correct, 1 missed**. The White Sox pregame pick lost against Pittsburgh, with a public final score of 0–2. This one observation says very little about model quality. The real Cubs–Pirates neural run produced **154,208 spikes across 19,288 active neurons**, over **80 ms simulated time**, in about **0.16 seconds CPU time**. “Active neurons” is the subset that spiked in that trial; computation still uses the full 166,700-neuron graph.

The backend refreshes public schedules/results every 900 seconds while the local server runs; the browser polls the record every 12 seconds. A successive refresh was observed completing at 2026-09-11 04:08:56 UTC. This does not retrain the checkpoint or create a scheduled Codex task.

Run the normal gate with `make verify`: **164 Python tests, Ruff, 34 frontend tests, TypeScript and the production Vite build passed**. Scoring tests cover the outcome/state matrix, draw handling, invalid score/probability families, pregame timing, source corrections, duplicate revisions, timezone equivalence and reschedules. The follow-up loop is tested for repeated cycles, stop behavior, and recovery after an unavailable checkpoint.

The additional browser check is `node scripts/verify_desk_browser.cjs`, from the repository root with the trained local server running. It requires Playwright/Chromium; set `PLAYWRIGHT_MODULE` to the installed Playwright package path when supplied by a bundled workspace runtime. It makes real paper inference requests and writes updated screenshots/evidence here. It is an acceptance check for a populated running experiment, not a clean-install fixture test.

## Verification incident

One `npm run build` invocation was mistakenly issued from the repository root rather than `web/`. npm resolved `/Users/davidmontgomery/package.json` and its unrelated build script ran `rm -rf out` before failing to locate pnpm. That cleanup targeted `/Users/davidmontgomery/out`; no pre-command inventory exists, so whether that directory contained anything cannot be established. The correct project build and full verification gate subsequently passed.
