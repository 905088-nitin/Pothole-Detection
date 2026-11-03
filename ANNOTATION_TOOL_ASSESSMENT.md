# Annotation Tool Assessment and 40-Frame Pilot Plan

**Status:** Assessment and recommendation only. No frames have been extracted or annotated, no software has been installed, and no inference or experiment has been run.

## Scope and evidence labels

- **Verified local fact** means it was observed in the repository or current environment during this assessment.
- **Recommendation** means a proposed workflow, not an action already taken or a project decision.
- **Assumption / verify before use** identifies tool behavior or a detail that must be checked against the selected tool version and export.

This assessment builds on [ANNOTATION_FEASIBILITY.md](./ANNOTATION_FEASIBILITY.md) and [PROPOSED_ANNOTATION_PROTOCOL.md](./PROPOSED_ANNOTATION_PROTOCOL.md). It does not change either document.

## Findings from the repository and environment

### Verified local facts

- The existing documents identify `pothole detection/pothoels-segmentation/p.mp4` as the candidate video and report metadata of 692 frames, 25 FPS, and 1280×720. The resulting duration is about 27.7 seconds. This assessment did not reopen or process the video.
- The existing project documents describe model detections/tracks as predictions, not ground truth, and recommend annotating independently of those outputs.
- A repository search found CVAT, Label Studio, makesense.ai, and LabelImg mentioned only as tool suggestions in `ANNOTATION_FEASIBILITY.md`. It found no annotation project, tool-specific setup/configuration, or annotation dependency manifest. The searched project files do not establish that an annotation application is installed.
- In the checked shell environment, `cvat`, `label-studio`, and `podman` were not found on `PATH`. `docker` and `docker compose` commands are available.
- The Docker client could not connect to its configured Docker daemon. Consequently, local Docker images could not be enumerated or confirmed. Docker Compose being available does **not** establish that CVAT is running or installable now.
- `python3 -m pip show cvat-cli label-studio` reported that those package names were not found for the checked Python interpreter. This check does not establish package state in every Python environment or whether a browser-hosted service is accessible.
- The worktree already contains unrelated modifications and untracked project files. They are outside this task and must be preserved.

### Assessment boundary

These checks support the conclusion that there is **no verified, project-configured CVAT installation** in the inspected repository/environment. They do not prove that no one has access to a separate hosted CVAT instance, another machine, or an uninspected Python environment.

## Is CVAT suitable?

**Recommendation: CVAT is a good functional fit for the pilot, conditional on approval and a working, locally permitted installation.** Its video annotation workflow is designed around labeled objects and tracks across frames. For this task, an annotator can create pothole boxes and link them into tracks across the 40-frame sequence. Track interpolation/keyframes may reduce repetitive box edits, but each interpolated box and identity still needs human review; interpolation is not evidence that an identity match is correct.

CVAT is more capability than is strictly needed for 40 frames, but its sequence and track concepts fit persistent IDs better than labeling each frame as an unrelated image. It also keeps annotations in a project/task context and supports export workflows. Before relying on it, test the selected version with a tiny, non-project sample or an approved pilot import/export check, and verify:

1. The input is treated as a video with all intended frames and original dimensions, not silently rescaled or sampled.
2. The annotation UI's frame numbering maps to the agreed one-based **source-video** frame numbers.
3. Video export retains the per-frame boxes and track associations required by the project.
4. The selected export can represent or be paired with the `identity_uncertain` state and an absent/unknown ground-truth identity. A CVAT-generated track identifier is a tool identifier; it must not automatically be treated as a confident research ground-truth identity.
5. Local storage, access, backup, and the export format are acceptable under the project's data policy.

**Setup cost / assumption to verify:** A local CVAT deployment is commonly run as a web application backed by Docker services, so it requires an accessible Docker engine, setup/configuration, disk space, and a browser. This machine's Docker CLI currently cannot reach its daemon, so a local deployment is not presently verified as ready. A hosted CVAT would avoid local service setup but would require explicit approval to upload the video and check privacy/data-retention rules. No deployment, download, or upload has been attempted.

