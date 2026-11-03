# Proposed Video Annotation Protocol

**Status:** Proposal for review only. No video frames have been sampled or annotated as part of this document.

## Evidence categories

- **Verified repository fact** describes a file, setting, or artifact directly inspected in the current project.
- **Proposed rule** is a recommended convention that has not yet been adopted by the project.
- **Unresolved decision** requires approval before annotation/scoring begins.

## Verified repository facts

- Video: `pothole detection/pothoels-segmentation/p.mp4`; OpenCV metadata reports **692 frames, 25 FPS, 1280×720**. The resulting duration is approximately 27.7 seconds (692 / 25), calculated from metadata.
- The video detector reads frames sequentially and resizes them to **1020×500** before YOLO inference. In tracking mode it uses persistent Ultralytics tracking with `bytetrack.yaml`; see [test(for video).py](pothole%20detection/pothoels-segmentation/test%28for%20video%29.py#L87-L108).
- The paired evaluator uses the same video, checkpoint, confidence, CPU device, and resize for baseline and tracking passes; it records one-based frame indices and detection boxes. See [evaluate_temporal_consistency.py](pothole%20detection/pothoels-segmentation/evaluate_temporal_consistency.py#L42-L104).
- Existing detection records use fields `mode`, `frame_index`, `detection_index`, `track_id`, `class_id`, `class_name`, `confidence`, `x1`, `y1`, `x2`, and `y2`. Their coordinates are in resized-frame pixels, as documented in [EVALUATION.md](pothole%20detection/pothoels-segmentation/EVALUATION.md#L13-L17).
- The current video outputs and tracker IDs are model outputs, not annotations. The repository has no ground-truth identities for this video. The image segmentation dataset labels are not evidenced as labels of these video frames.

## Proposed pilot design

**Recommendation:** annotate **40 consecutive frames** as the first pilot. At 25 FPS this is 1.6 seconds. A 30–50-frame window is long enough to test the annotation workflow, visibility rules, identity assignment, export/import, and review process while keeping initial effort bounded.

To avoid selecting a window because the model appears to work well there:

1. Do not view predictions, detection records, or tracked outputs when selecting the pilot.
2. Before annotation, divide the 692-frame timeline into predeclared temporal bins and select one eligible 40-frame start uniformly at random from a nominated bin using a recorded random seed. Alternatively, if the professor prefers a specific scene, record the reason before viewing model outputs.
3. Record the exact one-based start/end frame indices, selection rule/seed, and any reason a sampled window was replaced.
4. Label every frame in the selected window, including frames with no visible pothole. Do not skip low-confidence, blurry, difficult, or empty frames.

A single 40-frame pilot checks feasibility only. It does not estimate performance reliably, represent the entire 692-frame clip, or support generalization beyond this video. If the workflow is approved, a later evaluation subset should sample multiple temporally distributed consecutive windows under a documented selection plan.

## Proposed bounding-box rules

These are proposed conventions, not existing project standards; approve or revise them before annotation.

- **Class definition:** positive means a visually identifiable road-surface pothole/depression. Do not label ordinary cracks, patches, shadows, stains, or manholes as potholes unless the project explicitly expands its class definition.
- **Box boundary:** use a tight axis-aligned rectangle around the visible pothole boundary. Use continuous pixel-edge coordinates in `xyxy` form `(x1, y1, x2, y2)`, with `x1 < x2` and `y1 < y2`; state whether right/bottom edges are exclusive. Clip coordinates to image bounds.
- **Partial visibility:** box the visible portion only; set `visibility_status=partial`. Do not infer hidden extent.
- **Occlusion:** box the visible portion and set an occlusion flag/status. Record the occluder or reason when it affects identity/visibility judgments.
- **Overlapping potholes:** use separate boxes only when annotators can distinguish separate depressions. If their boundaries cannot be separated confidently, mark the instance/frame ambiguous or ignore according to the agreed policy; do not force arbitrary boundaries.
- **Ambiguous surface feature:** use an explicit `ignore`/`uncertain` status and a short reason. Exclude ignored instances from scoring under a predeclared rule, while retaining them in the annotation file for auditability.
- **Very small objects:** set a minimum visible-size policy in pixels before labeling. If a pothole remains identifiable, annotate it and optionally flag it small; if it is not reliably distinguishable, flag it as uncertain/ignore rather than silently omitting it. No minimum size is currently established.
- **No pothole in a frame:** include a frame-level record with `annotation_status=complete` and `has_pothole=false`, even though there are no object rows. This distinguishes a reviewed empty frame from an unreviewed/missing frame.
- Annotators must work from the source video/frame, not from YOLO or ByteTrack outputs. Predictions may be overlaid later for comparison, never used as target boxes/IDs.

## Proposed ground-truth data format

Keep frame review state separate from object instances so empty frames and unreviewed frames are representable.

**`ground_truth_frames.csv` — one row per selected frame:**

| Field | Meaning |
|---|---|
| `video_id` | Stable identifier for this source video. |
| `frame_index` | One-based source frame number, matching existing evaluation convention. |
| `annotation_status` | For example: `complete`, `needs_review`, or `ignore_frame`. |
| `has_pothole` | `true`/`false` only after review is complete. |
| `frame_width`, `frame_height` | Dimensions used for the source annotation coordinates. |
| `annotator_id`, `review_status` | Non-sensitive annotator code and review/adjudication state. |
| `notes` | Optional frame-level visibility or ambiguity note. |

**`ground_truth_objects.csv` — one row per annotated object in one frame:**

| Field | Meaning |
|---|---|
| `video_id`, `frame_index` | Link to the reviewed frame. |
| `object_id` | Manually assigned persistent ground-truth identity, not a model track ID. |
| `class_id`, `class_name` | Ground-truth class; initially proposed as the single pothole class. |
| `x1`, `y1`, `x2`, `y2` | Bounding box coordinates under the declared convention. |
| `coordinate_width`, `coordinate_height` | Image dimensions in which the box was drawn. |
| `visibility_status` | Proposed values: `visible`, `partial`, `occluded`, `uncertain`, `ignore`. |
| `ignore_reason`, `annotator_id`, `review_status` | Optional reason and review provenance. |

A frame annotation answers “what potholes are visible in this frame?” An object `object_id` links an annotated pothole across frames. These are separate concepts: each visible object produces a frame-level box row, while its persistent ID is repeated across its continuous annotated observations.

**Coordinate recommendation:** keep the original-resolution 1280×720 annotation as the source of record. Current model predictions are on 1020×500 resized frames. Since the resize stretches both axes, convert coordinates explicitly:

- `x_resized = x_original × (1020 / 1280)`
- `y_resized = y_original × (500 / 720)`

Apply the same axis-specific transform to both corners, and compare only after dimensions/convention have been checked. Do not mix original and resized coordinates in an IoU calculation. A simpler alternative is to annotate directly in 1020×500, but that loses source-resolution detail; the chosen convention is an unresolved decision.

## Proposed ground-truth identity rules

These rules require annotator agreement before any tracking score is calculated.

- Assign a new `object_id` when a distinct pothole first becomes identifiable. Keep the ID unchanged across consecutive frames while the same physical pothole is visually matchable, even if its box changes due to camera motion or changing visibility.
- **Temporary partial occlusion:** retain the same ID if the pothole can still be matched confidently before and after the occlusion. Mark visibility/occlusion status per frame.
- **Fully hidden:** if the object is not visually observable, create no visible box for that frame; preserve the ID in later frames only if re-identification is defensible from the video evidence and within the predeclared reappearance policy.
- **Leaves and re-enters view:** do not automatically reuse an ID. Reuse only if continuity/appearance/location evidence supports the same physical pothole under the agreed policy; otherwise mark identity unknown/ambiguous or assign a new track episode according to the chosen protocol.
- **Camera motion:** camera movement alone does not create a new pothole identity. Match using the visual scene and temporal continuity, not fixed image coordinates. If movement makes identity uncertain, flag uncertainty rather than guessing.
- **Overlapping/ambiguous identities:** do not assign or switch IDs solely to make tracks continuous. Mark uncertain intervals and have them reviewed/adjudicated.
- **Unmatchable object:** preserve the visible box if its pothole class is clear, but set identity to unknown/blank when its persistent identity cannot be supported. Do not invent IDs.

For fair tracking evaluation, annotate continuous frame sequences, not isolated frames. Record explicit visibility and identity-uncertainty decisions so the evaluation can distinguish “not visible” from “visible but missed.”

## Future evaluation enabled by annotations

### Detection

With reviewed frame-level boxes, compare predictions and ground truth only on the same frames, classes, and coordinate system. Predeclare a one-to-one box matching rule using class agreement and an IoU threshold (or thresholds). Then calculate precision, recall, and F1 from matched predictions/ground-truth boxes and false positives/negatives under that rule. Average precision can be calculated from confidence-ranked detections across a sufficiently defined labeled set, with the IoU protocol reported. Specify how empty frames and `ignore` regions are handled. These metrics have **not** been measured from the current prediction-only CSVs.

### Tracking identity

Boxes alone are insufficient for identity accuracy. With manually assigned persistent ground-truth IDs over continuous frames, use a defined multi-object tracking evaluation protocol that performs frame-level spatial matching and identity association. IDF1 and identity switches may then be reported under that protocol; optionally report HOTA/MOTA if implementation, matching, ignore, and visibility rules are specified. The chosen evaluator and version must be documented. None of these ground-truth tracking metrics has been measured in this project so far.

A 30–50-frame pilot on one video can test the protocol and reveal annotation issues. It cannot establish general performance across videos, scenes, locations, cameras, or environmental conditions.

## Proposed quality assurance

1. Freeze a short written class/box/visibility/identity guide before labeling.
2. Annotate without model overlays. Keep source frames and prediction outputs separate.
3. Have a second person independently label or review a subset, prioritizing uncertain, partially visible, overlapping, and reappearing objects. If no second reviewer is available, re-review a blinded sample after a delay and report that limitation.
4. Log disagreements with frame index, object, issue type, annotator decisions, final adjudication, and rationale. Do not silently overwrite disagreements.
5. Check frame coverage, duplicate object rows, coordinate bounds, empty-frame declarations, ID consistency, and transformed coordinates before evaluation.
6. Report reviewer agreement or disagreement descriptively; do not imply consensus guarantees correctness.

Likely disagreement sources include pothole-versus-crack boundaries, box tightness, whether an object remains visible under occlusion, separating overlapping defects, minimum size, and whether a returning pothole is the same physical object.

## Decisions required before starting

1. Is the first phase detection-only box annotation, or will the pilot include persistent object IDs from the start? Identity labels cost more but are required for identity-aware metrics.
2. Approve a prediction-blind way to select the 30–50-frame window and record its exact indices/seed.
3. Choose original 1280×720 coordinates or resized 1020×500 coordinates as the annotation source of record.
4. Approve pothole inclusion/exclusion examples, minimum visible size, edge convention, and partial/occluded/ambiguous policies.
5. Decide when identity is preserved after occlusion or re-entry and when it must be unknown/new.
6. Select a locally permitted annotation tool/export format, reviewer, and adjudication procedure; confirm video privacy/permission if any hosted service is considered.
7. Predeclare the detection matching IoU threshold(s), ignore handling, and identity-aware tracking evaluator before computing scores.

## Feasibility conclusion

A 30–50-frame consecutive pilot is feasible for testing annotation rules, tool export, coordinate conversion, and identity decisions. It is not a performance benchmark and cannot support generalization beyond this video. The project already has model-output boxes that can be aligned for later comparison, but those predictions are not ground truth. No annotation has begun under this proposal.
