# Verification of the completed 11:07 cut

- Fresh Claude narration-only holistic review: APPROVE. Exact text is bound to its SHA-256 in claude-v4/approval.json. No more line-edit loops were performed after approval.
- Actual md-video-maker planner and renderer used. Final source/export metadata is in production-run-v4.json.
- 33 still scenes reuse 31 existing images. No images generated in this revision; no bespoke animations.
- All 33 exported middle frames visually inspected against their narration. All 99 early/middle/late samples matched the intended existing image; maximum thumbnail RMSE 1.80.
- Full 1080p24 H.264/AAC export decoded without errors. Duration 667 seconds. 33 chapters and 167 aligned caption cues; all 1,543 words align to the approved text and current audio.
- River American narration: native speed 0.82; about 139 words/minute overall, with approximately 141 in the opening. No post-production speed change. Audio normalized to target -18 LUFS.
- Browser: correct 11:07 metadata, advancing playback, visible captions and successful chapter seeking. Stale metadata caching was found and fixed. Closing artwork was verified from the exported frames; the user's subsequent playback was left undisturbed.
- make verify: 4,194 Python tests, Ruff, 150 frontend tests and Vite build passed. Existing warnings: Starlette/httpx and AnyIO deprecations.
- Film-specific tests: 33 passed. Factory regression suite: 5 passed. Changed production/preview Python files passed Ruff.

Media hashes and detailed measurements are in media-verification.json. Current preview behavior is recorded in browser-verification-v4.json. Large media and generated-image assets remain local and are excluded from Git. No application experiment or model pointer changed, and nothing was pushed or deployed.