**Track and uncertainty handling recommendation:** Use CVAT track mode only where the visual evidence supports continuity. If a pothole is visible but a match across frames is uncertain, do not force the previous identity to continue. Keep the box, mark identity as uncertain using an agreed attribute or a companion adjudication table, and preserve the tool-native track ID separately from the canonical ground-truth ID. Confirm that the chosen export preserves the needed attributes; otherwise retain a separate CSV mapping keyed by source frame and object.

## Comparison with a simpler alternative: LabelImg on extracted frames

| Consideration | CVAT | LabelImg |
|---|---|---|
| Setup effort | Higher for a local video workflow: application/service setup and a reachable Docker engine may be needed. No working local deployment was verified here. | Lower for a beginner labeling still images: open images and draw boxes. It still needs to be installed, and this project would first need an approved frame-extraction step. It is not verified as installed here. |
| Video annotation | Has a video/task workflow intended for frame sequences. Import and frame mapping must be checked for the chosen version. | Not a native video-tracking workflow. Annotators work through extracted still frames one by one. |
| Persistent track IDs | Supports track annotations across frames. Human judgment is still required; an uncertain match should be flagged, not inferred from the tool's track ID. | No native persistent video tracks. IDs and cross-frame links would need a separate, carefully maintained table. |
| Export | Video-capable formats can retain track/frame structure, but exact format availability and attribute retention depend on the task/version; retain the native project and validate a normalized export before evaluation. | Commonly exports per-image formats such as Pascal VOC XML or YOLO text. These do not by themselves define persistent identities across frames. |
| Beginner suitability for this goal | More concepts and setup initially, but the track workflow matches the research objective and centralizes the sequence. | Easier to start for boxes on images, but manual frame management and an external identity ledger add substantial opportunities for bookkeeping errors. |

LabelImg is a simpler **box-only** alternative, not an equivalent tracking tool. Given the stated goal includes persistent ground-truth identities, CVAT is the stronger fit if local setup and export validation are approved. If avoiding installation is the overriding priority, do not assume that a hosted tool is acceptable; decide data policy and identity bookkeeping first.

## Recommended 40-frame selection and recording plan

### Prediction-blind selection

1. Before looking at any predictions, detection records, tracked videos, or model overlays, approve `pothole detection/pothoels-segmentation/p.mp4` as the source and freeze the sampling rule.
2. For the reported 692-frame source, choose one valid start frame uniformly from **1 through 653 inclusive** (692 − 40 + 1). Use a recorded random seed and a named/versioned random-number method, or have an independent person make and record a random draw. Do not select or replace the window because predictions look easy, difficult, favorable, or unfavorable.
3. The selected window is the 40 consecutive source frames from `start_frame` through `start_frame + 39`, inclusive. Record each one-based index explicitly. Include every frame, including empty, blurry, difficult, or partially occluded frames. If technical corruption makes a frame unusable, record the frame and reason and obtain approval before changing the window; do not silently substitute a more convenient frame.
4. Keep model outputs separate from annotator materials until the labels and review decisions are locked.

No random draw or frame-index selection has been made in this assessment. The range above follows the metadata recorded in the existing project documents and is conditional on confirming the same source file and frame count when extraction is eventually approved.

### Sampling manifest

Create a manifest as part of the future approved annotation package, not by modifying existing project documents. Record at least:

- source path/name and, when authorized, a checksum to identify the exact video;
- verified source frame count, frame rate, width, and height;
- selection rule, random method/version, seed or draw record, and who selected it;
- one-based `start_frame` and inclusive `end_frame`, plus the explicit list of all 40 source frame indices;
- the agreed frame-to-time convention and the mapping from any tool-native frame numbers to one-based source indices;
- extracted-image filenames mapped one-to-one to source indices, if image extraction is approved;
- any exclusion/replacement, its reason, and who approved it.

