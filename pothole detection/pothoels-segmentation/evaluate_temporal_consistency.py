import argparse
import csv
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import cv2
from ultralytics import YOLO


FRAME_WIDTH = 1020
FRAME_HEIGHT = 500
CONFIDENCE = 0.25
DEVICE = "cpu"
TRACKER = "bytetrack.yaml"


def csv_writer(path, fieldnames):
    file = path.open("w", newline="", encoding="utf-8")
    return file, csv.DictWriter(file, fieldnames=fieldnames)


def evaluate_mode(
    mode, video_path, weights_path, confidence, frame_writer, detection_writer
):
    model = YOLO(str(weights_path))
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        cap.release()
        raise RuntimeError(f"Could not open video for {mode} run: {video_path}")

    processed_frames = 0
    frames_with_detections = 0
    total_detections = 0
    detection_record_count = 0
    detections_without_track_id = 0
    track_frames = defaultdict(list)
    frame_processing_seconds = []
    start_time = time.perf_counter()

    try:
        while True:
            frame_start = time.perf_counter()
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            if mode == "track":
                results = model.track(
                    frame,
                    persist=True,
                    tracker=TRACKER,
                    device=DEVICE,
                    conf=confidence,
                    verbose=False,
                )
            else:
                results = model.predict(
                    frame,
                    device=DEVICE,
                    conf=confidence,
                    verbose=False,
                )

            boxes = [
                box
                for result in results
                if result.boxes is not None
                for box in result.boxes
            ]
            track_ids = []
            frame_detection_records = 0
            for detection_index, box in enumerate(boxes, start=1):
                class_id = int(box.cls.item())
                class_name = model.names.get(class_id, str(class_id)) if isinstance(
                    model.names, dict
                ) else model.names[class_id]
                track_id = ""
                if mode == "track" and box.id is not None:
                    track_id = int(box.id.item())
                    track_ids.append(track_id)
                    track_frames[track_id].append(processed_frames)
                elif mode == "track":
                    detections_without_track_id += 1

                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detection_writer.writerow(
                    {
                        "mode": mode,
                        "frame_index": processed_frames + 1,
                        "detection_index": detection_index,
                        "track_id": track_id,
                        "class_id": class_id,
                        "class_name": class_name,
                        "confidence": float(box.conf.item()),
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                    }
                )
                frame_detection_records += 1

            if frame_detection_records != len(boxes):
                raise RuntimeError(
                    f"{mode} frame {processed_frames + 1}: wrote "
                    f"{frame_detection_records} detection records for {len(boxes)} detections"
                )

            elapsed = time.perf_counter() - frame_start
            frame_processing_seconds.append(elapsed)
            processed_frames += 1
            detection_count = len(boxes)
            if frame_detection_records != detection_count:
                raise RuntimeError(
                    f"{mode} frame {processed_frames}: detection record count "
                    "does not match frame statistics"
                )
            if mode == "track" and len(track_ids) + sum(
                box.id is None for box in boxes
            ) != detection_count:
                raise RuntimeError(
                    f"track frame {processed_frames}: detections with and without IDs "
                    "do not sum to the detection count"
                )
            frames_with_detections += detection_count > 0
            total_detections += detection_count
            detection_record_count += frame_detection_records
            frame_writer.writerow(
                {
                    "mode": mode,
                    "frame_index": processed_frames,
                    "detection_count": detection_count,
                    "track_ids": ";".join(map(str, track_ids)),
                    "frame_processing_seconds": f"{elapsed:.6f}",
                    "frame_processing_fps": f"{1.0 / elapsed:.3f}" if elapsed else "",
                    "checkpoint": str(weights_path),
                    "video": str(video_path),
                    "confidence": confidence,
                    "resize_width": FRAME_WIDTH,
                    "resize_height": FRAME_HEIGHT,
                    "device": DEVICE,
                    "tracker": TRACKER if mode == "track" else "none",
                }
            )
    finally:
        cap.release()

    total_seconds = time.perf_counter() - start_time
    average_fps = processed_frames / total_seconds if total_seconds else 0.0
    return {
        "mode": mode,
        "processed_frames": processed_frames,
        "frames_with_detections": frames_with_detections,
        "total_detections": total_detections,
        "detection_record_count": detection_record_count,
        "detections_without_track_id": detections_without_track_id,
        "track_frames": track_frames,
        "processing_seconds": total_seconds,
        "average_fps": average_fps,
        "frame_processing_seconds": frame_processing_seconds,
    }


