# 40-Frame Annotation Pilot: Execution Checklist

## Fastest practical workflow

**Use CVAT video track mode** once an approved local CVAT installation is available. It supports boxes across a sequence with persistent track IDs. Labeling 40 exported images in a still-image tool would be simpler to start, but requires separate ID bookkeeping and is slower for this goal.

**Blocked now:** CVAT is not available on `PATH`, and Docker cannot reach its daemon. No CVAT service or project configuration is verified. Starting annotation is blocked until an existing approved CVAT setup is made available or its environment is repaired. This checklist does not install or download anything; no runnable CVAT startup command is available until that setup exists.

## Before starting — decisions to approve

- [ ] Confirm source video: `pothole detection/pothoels-segmentation/p.mp4`.
- [ ] Approve prediction-blind random selection below and who records the draw.
- [ ] Confirm one pothole class and box rule: tight box around visible extent; do not infer hidden boundaries.
- [ ] Confirm identity rule: keep an ID only when visual evidence supports the match; otherwise mark identity uncertain, not a guessed ID.
- [ ] Confirm how the selected CVAT version/export will preserve uncertain identity (attribute or companion log), and who can access the local project.
- [ ] Name the second reviewer, the review subset, and the adjudicator. Recommended: second annotator independently labels 10 consecutive frames chosen by a separate recorded random draw from the 40.
- [ ] Approve where the source, annotations, export, and disagreement log may be stored.

## Select and record the 40 frames (do not inspect predictions)

1. Do not view YOLO/ByteTrack outputs, prediction CSVs, or overlays before selecting and recording the window.
2. The existing project documents report 692 source frames. If that count is confirmed for the approved source, choose a uniform random start from **1–653 inclusive**. A manual option: toss a fair coin 10 times, write heads as 1 and tails as 0, and read the results as a binary number from 0–1023. Accept 1–653; redraw 0 or 654–1023. Record each draw, including rejected draws. Alternatively, use an approved local random-number method and record its name/version and seed.
3. Set `end_frame = start_frame + 39`. The selected frames are the inclusive, one-based source indices `start_frame` through `end_frame`. Do not skip empty or difficult frames or replace a window for model-related reasons.
4. Record before annotation: source filename (and checksum if approved), verified frame count/FPS/dimensions, selection method, date/person, accepted start and end, and all 40 indices. If a technical issue makes the selection unusable, log its reason and get approval before redrawing.

**Sampling record (fill in after approval; none selected yet):**

| Source | Count / FPS / size | Method, seed or draw record | Start (1-based) | End (inclusive) | Selected indices |
|---|---|---|---:|---:|---|
| `pothole detection/pothoels-segmentation/p.mp4` | To verify | To record | — | — | — |

## Start annotation — manual steps vs. tool-dependent steps

### Manual preparation (no extraction or annotation has happened)

- [ ] Obtain approval for the decisions above and confirm the source metadata and exact selected indices.
- [ ] Keep the original video as the 1280×720 source of record. Do not use resized prediction videos or model outputs as annotation references.
- [ ] Prepare an annotation register keyed by source frame index. For every frame, record whether review is complete and whether a pothole is visible; retain reviewed empty frames.
- [ ] Assign a new canonical ground-truth ID when a pothole first becomes identifiable. Reuse it only when the visual evidence supports continuity. Record uncertainty and a brief reason instead of forcing an ID.

### Steps requiring a working, approved CVAT installation

These are CVAT UI actions after the service is available; **do not run service commands until its approved installation/configuration exists and Docker works**.

- [ ] Create a video annotation task and import the approved source. Verify original dimensions and map CVAT's frame counter to the recorded one-based source indices.
- [ ] Define the pothole label and rectangle shape. Use track mode for supported identities; adjust boxes through the sequence and inspect every frame rather than trusting interpolation.
- [ ] For an uncertain identity, keep the visible box but mark identity uncertain as agreed. Do not treat CVAT's internal track number as ground truth by itself.
- [ ] Annotate every selected frame, including frames with no pothole. Save the native project and export a video-capable format; verify the export retains frame indices, boxes, and track links. Keep a companion table for any uncertainty or review fields the export cannot represent.
- [ ] Check that boxes are in original 1280×720 coordinates and that all 40 source indices are present before considering the annotation complete.

## Independent review and disagreement log

The second annotator independently labels the preselected 10-frame subset from the source video, without seeing the first annotation or model outputs. Preserve both original annotations. Compare presence, box boundaries, visibility, and identity links; adjudicate by reviewing the source against the agreed rules. If identity remains uncertain, leave it uncertain rather than forcing agreement.

Use one row per disagreement:

| Frame index (1-based) | Object / issue | Annotator A decision | Annotator B decision | Resolution and reason | Adjudicator / date |
|---|---|---|---|---|---|

Include disagreements about pothole presence, box boundary, partial visibility/occlusion, and identity continuity. Do not silently overwrite either person's original work.

## Environment and change boundary

**Current blocker:** the `cvat` command is not found; the Docker client cannot connect to its daemon. Therefore CVAT startup, import/export checks, and annotation cannot begin here. A working approved installation is required; no installation or download is authorized by this checklist.

This checklist is the only file created for this task. No frames were extracted, no inference was run, and no existing code, data, or experiment output was changed.
