# Professor Presentation Plan: Pothole Detection with YOLO + ByteTrack

## Evidence labels

- **Verified implementation** means directly visible in the inspected source or saved configuration.
- **Measured observation** means recorded in the existing CSV results and independently cross-checked.
- **Interpretation** means a cautious reading of those measurements, not a ground-truth performance claim.
- **Future work** means proposed work not completed or measured in the current project.

## 1. Project overview

### Research problem and motivation

Pothole detectors applied independently to each video frame may produce changing boxes and labels over time. That can make a video output harder to follow and may cause repeated, disconnected reports of what appears to be the same visible pothole. This project tests whether an object tracker can associate YOLO detections across frames and provide IDs.

### Project objectives

1. Run the existing YOLO pothole checkpoint on video.
2. Compare per-frame YOLO prediction with YOLO plus persistent ByteTrack association using the same video and detector settings.
3. Describe returned detections and tracking continuity using saved frame, track, gap, and bounding-box statistics.
4. Identify what cannot be concluded without annotated video ground truth.

### Current implementation

**Verified:** The local checkpoint loads as an Ultralytics detection model with class `Pothole`. The checkpoint source, training procedure, training dataset, and license are unverified. It is not established as the original paper authors' checkpoint.

The current contribution demonstrated in this code is integrating ByteTrack into the video inference path and measuring its outputs. The available results do not establish that this is a new detector architecture or that the tracker improves detection accuracy.

## 2. System workflow

1. Open a local MP4 using OpenCV `VideoCapture`.
2. Read frames in order and resize each frame to 1020×500.
3. Run YOLO on CPU with confidence threshold 0.25.
4. In **baseline** mode, call `model.predict` independently per frame.
5. In **tracking** mode, call `model.track` on each sequential frame with `persist=True` and `tracker="bytetrack.yaml"`. The returned boxes are annotated with a track ID when one is available.
6. Optionally write the annotated frames to an MP4.

Relevant code:
- Video CLI, input loop, mode selection, annotation, and output writing: [test(for video).py](pothole%20detection/pothoels-segmentation/test%28for%20video%29.py), especially the frame loop and `predict`/`track` branches.
- Paired evaluation and CSV writing: [evaluate_temporal_consistency.py](pothole%20detection/pothoels-segmentation/evaluate_temporal_consistency.py).
- Analysis statistics and plots: [analyze_temporal_consistency.py](pothole%20detection/pothoels-segmentation/analyze_temporal_consistency.py).

**Baseline versus tracking:** Baseline returns detector boxes per frame without persistent association. Tracking asks Ultralytics to maintain tracker state across consecutive frames and adds IDs where returned. ByteTrack associates detections; it does not verify that a detection is a true pothole or guarantee perfectly stable physical-object identity.

## 3. Experimental setup

| Setting | Recorded value |
|---|---|
| Video | `pothole detection/pothoels-segmentation/p.mp4` |
| Video properties | 692 frames, 25 FPS, 1280×720 |
| Checkpoint | Project-root `best.pt`; origin and training details unverified |
| Model task/class | Detection; class name `Pothole` |
| Confidence threshold | 0.25 |
| Device | CPU |
| Processing size | 1020×500 |
| Baseline | Ultralytics `model.predict` per frame |
| Tracking | Ultralytics `model.track`, `persist=True`, `bytetrack.yaml` |

The evaluation opens the same video in separate passes and loads the same checkpoint for each mode. Confidence, device, and resize values match. The intended difference is the inference API/tracker. This is a paired settings comparison, but not a ground-truth accuracy experiment. Timing was measured once per mode, in fixed baseline-then-track order, so the FPS numbers are descriptive single-run throughput, not a controlled benchmark.

## 4. Results

Source: `outputs/temporal_evaluation/run_20261027_013633_351042/summary.csv` and `outputs/temporal_evaluation/run_20261027_013633_351042/analysis_20261027_015805_475307/analysis_summary.csv`.