def write_track_reports(track_frames, duration_writer, gap_writer):
    total_gap_episodes = 0
    total_gap_frames = 0

    for track_id, observed_frames in sorted(track_frames.items()):
        observed_frames = sorted(observed_frames)
        gaps = []
        for previous_frame, next_frame in zip(observed_frames, observed_frames[1:]):
            missing_frames = next_frame - previous_frame - 1
            if missing_frames > 0:
                gaps.append((previous_frame, next_frame, missing_frames))
                gap_writer.writerow(
                    {
                        "track_id": track_id,
                        "last_observed_frame": previous_frame + 1,
                        "reappeared_frame": next_frame + 1,
                        "missing_frames": missing_frames,
                        "interpretation": "unobserved interval; not a confirmed false negative",
                    }
                )

        gap_count = len(gaps)
        gap_frames = sum(gap[2] for gap in gaps)
        total_gap_episodes += gap_count
        total_gap_frames += gap_frames
        duration_writer.writerow(
            {
                "track_id": track_id,
                "observed_frames": len(observed_frames),
                "first_observed_frame": observed_frames[0] + 1,
                "last_observed_frame": observed_frames[-1] + 1,
                "span_frames_including_gaps": observed_frames[-1] - observed_frames[0] + 1,
                "gap_episodes": gap_count,
                "missing_frames_within_span": gap_frames,
                "duration_note": "observed detection frames; not proof of object presence",
            }
        )

    return total_gap_episodes, total_gap_frames


