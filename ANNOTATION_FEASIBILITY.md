# Ground-Truth Annotation Feasibility Assessment

**Assessment date:** 2026-10-28
**Scope:** Feasibility only. No frames were annotated, no inference was run, no packages were installed, and no existing files or data were modified.

## Facts verified from this repository

- The target video is `pothole detection/pothoels-segmentation/p.mp4`. OpenCV reports it opens successfully and has **692 frames, 25 FPS, and 1280×720** resolution. Its duration is about **27.7 seconds** (692 / 25); this is calculated from the metadata, not a separate media-duration check.
- The video detector in [test(for video).py](pothole%20detection/pothoels-segmentation/test%28for%20video%29.py#L54-L99) reads frames sequentially, resizes them to **1020×500**, then calls either YOLO `predict` or persistent ByteTrack `track`.
- The evaluator in [evaluate_temporal_consistency.py](pothole%20detection/pothoels-segmentation/evaluate_temporal_consistency.py#L42-L65) processes the video frame by frame and records per-frame outputs. It writes one-based `frame_index` and `detection_index`, `track_id` when available, class/confidence, and `xyxy` boxes in the resized 1020×500 frame coordinates. The coordinate convention is documented in [EVALUATION.md](pothole%20detection/pothoels-segmentation/EVALUATION.md#L13-L15).
- The existing evaluation contains model/tracker output records, not human-verified ground truth. Existing detection records must not be used as annotation labels.
- The local `Image-segmentation DATASET/` has `train`, `valid`, and `test` directories with `images` and `labels`; its README says annotations are in YOLOv8 format. It is an image dataset, and no inspected evidence links those labels to frames in `p.mp4` or supplies persistent video identities.
- The separate `Pothole-Classification DATASET/` is organized into pothole/non-pothole image classes. It is not a video box or track-label set.
- No video annotation files, frame-to-label index, annotation-tool project, tracking ground-truth IDs, or annotation instructions were found in the inspected `pothole detection/pothoels-segmentation/` directory. No project dependency or setup manifest for an annotation tool was found there.
- Existing evaluation outputs include `detection_records.csv`, which can help locate predicted boxes for later comparison, but those are model predictions and must be kept separate from annotator decisions.

## Recommendation: a manageable representative subset

A practical **pilot** is 10–12 short temporal windows, each about 1–2 seconds long, sampled across the full 27.7-second clip. At 25 FPS, that is roughly 25–50 consecutive frames per window, or about **250–600 frames** total. A moderate first pass could use 12 windows × 1 second = **300 frames**. This is a workload/coverage compromise, not a statistically optimal sample size.

Suggested selection procedure:

1. Divide the clip into 10–12 equal-duration time bins from start to finish.
2. Select one contiguous 1–2 second window per bin, with a reproducible documented rule (for example, choose the center time of each bin, then use a fixed pseudo-random offset within a bounded range). Record the sampling seed or exact selected frame indices.
3. Review a contact sheet or video-only preview of the selected windows before finalizing them. If a window is unusable (cut, obstruction, severe blur, or no road view), replace it with a nearby window in the same time bin and record why.
4. Keep each chosen window consecutive. Do not select only isolated, easy frames: temporal continuity is necessary for visibility persistence and identity assessment.
5. Do not choose frames based on YOLO predictions alone. If prediction-assisted triage is used to find potentially difficult regions, also retain a predetermined uniform/temporal sample and record the selection process to reduce selection bias.

**Trade-off:** Fewer windows reduce labeling time but risk missing lighting, road, camera-motion, and pothole-visibility variation. Longer contiguous windows help assess temporal behavior but cost more labeling effort. A 300-frame pilot is suitable for testing the protocol and estimating actual annotation time; it cannot establish broad performance or represent other videos, locations, cameras, or conditions. Increase coverage only after reviewing pilot workload and scene diversity.

## Workload estimate (estimate, not measured)

Assumptions: manual box drawing, one annotator, a simple pothole-only class, frame-level annotations, and no prior annotation project. These estimates include ordinary inspection but not training annotators, arbitration, export troubleshooting, or a second-pass quality audit.

- **300 sampled frames:** roughly 1–3 minutes/frame if many frames need careful inspection gives about **5–15 hours** of initial labeling. Sparse potholes or fast annotation software may reduce this; crowded/ambiguous scenes may increase it.
- **500–600 frames:** roughly **8–30 hours** at the same assumed pace.
- Adding persistent object IDs across windows adds work and judgment; it should be estimated separately after the box-only pilot. If a pothole exits and later re-enters after a long unseen interval, identity may be inherently ambiguous.

Run a 30–50 frame pilot first, time the actual work, compare a sample with a second reviewer, then revise the estimate. The above rates are planning assumptions, not facts about this video.

## Practical tools and formats

No annotation tool is currently configured in the project. Practical choices include:

- **CVAT** or **Label Studio** for video/frame boxes and track IDs if a local or institution-approved installation is available. These are recommendations only; neither is verified as installed here.
- **LabelImg** or **makesense.ai** for still-frame bounding boxes. These are more appropriate for independent frame boxes than for managing persistent identities across clips.
- A simple **CSV or JSON** export can be evaluated by a small project-specific evaluator later. Store one row/object per frame with fields such as `video_id`, `frame_index` (one-based to match existing CSVs), `object_id` (persistent manual identity), `class_name`, `x1`, `y1`, `x2`, `y2`, and `visibility/occlusion flag`. Record coordinate dimensions explicitly.
- Prefer original-frame coordinates (1280×720) as the human annotation source of record, or consistently annotate the existing 1020×500 display frames. If annotation is done at original resolution, transform boxes using documented scale factors before comparing with detector outputs. The current detections are saved in resized-frame coordinates, so comparisons must use a consistent coordinate system.

For portability, keep tool-native project files plus an exported, versioned CSV/JSON and a sampling manifest. Confirm tool/export license and institutional data policy before uploading any video externally.

## Suggested pothole bounding-box protocol

1. Define the target as a visible road-surface pothole/depression, not every crack, patch, shadow, manhole, or stain. Write down inclusion/exclusion examples before labeling.
2. Draw a tight axis-aligned box around the visible pothole boundary. Do not use the YOLO output as the target; annotators should label the image/video independently of model boxes.
3. Use one consistent coordinate convention, inclusive/exclusive pixel edge policy, image dimensions, and frame indexing. The existing outputs use one-based frame indices and `xyxy` coordinates on the resized 1020×500 image; a new ground-truth file must state whether it uses those or original 1280×720 coordinates.
4. **Partially visible:** box only the visible extent; mark visibility/occlusion (for example, `partial`) and avoid guessing hidden boundaries.
5. **Ambiguous:** mark `ignore`/`uncertain` with a short reason rather than forcing a positive or negative label. Set an adjudication rule before evaluation.
6. **Overlapping potholes:** label separate boxes only when separate physical depressions are visually distinguishable. If boundaries cannot be separated reliably, use an ambiguity flag and document the rule.
7. **Very small objects:** decide a minimum visible size before labeling. Keep a pothole if it is still visually identifiable; otherwise label it as too small/uncertain or ignore according to the agreed rule. Record the pixel threshold and apply it consistently.
8. Include frames with no visible potholes as explicit empty-label frames. They are essential for false-positive measurement; do not omit them.
9. Have a second person independently review a subset, especially ambiguous and partially occluded cases. Resolve disagreements and preserve an audit trail.

## Metrics enabled by box ground truth

Once the selected frames have human boxes and a predeclared matching rule, detection metrics can include precision, recall, F1, and average precision at stated IoU thresholds. Per-frame matching typically requires class agreement and one-to-one predicted/ground-truth box assignment. Define handling for ignored/ambiguous labels and empty frames before scoring. A sparse subset produces subset-specific estimates only; report the selected frames and do not generalize to all videos without a representative evaluation design.

Detection boxes alone do **not** make tracking identity accuracy measurable. For fair tracking metrics, manually assign a persistent ground-truth `object_id` to each visible pothole over the annotated sequence, maintain IDs across occlusion/exit/re-entry only when identity is defensible, and document when identity is unknown. Then use an explicit MOT evaluation protocol (for example, frame association plus IDF1 and identity switches; optionally HOTA/MOTA if the matching and ignore rules are defined). Continuous sequences are needed; isolated frames cannot establish identity switches or track fragmentation. If identities are ambiguous, exclude or flag those intervals under a predeclared policy rather than inventing IDs.

## Risks and limitations

- One 27.7-second video is a narrow sample. Any measured result applies only to annotated portions of this clip and setup.
- Selecting windows after looking at model outputs can bias results. Use a documented temporal sampling plan and preserve difficult/empty frames.
- Pothole boundaries may be subjective, especially under shadows, water, occlusion, low resolution, and motion blur. Define rules and measure reviewer agreement.
- Sparse frames can miss short-lived detections and inflate/obscure temporal gaps. Use consecutive annotated frames within sampled windows for temporal evaluation.
- Original and resized coordinate systems can silently mismatch and corrupt IoU calculations. Declare and test the transform.
- A track gap alone is not a detector false negative: the pothole may have left the view, been occluded, or become unidentifiable. Ground-truth visibility must be recorded to make that judgment.
- Prediction-guided frame selection and prediction-derived labels risk circular evaluation. Do not use predictions as ground truth.
- External annotation services may raise privacy, licensing, or data-retention issues; confirm local policy before uploading footage.

## Decisions needed before annotation

1. Is the immediate goal detector quality on this clip, temporal identity quality, or both? Tracking identity requires persistent object IDs, not boxes alone.
2. What subset budget can you label and second-check? Choose the pilot window count/length after a 30–50-frame time trial.
3. Should annotators use original 1280×720 frames or the 1020×500 processed frames? Pick one source coordinate convention and document transforms.
4. What precisely counts as a pothole versus a crack, patch, shadow, or surface defect? What is the minimum visible size?
5. How should partial visibility, occlusion, ambiguous boundaries, and a pothole leaving/re-entering the camera view be handled?
6. Who will annotate and adjudicate disagreements? Can a second reviewer check a subset?
7. Which annotation tool is permitted and available locally, and what export format will be retained?
8. What detection IoU threshold(s), ignore rules, and matching protocol will be fixed before measuring metrics?
9. For tracking, what identity policy applies across occlusion and exits/re-entries, and which MOT metrics will be reported?
10. Is the video cleared for use with any selected annotation tool, especially a hosted service?

## Bottom line

A small, temporally stratified, manually annotated subset is feasible for a bounded pilot. The image datasets in the repository do not replace video-specific labels or identity annotations. Begin with a short consecutive-frame pilot, agree on the box/visibility/identity rules, and use the measured pilot workload to set the final subset size. Results would apply to this video only; they would not establish general performance across videos or deployment conditions.