| Measure | Baseline YOLO | YOLO + ByteTrack |
|---|---:|---:|
| Frames processed | 692 | 692 |
| Frames with at least one returned box | 679 (98.1214%) | 646 (93.3526%) |
| Returned boxes | 3,727 | 2,801 |
| Mean returned boxes per processed frame | 5.385838 | 4.047688 |
| Unique tracker IDs | N/A | 119 |
| Observed duration per ID, mean / median / maximum | N/A | 23.54 / 11 / 117 frames |
| IDs observed for at least 5 / 10 / 20 frames | N/A | 78 / 61 / 48 |
| Gap episodes / missing track-frames | N/A | 114 / 331 |
| Mean / maximum gap length | N/A | 2.90 / 28 frames |
| Adjacent-frame same-ID box transitions | N/A | 2,568 |
| Adjacent-frame box IoU, mean / median | N/A | 0.801708 / 0.814433 |
| IDs with multiple observed runs after gaps (proxy) | N/A | 50 |

### What the measurements mean

- A **frame with detections** is a frame where the selected mode returned at least one box. It is not recall or the share of real potholes detected.
- **Returned boxes** count output boxes. The two totals differ, but without annotations they do not tell us which mode is more accurate.
- **Observed duration** counts frames where an ID had a detection. A track's elapsed first-to-last span can be longer if there are gaps.
- A **gap episode** means an ID was emitted, absent for one or more processed frames, then emitted again. This is an observation gap, not a confirmed false negative.
- **Adjacent-frame IoU** measures overlap between consecutive boxes assigned the same ID. It is a geometric continuity proxy, not proof the ID follows the same physical pothole.
- **Multiple observed runs** counts within-ID runs separated by gaps. It is a fragmentation proxy, not ground-truth identity-switch or fragmentation measurement.

### Observation versus conclusion

**Supported observations:** both modes processed 692 frames with the recorded settings; baseline emitted 3,727 boxes and tracking mode emitted 2,801; tracking emitted 119 IDs; and the reported durations, gaps, and box-continuity calculations are internally consistent with the saved per-frame detection records.

**Not supported:** that ByteTrack improved or reduced detection accuracy, recall, precision, false-positive rate, or correct physical-pothole identity. Detection totals are mode outputs, not labels-based scores. Ground-truth boxes and persistent identities are needed to support those claims.

## 5. Limitations

1. **No ground truth:** The evaluated video has no verified frame-level pothole boxes and identity annotations in this experiment. Detection accuracy, precision, recall, false negatives, and correct track identity therefore remain unknown.
2. **Checkpoint provenance is unverified:** The file is `best.pt`, but its author/source, training data, procedure, and license are not documented. Do not identify it as the paper authors' checkpoint.
3. **Tracking metrics are proxies:** Gaps mean IDs temporarily were not emitted and later reappeared. Duration, IoU, and observed-run fragmentation describe outputs, not ground-truth tracking errors or identity switches.

Additional caveat: this is a single video/checkpoint/configuration and a single run per mode. Reported FPS is not a robust comparative benchmark.

## 6. Suggested slide sequence

### Slide 1 — Research question and motivation
- Key points: Frame-by-frame detections may be difficult to follow over time; the project tests detector-to-tracker association.
- Visual: Use a still frame from the existing input video or a frame from one of the saved demo videos. Label it as an example frame, not a new experiment result.

### Slide 2 — Scope and claims
- Key points: Existing YOLO detector plus ByteTrack video association; evaluate output continuity; no retraining or ground-truth accuracy study in this run.
- Visual: Simple workflow diagram labeled “proposed explanatory diagram,” or reuse the verified workflow in this plan.

### Slide 3 — Detector and checkpoint
- Key points: Ultralytics detection task, class `Pothole`; checkpoint is local `best.pt`; provenance, training and license are unknown.
- Visual: A screenshot of the command output/model class or an annotated video frame. Do not show a paper attribution without evidence.

### Slide 4 — Video processing workflow
- Key points: MP4 → ordered frames → 1020×500 resize → YOLO CPU inference → optional tracking IDs → annotated MP4.
- Visual: `p_baseline.mp4` and `p_bytetrack.mp4` opening frames or a clearly labeled workflow diagram.

### Slide 5 — Fair mode comparison setup
- Key points: Same 692-frame video, checkpoint, confidence 0.25, CPU and resize; `predict` baseline versus persistent `track` with `bytetrack.yaml`.
- Visual: A two-column settings table from this plan; no new plot required.

### Slide 6 — Returned output summary
- Key points: Show the verified table rows for frames, frames with returned detections and returned boxes. Emphasize these are output counts, not accuracy.
- Visual: Existing `detections_by_frame.png` from the latest analysis folder.

### Slide 7 — Track duration and gaps
- Key points: 119 IDs; duration thresholds; 114 gap episodes and 331 missing track-frames; gaps are unobserved intervals.
- Visual: Existing `track_duration_distribution.png` and/or `gaps_and_box_continuity.png` from the latest analysis folder.