def write_csv(path, fieldnames, rows):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Compare baseline YOLO detections and ByteTrack temporal statistics."
    )
    parser.add_argument("video", type=Path, help="Input video path")
    parser.add_argument(
        "--weights",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "best.pt",
        help="YOLO checkpoint (default: best.pt in the project root)",
    )
    parser.add_argument("--conf", type=float, default=CONFIDENCE)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "outputs" / "temporal_evaluation",
    )
    args = parser.parse_args()

    video_path = args.video.expanduser().resolve()
    weights_path = args.weights.expanduser().resolve()
    if not video_path.is_file():
        parser.error(f"video file does not exist: {video_path}")
    if not weights_path.is_file():
        parser.error(f"YOLO checkpoint does not exist: {weights_path}")
    if not 0.0 <= args.conf <= 1.0:
        parser.error("--conf must be between 0 and 1")

    metadata_cap = cv2.VideoCapture(str(video_path))
    if not metadata_cap.isOpened():
        metadata_cap.release()
        parser.error(f"could not open input video: {video_path}")
    video_fps = metadata_cap.get(cv2.CAP_PROP_FPS)
    video_width = int(metadata_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(metadata_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    metadata_frame_count = int(metadata_cap.get(cv2.CAP_PROP_FRAME_COUNT))
    metadata_cap.release()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    run_dir = args.output_dir / datetime.now().strftime("run_%Y%m%d_%H%M%S_%f")
    run_dir.mkdir()
    frame_path = run_dir / "frame_stats.csv"
    duration_path = run_dir / "track_durations.csv"
    gaps_path = run_dir / "track_gaps.csv"
    summary_path = run_dir / "summary.csv"
    detection_path = run_dir / "detection_records.csv"

    frame_fields = [
        "mode", "frame_index", "detection_count", "track_ids",
        "frame_processing_seconds", "frame_processing_fps", "checkpoint", "video",
        "confidence", "resize_width", "resize_height", "device", "tracker",
    ]
    frame_file, frame_writer = csv_writer(frame_path, frame_fields)
    detection_fields = [
        "mode", "frame_index", "detection_index", "track_id", "class_id",
        "class_name", "confidence", "x1", "y1", "x2", "y2",
    ]
    detection_file, detection_writer = csv_writer(detection_path, detection_fields)
    frame_writer.writeheader()
    detection_writer.writeheader()
    try:
        baseline = evaluate_mode(
            "baseline", video_path, weights_path, args.conf, frame_writer, detection_writer
        )
        tracked = evaluate_mode(
            "track", video_path, weights_path, args.conf, frame_writer, detection_writer
        )
    finally:
        frame_file.close()
        detection_file.close()

    for result in (baseline, tracked):
        if result["detection_record_count"] != result["total_detections"]:
            raise RuntimeError(
                f"{result['mode']}: detection-record rows do not match total detections"
            )

    duration_fields = [
        "track_id", "observed_frames", "first_observed_frame", "last_observed_frame",
        "span_frames_including_gaps", "gap_episodes", "missing_frames_within_span", "duration_note",
    ]
    gap_fields = [
        "track_id", "last_observed_frame", "reappeared_frame", "missing_frames", "interpretation",
    ]
    with duration_path.open("w", newline="", encoding="utf-8") as duration_file, gaps_path.open(
        "w", newline="", encoding="utf-8"
    ) as gaps_file:
        duration_writer = csv.DictWriter(duration_file, fieldnames=duration_fields)
        gap_writer = csv.DictWriter(gaps_file, fieldnames=gap_fields)
        duration_writer.writeheader()
        gap_writer.writeheader()
        gap_episodes, missing_gap_frames = write_track_reports(
            tracked["track_frames"], duration_writer, gap_writer
        )

    summary_rows = []
    for result in (baseline, tracked):
        tracks = result["track_frames"]
        durations = [len(frames) for frames in tracks.values()]
        summary_rows.append(
            {
                "mode": result["mode"],
                "processed_frames": result["processed_frames"],
                "frames_with_detections": result["frames_with_detections"],
                "total_detections": result["total_detections"],
                "unique_track_ids": len(tracks) if result["mode"] == "track" else "",
                "tracks_at_least_5_frames": sum(duration >= 5 for duration in durations),
                "tracks_at_least_10_frames": sum(duration >= 10 for duration in durations),
                "tracks_at_least_20_frames": sum(duration >= 20 for duration in durations),
                "track_gap_episodes": gap_episodes if result["mode"] == "track" else "",
                "missing_frames_in_track_gaps": missing_gap_frames if result["mode"] == "track" else "",
                "processing_seconds": f"{result['processing_seconds']:.3f}",
                "average_processing_fps": f"{result['average_fps']:.3f}",
                "confidence": args.conf,
                "checkpoint": str(weights_path),
                "video": str(video_path),
                "video_fps": video_fps,
                "video_resolution": f"{video_width}x{video_height}",
                "metadata_frame_count": metadata_frame_count,
                "resize": f"{FRAME_WIDTH}x{FRAME_HEIGHT}",
                "device": DEVICE,
                "tracker": TRACKER if result["mode"] == "track" else "none",
                "metric_scope": "measured detections and proxy tracking continuity; no ground-truth accuracy claim",
            }
        )

    summary_fields = list(summary_rows[0])
    write_csv(summary_path, summary_fields, summary_rows)

    print(f"Input: {video_path}")
    print(f"Checkpoint: {weights_path}")
    print(f"Video: {video_fps:g} FPS, {video_width}x{video_height}, {metadata_frame_count} metadata frames")
    print(f"Confidence: {args.conf}; resize: {FRAME_WIDTH}x{FRAME_HEIGHT}; device: {DEVICE}")
    print("\nMode      Frames  Frames w/det  Detections  Unique IDs  Avg FPS  Time (s)")
    for row in summary_rows:
        print(
            f"{row['mode']:<9} {row['processed_frames']:>6}  "
            f"{row['frames_with_detections']:>13}  {row['total_detections']:>10}  "
            f"{str(row['unique_track_ids']):>10}  {row['average_processing_fps']:>7}  "
            f"{row['processing_seconds']:>7}"
        )
    print(
        "\nTrack duration means frames where the ID had a detection. Gaps mean an ID "
        "was absent and later reappeared; neither is a ground-truth false-negative or accuracy metric."
    )
    print(f"Frame statistics: {frame_path}")
    print(f"Track durations: {duration_path}")
    print(f"Track gaps: {gaps_path}")
    print(f"Comparison summary: {summary_path}")
    print(f"Detection records: {detection_path}")
    print(
        "Detection-record validation: "
        f"baseline {baseline['detection_record_count']}/{baseline['total_detections']} rows; "
        f"track {tracked['detection_record_count']}/{tracked['total_detections']} rows, "
        f"{tracked['detections_without_track_id']} detections without track IDs"
    )


if __name__ == "__main__":
    main()