Use the source-video one-based frame index as the canonical key in annotation and review records. Do not rely on a filename sequence or a tool's internal frame counter alone. Verify the first and last imported/exported frame against the manifest before annotation proceeds. At 25 FPS, timestamps may be recorded as `(frame_index - 1) / 25` seconds if the source is confirmed to use zero-based time from its first frame; preserve the frame index as the primary key.

## Independent review and adjudication

1. Freeze the pothole definition, box-edge convention, partial/occluded/empty-frame rules, and the stated identity policy before either person labels.
2. Preselect a review subset without reference to model results. For a practical pilot, independently annotate a contiguous 10-frame subwindow within the 40 frames, selected by a recorded random rule before the first annotation begins. If workload permits, independently annotate all 40 frames instead; that gives a more complete pilot review.
3. The second annotator works from the source sequence without seeing the first annotator's boxes, IDs, uncertainty flags, or model outputs. Both annotators use the same source-frame index and coordinate convention. Keep both original annotation sets unchanged.
4. After both sets are complete, compare frame coverage, box placement, pothole inclusion/exclusion, visibility state, and identity links. Treat every identity disagreement and every uncertain/reappearing-object decision as an explicit review item, even if it falls outside the random subset; label these as targeted adjudication rather than part of the independently sampled agreement subset.
5. Maintain a disagreement log with source frame index/indices, issue type, each annotator's original box and identity/uncertainty decision, resolution, resolver, date, and concise rationale. Relevant issue types include object presence/boundary, partial visibility, occlusion, split/merge, ID continuity, and uncertain identity.
6. Resolve by discussion against the original video and the written rules. If evidence does not support a match, retain the box and mark its identity uncertain rather than forcing consensus. Preserve the two original annotations and the adjudicated result as separate records; do not silently overwrite an annotator's work.
7. Report the subset and review procedure descriptively. Agreement is a QA observation, not proof of annotation accuracy.

## Approval required before any extraction or installation

No extraction, software installation, Docker service startup, hosted upload, or annotation has been performed. Before those actions, obtain approval for:

- **Source and sampling:** the exact source video; the prediction-blind random-window rule; and the later recorded seed/draw and resulting exact 40 source indices.
- **Tool and deployment:** CVAT versus the simpler alternative; local versus hosted use; permission to install/activate the required software or Docker engine and services; and whether the video may leave the machine. Hosted upload should remain off the table unless explicitly cleared.
- **Annotation policy:** original 1280×720 as source of record; one-based source frame indices; box-edge convention and pothole inclusion rules; how partial/occluded/ambiguous objects are represented; and how an uncertain identity is stored without inventing a persistent ID.
- **Review:** the second annotator's identifier, the independently reviewed subset (or all 40), the disagreement-log location, and who adjudicates unresolved cases.
- **Data handling:** where extracted frames, native tool projects, exports, and review records may be stored and who may access them.

After approval, first confirm the source metadata and exact frame mapping, then perform a small import/export check before completing the pilot. Keep the original-resolution source as the annotation reference and preserve any tool-native project alongside a validated export.

## Inspected files and change boundary

Inspected:

- `ANNOTATION_FEASIBILITY.md`
- `PROPOSED_ANNOTATION_PROTOCOL.md`
- `pothole detection/pothoels-segmentation/p.mp4` metadata as reported in those documents; the video itself was not opened or processed.
- Repository file/config inventory, annotation-tool text references, and the current Git worktree status.
- Local command/package metadata for `cvat`, Docker/Compose, `label-studio`, `podman`, and the checked Python interpreter.

The only file created for this task is `ANNOTATION_TOOL_ASSESSMENT.md`. Pre-existing modifications and untracked files were left untouched; no source, video, dataset, model, evaluation output, or either existing Markdown document was modified.
