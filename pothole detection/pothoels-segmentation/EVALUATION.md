# Temporal evaluation

Run the paired baseline and ByteTrack evaluation from the project root:

```bash
.venv/bin/python "pothole detection/pothoels-segmentation/evaluate_temporal_consistency.py" \
  "pothole detection/pothoels-segmentation/p.mp4" \
  --weights best.pt \
  --conf 0.25 \
  --output-dir outputs/temporal_evaluation
```

Each run writes a new timestamped directory under the output directory. It contains `frame_stats.csv`, `track_durations.csv`, `track_gaps.csv`, `summary.csv`, and `detection_records.csv`.

`detection_records.csv` has one row per detector output. `frame_index` and `detection_index` are one-based. `x1`, `y1`, `x2`, and `y2` are floating-point pixel coordinates in `xyxy` order relative to the resized 1020-by-500 frame passed to YOLO, not the original video dimensions. `track_id` is blank when no ID is provided (including baseline mode). Confidence and class values come from that same result box.

The evaluator validates for each frame that the number of detection-record rows matches `frame_stats.csv`'s `detection_count`; in tracking mode it also validates that rows with IDs plus rows without IDs equal the detection count. These are output-integrity checks, not ground-truth accuracy checks. Detection counts, track durations, and gaps do not establish pothole accuracy, recall, or real-object identity without annotated video ground truth.

## Analyze an existing run

Analyze a completed run without rerunning inference or modifying its CSVs:

```bash
.venv/bin/python "pothole detection/pothoels-segmentation/analyze_temporal_consistency.py" \
  "outputs/temporal_evaluation/run_20261027_013633_351042"
```

The analysis script creates a new timestamped `analysis_*` directory inside the run folder. It writes `analysis_summary.csv`, `box_continuity.csv`, `fragmentation_proxies.csv`, and three PNG figures. Use `--output-dir PATH` to choose another new output directory; an existing destination is not overwritten.

Box continuity uses IoU and center displacement between consecutive detections with the same ByteTrack ID. Adjacent-frame transitions are summarized separately from same-ID reappearances after gaps. Fragmentation values count within-ID consecutive-observation runs separated by gaps; they are descriptive proxies, not ground-truth track fragmentation or proof of object identity. No accuracy, recall, precision, or false-negative rate can be inferred without annotated video ground truth.
