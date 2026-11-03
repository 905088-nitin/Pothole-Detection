# Results Review: Pothole Detection and ByteTrack

**Prepared:** 2026-10-27

**Evaluation run:** `outputs/temporal_evaluation/run_20261027_013633_351042/`
**Analysis:** `outputs/temporal_evaluation/run_20261027_013633_351042/analysis_20261027_015805_475307/`

## Experiment setup

The saved evaluation uses the same YOLO checkpoint (`best.pt`), video (`pothole detection/pothoels-segmentation/p.mp4`), confidence threshold (`0.25`), CPU device, and frame resize (`1020x500`) for both modes. The baseline uses per-frame YOLO prediction. The tracking mode uses persistent Ultralytics tracking with `bytetrack.yaml`.

The input video metadata is 692 frames, 25 FPS, and 1280x720. Both modes processed all 692 frames. The checkpoint is a detection model with class `Pothole`; its provider, training data/procedure, and license are unverified. It is not identified here as the paper authors' checkpoint.

## Results table

| Measure | Baseline YOLO | YOLO + ByteTrack | Meaning |
|---|---:|---:|---|
| Frames processed | 692 | 692 | Frames read and evaluated in that mode. |
| Frames with at least one returned detection | 679 (98.1214%) | 646 (93.3526%) | Frames where the mode emitted one or more boxes; not recall. |
| Returned detections / boxes | 3,727 | 2,801 | Total boxes emitted by that mode; not an accuracy score. |
| Mean returned boxes per processed frame | 5.385838 | 4.047688 | Returned-box total divided by 692 frames. |
| Unique ByteTrack IDs | Not applicable | 119 | Different IDs emitted at least once in this video. |
| Observed duration per ID, mean / median / maximum | Not applicable | 23.54 / 11 / 117 frames | Number of frames with a detection carrying that ID; not guaranteed physical-object lifetime. |
| IDs observed for at least 5 frames | Not applicable | 78 / 119 (65.5462%) | IDs appearing in five or more processed frames. |
| IDs observed for at least 10 frames | Not applicable | 61 / 119 (51.2605%) | IDs appearing in ten or more processed frames. |
| IDs observed for at least 20 frames | Not applicable | 48 / 119 (40.3361%) | IDs appearing in twenty or more processed frames. |
| Track-gap episodes | Not applicable | 114 | Same ID absent in one or more processed frames and later emitted again. |
| Missing track-frames within gaps | Not applicable | 331 | Sum of unobserved processed-frame intervals across gap episodes. |
| Gap length, mean / maximum | Not applicable | 2.90 / 28 frames | Number of intervening frames between an ID's observations. |
| Consecutive-observation box transitions | Not applicable | 2,568 | Same ID observed in adjacent processed frames. |
| Adjacent-frame box IoU, mean / median | Not applicable | 0.801708 / 0.814433 | Bounding-box overlap between consecutive observations of the same ID; a geometric continuity proxy. |
| IDs with multiple observed runs after gaps | Not applicable | 50 IDs | Within-ID run-count proxy; not ground-truth fragmentation. |
| Extra observed runs after gaps | Not applicable | 114 | Total within-ID runs beyond the first; equals gap count by construction. |

## Metric interpretation

- **Frames with detections** is the number of frames whose output contains at least one box. It describes detector/tracker output frequency, not the percentage of real potholes found.
- **Returned detections** counts boxes returned by the selected mode. It is not precision, recall, or accuracy.
- **Observed track duration** counts detection-bearing frames for an ID. The elapsed span from first to last observation can be longer when gaps occur.
- **Gap episode** is an ID-level observation pattern: an ID is seen, absent for at least one processed frame, then seen again. Missing track-frames are those intervening indices. These are not confirmed missed detections because the CSV has no ground truth stating that the pothole remained visible and detectable.
- **Adjacent-frame IoU** compares the overlap of consecutive boxes assigned the same ID. It measures geometric box continuity for these model outputs, not whether the ID follows the same real pothole.
- **Fragmentation proxies** count observed runs for an ID separated by gaps. They do not measure identity switches, and cannot detect a real pothole that receives a different ID after a break without annotations linking detections to physical potholes.

## Why detection totals are not an accuracy comparison

Baseline YOLO returns per-frame detections, while tracking mode returns detections associated through the tracker. Their counts differ because they are outputs of different modes, not because one mode was tested against labels. Without ground-truth boxes and identities, the results cannot determine whether a box is correct, whether an undetected pothole was present, or whether a track ID stayed attached to the same physical pothole. The lower tracking-mode box total therefore must not be presented as reduced accuracy or improved accuracy.

## Supported findings

The saved CSVs support that both modes processed the same number of frames with the recorded settings; each mode emitted the stated number of boxes; ByteTrack emitted 119 IDs; and the observed durations, gaps, and box-overlap statistics have the reported values. These findings describe this checkpoint on this one video and configuration.

## Conclusions requiring ground truth

No detection accuracy, precision, recall, false-positive rate, false-negative rate, pothole detection improvement, identity-switch rate, or correct physical-pothole identity can be established from these files. Those claims require video annotations with pothole boxes and persistent identities, aligned with the evaluated frames.

## Verification performed

The metrics above were independently recomputed from `frame_stats.csv` and `detection_records.csv`, then compared with `summary.csv`, `track_durations.csv`, `track_gaps.csv`, `analysis_summary.csv`, `box_continuity.csv`, and `fragmentation_proxies.csv`. All compared values matched. In particular, per-mode detection records match per-frame counts; the 114 gap tuples and 331 missing frames reconstruct from tracked IDs; adjacent transitions recompute to 2,568 with mean IoU 0.801708; and the fragmentation proxy recomputes to 50 IDs with multiple observed runs and 114 extra runs.

No inference was rerun for this review. These checks validate CSV arithmetic and consistency, not model accuracy or real-world identity correctness.
