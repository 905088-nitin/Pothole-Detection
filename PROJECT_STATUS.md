# Project Status

**Project:** Pothole Detection through Images and Videos using CNN

**Status date:** 2026-10-27

## Verified implementation

- Video detection uses Ultralytics YOLO with the local `best.pt` checkpoint. The inspected checkpoint runs as a detection model with the class `Pothole`; the video script draws boxes, confidence scores, and track IDs when available.
- The video script supports `baseline` frame-by-frame prediction and `track` mode using Ultralytics `model.track(..., persist=True, tracker="bytetrack.yaml")`.
- The evaluation uses the same checkpoint, input video, confidence threshold (`0.25`), CPU device, and resize (`1020x500`) for both modes. The tracker setting differs by design.
- Evaluation and analysis usage is documented in [EVALUATION.md](pothole%20detection/pothoels-segmentation/EVALUATION.md).

## Checkpoint record and provenance

- Filename: `best.pt` (about 21 MB).
- SHA-256: `1067a09d37e4e9081164e6d6da337ad66d8ec7a884a6a194e58703beee804aa2`.
- The checksum was verified against the local file on 2026-10-27.
- The checkpoint is present locally but is not tracked by Git. No checkpoint source URL, download record, author attribution, model card, or license was found in the inspected project documentation.
- **Unverified:** whether this checkpoint is from the research-paper authors; its training dataset; training procedure; and checkpoint license. Do not attribute it to the paper authors or infer its license from either dataset's license notice.
- The project contains separate dataset notices: the image-segmentation dataset notice states Public Domain, and the pothole-classification dataset notice states CC BY 4.0. These notices do not establish the checkpoint's provenance or license.

## Current saved evaluation

Complete evaluation run: [run_20261027_013633_351042](outputs/temporal_evaluation/run_20261027_013633_351042/). The video metadata recorded in the run is 692 frames, 25 FPS, 1280x720.

| Mode | Processed frames | Frames with detections | Returned boxes |
|---|---:|---:|---:|
| Baseline YOLO | 692 | 679 | 3,727 |
| YOLO + ByteTrack | 692 | 646 | 2,801 |

The tracking run recorded 119 unique IDs, 114 track-gap episodes, and 331 missing track-frames. The separate analysis reports these as descriptive tracking statistics/proxies.

Detection counts are counts of outputs returned by each mode, not accuracy measurements, and are not directly comparable as a measure of detector quality. No ground-truth video annotations have established detection accuracy, recall, precision, false-negative rates, or track-identity correctness. A track gap means an ID was not emitted for processed frame(s) and later reappeared; it is not a confirmed false negative. Gap- and duration-derived fragmentation statistics are proxies, not ground-truth identity switches or fragmentation.

The earlier run at `outputs/temporal_evaluation/run_20261027_012007_154304/` predates detection-level CSV output and does not contain `detection_records.csv`. For per-detection analysis, use the complete run above and the latest analysis folder, `analysis_20261027_015805_475307/`. An earlier analysis folder in that run predates aggregate continuity fields.

## Outstanding before a research demonstration

1. Record the checkpoint provider/source and acquisition date if recoverable; verify its license and training details from the provider. Otherwise present these fields as unknown and describe it as a third-party checkpoint of unverified provenance.
2. Preserve the checkpoint SHA-256 with any shared copy and ensure the local-only checkpoint and current scripts/results are included in the demonstration package as appropriate.
3. Obtain annotated video ground truth with pothole boxes and identities before making detection-accuracy or identity-stability claims.
4. If comparing speed, run repeated trials with warm-up and controlled or randomized mode order; current results are single-run throughput measurements, not a robust benchmark.
5. Keep conclusions limited to the recorded output counts and descriptive temporal proxies until ground-truth evaluation is available.