### Slide 8 — Visual demonstration
- Key points: Show the same segment from each video; identify boxes/confidence in both and IDs only in the tracked output. Playback demonstrates behavior, not accuracy.
- Visual: Play `outputs/professor_demo_20261027/p_baseline.mp4`, then `outputs/professor_demo_20261027/p_bytetrack.mp4`.

### Slide 9 — Limits and next research step
- Key points: Unknown checkpoint provenance, no ground-truth video identities, single video and single timing run; annotated video is required for accuracy and identity metrics.
- Visual: A short future-work list. Any proposed annotation example is future work and should be labeled as such.

### Slide 10 — Takeaway and questions
- Key points: Current verified contribution is a YOLO + ByteTrack video pipeline and a descriptive paired output analysis; accuracy/identity claims await ground truth.
- Visual: One-sentence takeaway and questions; no additional metric graphic needed.

## 7. Demonstration plan

Use the two verified files and show the same segment or play both complete outputs if time allows:

1. Baseline: `outputs/professor_demo_20261027/p_baseline.mp4`.
2. YOLO + ByteTrack: `outputs/professor_demo_20261027/p_bytetrack.mp4`.

State that both were generated from the same input video, `best.pt`, confidence 0.25, CPU inference, and 1020×500 resize; the mode difference is per-frame `predict` versus persistent `track` with `bytetrack.yaml`. In baseline, labels show class/confidence. In tracking mode, IDs appear when the tracker returns them.

Point out visible temporal behavior as an illustration of the implementation only. Do not claim that fewer/more boxes, a long-lived ID, an apparent stable ID, or visual smoothness proves better detection accuracy or correct real pothole identity. The saved files were verified as 692-frame 25-FPS MP4s at 1020×500.

## 8. Likely professor questions

1. **Is `best.pt` the paper authors' trained model?**
   Unknown. The local checkpoint's source and author are not documented, so I cannot attribute it to the paper authors.
2. **What model task and class does it expose?**
   It loads as an Ultralytics detection model with class name `Pothole`.
3. **What does ByteTrack add here?**
   It associates detections between consecutive frames and provides IDs when available; the code uses persistent tracking with `bytetrack.yaml`.
4. **Why are there fewer boxes in tracking mode?**
   The modes return different outputs. Without ground-truth labels, the count difference cannot tell us whether either mode is more accurate.
5. **Does 98.12% versus 93.35% indicate recall?**
   No. Those values are the fractions of frames with at least one returned box, not recall against annotated potholes.
6. **Are the 114 gaps false negatives?**
   No. They mark an ID absent from processed outputs and later reappearing. The saved data cannot establish whether the pothole was still visible or should have been detected.
7. **Does mean adjacent IoU of 0.801708 prove stable identities?**
   No. It measures box overlap between consecutive detections assigned the same ID; it does not verify physical object identity.
8. **How do we know the baseline and tracking setup is fair?**
   The saved frame records show the same video, checkpoint, confidence, device and resize, with the intended mode/tracker difference. It remains a single-video output comparison, not a labeled accuracy evaluation.
9. **Can we claim a speed improvement?**
   Not from this experiment. There is one timing run per mode and no randomized order or repeated benchmark trials.
10. **What is required to establish accuracy or identity-switch performance?**
    Annotated video with pothole boxes per frame and persistent ground-truth identities, then suitable detection and tracking metrics compared against those labels.

## 9. Short spoken explanation (about 60–90 seconds)

“My project investigates temporal consistency in video pothole detection. The current pipeline uses an Ultralytics YOLO detection checkpoint and compares frame-by-frame prediction with the same model run through persistent ByteTrack. Both modes use the same 692-frame video, confidence threshold of 0.25, CPU inference, and 1020-by-500 frame resize. The saved run recorded 3,727 returned boxes in baseline mode and 2,801 in tracking mode. ByteTrack emitted 119 IDs, with 114 ID reappearance gaps; the average overlap between consecutive boxes assigned the same ID was about 0.802. These numbers describe the system outputs and continuity proxies, not detection accuracy or proof that an ID follows the same physical pothole. We do not yet have ground-truth frame boxes and identities, and the checkpoint's provenance and training details are unverified. My next research step is to obtain or create annotated video ground truth so detection quality and tracking identity performance can be evaluated rather than inferred from output counts.”
