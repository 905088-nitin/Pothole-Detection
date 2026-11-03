# Professor Demonstration Guide

Run commands from the project root:

`/Users/nitinror/Downloads/Pothole-Detection-through-images-and-videos-using-CNN-main`

## Verified inputs and environment

- Input video: `pothole detection/pothoels-segmentation/p.mp4`
- Checkpoint: `best.pt` in the project root
- Configured environment: `.venv` using Python 3.14.2
- Verified packages: Ultralytics 8.4.190, PyTorch 2.14.1, OpenCV 5.0.0, NumPy 2.5.4
- Input video verified readable: 692 frames, 25 FPS, 1280x720
- The checkpoint loads as an Ultralytics detection model with class `Pothole`. Its source, training details, and license are unverified; see `PROJECT_STATUS.md`.

## Demonstration commands

Baseline YOLO detection:

```bash
.venv/bin/python "pothole detection/pothoels-segmentation/test(for video).py" \
  "pothole detection/pothoels-segmentation/p.mp4" \
  --weights best.pt \
  --conf 0.25 \
  --mode baseline \
  --output outputs/professor_demo_20261027/p_baseline.mp4
```

YOLO + ByteTrack:

```bash
.venv/bin/python "pothole detection/pothoels-segmentation/test(for video).py" \
  "pothole detection/pothoels-segmentation/p.mp4" \
  --weights best.pt \
  --conf 0.25 \
  --mode track \
  --output outputs/professor_demo_20261027/p_bytetrack.mp4
```

Both commands use the same video, checkpoint, confidence, CPU inference, and 1020x500 frame resize. The intended difference is `predict` baseline versus persistent `track` with `bytetrack.yaml`. The separate output names preserve previous videos.

Press `q` in the OpenCV preview window to stop early. For a complete output, let the video finish.

## Verified demonstration outputs

The commands above were run on 2026-10-27. Both scripts processed 692 frames:

- `outputs/professor_demo_20261027/p_baseline.mp4`: 3,727 boxes returned.
- `outputs/professor_demo_20261027/p_bytetrack.mp4`: 2,801 boxes returned.

Both generated MP4s were reopened with OpenCV and verified to contain 692 readable frames at 25 FPS and 1020x500. A separate real tracking pass on the input produced 2,801 detections and 119 unique track IDs. The script displays an ID when `result.boxes.id` is supplied by the tracker.

These are implementation/output checks, not accuracy results. Returned detection counts are not directly comparable as accuracy. No ground-truth video annotations establish pothole detection accuracy or correct real-object identity; do not claim ByteTrack improves accuracy or guarantees stable IDs from this demonstration alone.

## Troubleshooting

- `YOLO checkpoint does not exist`: run from the project root, confirm `best.pt` is in the root, or pass its actual path using `--weights`.
- `video file does not exist` or `could not open video`: confirm the input MP4 path and that OpenCV can read it.
- `ModuleNotFoundError`: select/activate the project `.venv` and verify Ultralytics, OpenCV, NumPy, and PyTorch are installed there.
- No visible detections: confirm the checkpoint is the expected pothole detector and inspect model class names, video contents, and confidence threshold. Do not lower confidence solely to make the demo look busier; justify threshold changes separately.
- No visible ID text: IDs are shown only in `--mode track` when the tracker returns IDs. Baseline mode intentionally has no track IDs.
