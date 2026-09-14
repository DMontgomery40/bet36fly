# Connectomes for bet365

An 8–12 minute film for technical bet365 colleagues who know neural networks and are new to connectomes. Display identity is **bet36fly**; narration says **bet three sixty fly**. The voice is ElevenLabs River, an American voice, at a relaxed native speaking speed.

The completed cut is **11:07**, with 33 still scenes using 31 existing images. Claude approved the final narration in a fresh session given only the text and a general engagement/coherence rubric. Earlier narrative reviews are superseded; the complete review record is in `qa/claude-v4/APPROVAL.md`. Media and visual checks passed.

## Actual factory workflow

The factory is `/Users/davidmontgomery/markdown-video-experiment/md-video-maker`. Its `VIDEO_BRAIN.md` and `GOOD_EXAMPLES.md` govern production. The full Koi Pond and TRIBE reference narratives were provided to Claude for authoring. Separate fresh Claude sessions review only the narration, without the brief, project history, reference films or author rationale. Their actual prompts and responses are retained locally under `qa/claude-v4/`; prompts containing reference material are excluded from Git.

The actual `mdvm.py plan` command creates the scene plan from `BRIEF.md`. Narration is locked during visual planning, and its text is checked for exact preservation. Review fixes are saved inline in the plan. Every scene uses an accepted existing `image_source_path`. No image generation or bespoke animation is part of this revision.

The actual `mdvm.py render` command generates the approved narration with the factory's ElevenLabs helper and assembles its still-image film. Its `meta` fields specify River's exact voice ID, speed 0.82, stability 0.70, similarity 0.75, style 0 and speaker boost disabled. The frame is 1920×1080 at 24 fps. A packaging step adds aligned captions, chapter metadata and consistent audio loudness while copying the factory's video stream.

The default npm Codex wrapper is missing its executable on this machine; prepend `/Applications/ChatGPT.app/Contents/Resources` to PATH to use the installed app binary for planning. The factory also incorrectly normalized absent optional video paths to the project directory. That bug is fixed in the actual factory, with regression coverage for missing, null, blank, relative and absolute paths. The portable fix is in `qa/factory-path-fix.patch`.

Before recording, `tools/production_contract.py` checks the exact approved narration hash, selected American voice and unchanged accepted image hashes. A rejected review or any later narration change invalidates approval. The local `tools/narrate.py`, animation renderer and mixed assembly tools are retained as historical source; they are not the revision-four production route.

## Deliverables and verification

The actual factory export is `connectome-film.mp4`. The packaged film is `bet36fly-connectomes.mp4`, with `captions.srt`, `captions.vtt`, `timeline.json`, `NARRATION.md` and `SOURCES.md`. Large media remains local and is excluded from Git.

Serve this directory using the range-capable preview for reliable chapter seeking:

```sh
../../.venv/bin/python -m uvicorn tools.serve_film:app --host 127.0.0.1 --port 8790
```

Open http://127.0.0.1:8790/ . Verification covers the exact Claude-approved narration, unchanged existing images, generated audio and alignment, exported media duration and formats, complete decoding, every displayed scene and actual browser playback. Application verification uses `make verify`; targeted tests cover narration caching, production approval and HTTP range handling. Factory tests cover optional asset paths and mixed audio assembly.

No application behavior, scientific experiment, model pointer or evaluation data was changed for the film. Nothing is published or deployed.
