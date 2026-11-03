import argparse
import csv
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


FRAME_COLUMNS = {
    "mode", "frame_index", "detection_count", "track_ids", "checkpoint", "video",
    "confidence", "resize_width", "resize_height", "device", "tracker",
}
DETECTION_COLUMNS = {
    "mode", "frame_index", "detection_index", "track_id", "class_id", "class_name",
    "confidence", "x1", "y1", "x2", "y2",
}
DURATION_COLUMNS = {
    "track_id", "observed_frames", "first_observed_frame", "last_observed_frame",
    "span_frames_including_gaps", "gap_episodes", "missing_frames_within_span",
}
GAP_COLUMNS = {
    "track_id", "last_observed_frame", "reappeared_frame", "missing_frames",
}


def read_csv(path, required_columns):
    if not path.is_file():
        raise ValueError(f"Required CSV is missing: {path}")
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file, strict=True)
        missing = required_columns - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path.name} is missing columns: {sorted(missing)}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"Required CSV has no data rows: {path}")
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"Malformed CSV row in {path}")
    return rows


def box_iou(first, second):
    left = max(first["x1"], second["x1"])
    top = max(first["y1"], second["y1"])
    right = min(first["x2"], second["x2"])
    bottom = min(first["y2"], second["y2"])
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    first_area = max(0.0, first["x2"] - first["x1"]) * max(
        0.0, first["y2"] - first["y1"]
    )
    second_area = max(0.0, second["x2"] - second["x1"]) * max(
        0.0, second["y2"] - second["y1"]
    )
    union = first_area + second_area - intersection
    return intersection / union if union > 0 else 0.0


def summarize_distribution(values, prefix):
    if not values:
        return {
            f"{prefix}_mean": "",
            f"{prefix}_median": "",
            f"{prefix}_max": "",
        }
    return {
        f"{prefix}_mean": f"{statistics.mean(values):.6f}",
        f"{prefix}_median": f"{statistics.median(values):.6f}",
        f"{prefix}_max": f"{max(values):.6f}",
    }


def make_transitions(track_records, frame_width, frame_height):
    by_id = defaultdict(list)
    for record in track_records:
        if record["track_id"]:
            by_id[int(record["track_id"])].append(record)

    transitions = []
    for track_id, records in sorted(by_id.items()):
        records.sort(key=lambda record: (record["frame_index"], record["detection_index"]))
        for previous, current in zip(records, records[1:]):
            previous_center = (
                (previous["x1"] + previous["x2"]) / 2,
                (previous["y1"] + previous["y2"]) / 2,
            )
            current_center = (
                (current["x1"] + current["x2"]) / 2,
                (current["y1"] + current["y2"]) / 2,
            )
            dx = current_center[0] - previous_center[0]
            dy = current_center[1] - previous_center[1]
            frame_gap = current["frame_index"] - previous["frame_index"] - 1
            transitions.append(
                {
                    "track_id": track_id,
                    "previous_frame": previous["frame_index"],
                    "current_frame": current["frame_index"],
                    "missing_frames": frame_gap,
                    "transition_type": "adjacent_frame" if frame_gap == 0 else "reappearance_after_gap",
                    "box_iou": box_iou(previous, current),
                    "center_displacement_pixels": (dx * dx + dy * dy) ** 0.5,
                    "center_displacement_normalized": (
                        (dx * dx + dy * dy) ** 0.5 / (frame_width * frame_width + frame_height * frame_height) ** 0.5
                    ),
                }
            )
    return transitions, by_id


def write_rows(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def create_plots(output_dir, frame_rows, duration_values, gap_values, adjacent_transitions):
    colors = {"baseline": "#245b70", "track": "#c45a35"}
    fig, axis = plt.subplots(figsize=(10, 4.5), constrained_layout=True)
    for mode in ("baseline", "track"):
        rows = sorted((row for row in frame_rows if row["mode"] == mode), key=lambda row: row["frame_index"])
        axis.plot(
            [row["frame_index"] for row in rows],
            [row["detection_count"] for row in rows],
            color=colors[mode],
            linewidth=1.0,
            alpha=0.85,
            label=mode.capitalize(),
        )
    axis.set(title="Detections by processed frame", xlabel="Frame index", ylabel="Detection count")
    axis.legend(frameon=False)
    axis.grid(axis="y", alpha=0.2)
    fig.savefig(output_dir / "detections_by_frame.png", dpi=300)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    if duration_values:
        bins = min(25, max(5, len(set(duration_values))))
        axis.hist(duration_values, bins=bins, color="#547b62", edgecolor="white")
        for threshold in (5, 10, 20):
            axis.axvline(threshold, color="#333333", linestyle="--", linewidth=1)
    axis.set(title="Observed detections per ByteTrack ID", xlabel="Observed frames per ID", ylabel="Track ID count")
    axis.grid(axis="y", alpha=0.2)
    fig.savefig(output_dir / "track_duration_distribution.png", dpi=300)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.3), constrained_layout=True)
    if gap_values:
        bins = min(20, max(5, len(set(gap_values))))
        axes[0].hist(gap_values, bins=bins, color="#c45a35", edgecolor="white")
    axes[0].set(title="Track reappearance gap lengths", xlabel="Missing processed frames", ylabel="Gap episodes")
    axes[0].grid(axis="y", alpha=0.2)
    ious = [transition["box_iou"] for transition in adjacent_transitions]
    if ious:
        axes[1].hist(ious, bins=20, range=(0, 1), color="#245b70", edgecolor="white")
    axes[1].set(title="Adjacent-frame box IoU", xlabel="IoU between consecutive observations", ylabel="Track transitions")
    axes[1].grid(axis="y", alpha=0.2)
    fig.savefig(output_dir / "gaps_and_box_continuity.png", dpi=300)
    plt.close(fig)


def analyze(results_dir, output_dir):
    frames = read_csv(results_dir / "frame_stats.csv", FRAME_COLUMNS)
    detections = read_csv(results_dir / "detection_records.csv", DETECTION_COLUMNS)
    durations = read_csv(results_dir / "track_durations.csv", DURATION_COLUMNS)
    gaps = read_csv(results_dir / "track_gaps.csv", GAP_COLUMNS)
    original_summary = read_csv(results_dir / "summary.csv", {"mode", "processed_frames"})
    summary_lookup = {row["mode"]: row for row in original_summary}

    detections_by_frame = defaultdict(list)
    for record in detections:
        record["frame_index"] = int(record["frame_index"])
        record["detection_index"] = int(record["detection_index"])
        record["class_id"] = int(record["class_id"])
        record["confidence"] = float(record["confidence"])
        for key in ("x1", "y1", "x2", "y2"):
            record[key] = float(record[key])
        detections_by_frame[(record["mode"], record["frame_index"])].append(record)

    frame_lookup = {}
    for row in frames:
        key = (row["mode"], int(row["frame_index"]))
        if key in frame_lookup:
            raise ValueError(f"Duplicate frame-stat row: {key}")
        frame_lookup[key] = int(row["detection_count"])
    for key, count in frame_lookup.items():
        if len(detections_by_frame.get(key, [])) != count:
            raise ValueError(
                f"Detection CSV count mismatch at {key}: expected {count}, "
                f"found {len(detections_by_frame.get(key, []))}"
            )
    if set(detections_by_frame) - set(frame_lookup):
        raise ValueError("Detection records reference frames absent from frame_stats.csv")

    track_records = [record for record in detections if record["mode"] == "track"]
    summary_rows = []
    duration_by_id = {int(row["track_id"]): row for row in durations}
    observed_by_id = defaultdict(list)
    for record in track_records:
        if record["track_id"]:
            observed_by_id[int(record["track_id"])].append(record["frame_index"])

    expected_ids = set(observed_by_id)
    if expected_ids != set(duration_by_id):
        raise ValueError("Track ID set in detection_records.csv differs from track_durations.csv")
    for track_id, observed in observed_by_id.items():
        duration_row = duration_by_id[track_id]
        if len(observed) != int(duration_row["observed_frames"]):
            raise ValueError(f"Observed duration mismatch for track ID {track_id}")
        ordered_frames = sorted(observed)
        if (
            ordered_frames[0] != int(duration_row["first_observed_frame"])
            or ordered_frames[-1] != int(duration_row["last_observed_frame"])
            or ordered_frames[-1] - ordered_frames[0] + 1
            != int(duration_row["span_frames_including_gaps"])
        ):
            raise ValueError(f"Track span mismatch for track ID {track_id}")

    expected_gaps = set()
    for track_id, observed in observed_by_id.items():
        ordered_frames = sorted(observed)
        for previous_frame, current_frame in zip(ordered_frames, ordered_frames[1:]):
            missing = current_frame - previous_frame - 1
            if missing > 0:
                expected_gaps.add((track_id, previous_frame, current_frame, missing))
    saved_gaps = {
        (
            int(row["track_id"]),
            int(row["last_observed_frame"]),
            int(row["reappeared_frame"]),
            int(row["missing_frames"]),
        )
        for row in gaps
    }
    if expected_gaps != saved_gaps:
        raise ValueError("track_gaps.csv does not match the per-frame track observations")

    for mode in ("baseline", "track"):
        mode_frames = sorted(
            (row for row in frames if row["mode"] == mode),
            key=lambda row: int(row["frame_index"]),
        )
        counts = [int(row["detection_count"]) for row in mode_frames]
        frame_total = len(mode_frames)
        detection_total = sum(counts)
        detection_frames = sum(count > 0 for count in counts)
        mode_ids = {
            int(record["track_id"])
            for record in detections
            if record["mode"] == mode and record["track_id"]
        }
        durations_observed = [int(row["observed_frames"]) for row in durations]
        mode_duration_values = durations_observed if mode == "track" else []
        gap_lengths = [int(row["missing_frames"]) for row in gaps]
        mode_summary = summary_lookup.get(mode, {})
        summary_rows.append(
            {
                "mode": mode,
                "processed_frames": frame_total,
                "frames_with_detections": detection_frames,
                "detection_frequency_percent": f"{100 * detection_frames / frame_total:.4f}" if frame_total else "",
                "total_detections": detection_total,
                "average_detections_per_frame": f"{detection_total / frame_total:.6f}" if frame_total else "",
                "unique_track_ids": len(mode_ids) if mode == "track" else "",
                "mean_observed_track_frames": f"{statistics.mean(mode_duration_values):.6f}" if mode_duration_values else "",
                "median_observed_track_frames": f"{statistics.median(mode_duration_values):.6f}" if mode_duration_values else "",
                "max_observed_track_frames": max(mode_duration_values) if mode_duration_values else "",
                "tracks_ge_5_frames": sum(value >= 5 for value in mode_duration_values),
                "tracks_ge_10_frames": sum(value >= 10 for value in mode_duration_values),
                "tracks_ge_20_frames": sum(value >= 20 for value in mode_duration_values),
                "tracks_ge_5_percent": f"{100 * sum(value >= 5 for value in mode_duration_values) / len(mode_duration_values):.4f}" if mode_duration_values else "",
                "tracks_ge_10_percent": f"{100 * sum(value >= 10 for value in mode_duration_values) / len(mode_duration_values):.4f}" if mode_duration_values else "",
                "tracks_ge_20_percent": f"{100 * sum(value >= 20 for value in mode_duration_values) / len(mode_duration_values):.4f}" if mode_duration_values else "",
                "track_gap_episodes": len(gaps) if mode == "track" else "",
                "missing_track_frames": sum(gap_lengths) if mode == "track" else "",
                "mean_gap_frames": f"{statistics.mean(gap_lengths):.6f}" if mode == "track" and gap_lengths else "",
                "max_gap_frames": max(gap_lengths) if mode == "track" and gap_lengths else "",
                "processing_seconds": mode_summary.get("processing_seconds", ""),
                "average_processing_fps": mode_summary.get("average_processing_fps", ""),
                "confidence": mode_summary.get("confidence", ""),
                "checkpoint": mode_summary.get("checkpoint", ""),
                "video": mode_summary.get("video", ""),
                "resize": mode_summary.get("resize", ""),
                "device": mode_summary.get("device", ""),
                "tracker": mode_summary.get("tracker", ""),
                "adjacent_frame_transition_count": "",
                "adjacent_frame_mean_box_iou": "",
                "adjacent_frame_median_box_iou": "",
                "adjacent_frame_mean_normalized_center_displacement": "",
                "reappearance_transition_count": "",
                "reappearance_mean_box_iou": "",
                "reappearance_mean_normalized_center_displacement": "",
                "tracks_with_multiple_observation_runs_proxy": "",
                "extra_observation_runs_after_gaps_proxy": "",
                "metric_note": "Measured model outputs; no ground-truth accuracy claim",
            }
        )

    frame_settings = frames[0]
    frame_width, frame_height = int(frame_settings["resize_width"]), int(frame_settings["resize_height"])
    transitions, by_id = make_transitions(track_records, frame_width, frame_height)
    adjacent = [row for row in transitions if row["transition_type"] == "adjacent_frame"]
    reappearances = [row for row in transitions if row["transition_type"] != "adjacent_frame"]
    gap_counts = Counter(int(row["track_id"]) for row in gaps)
    fragments_per_id = {track_id: 1 + gap_counts[track_id] for track_id in by_id}
    fragmentation = [
        {
            "track_id": track_id,
            "observed_detection_runs_proxy": fragment_count,
            "extra_runs_after_gaps_proxy": fragment_count - 1,
            "gap_episodes": gap_counts[track_id],
            "interpretation": "within-ID observation runs; not ground-truth track fragmentation",
        }
        for track_id, fragment_count in sorted(fragments_per_id.items())
    ]

    continuity_row = {
        "mode": "track",
        "adjacent_frame_transition_count": len(adjacent),
        "adjacent_frame_mean_box_iou": f"{statistics.mean(row['box_iou'] for row in adjacent):.6f}" if adjacent else "",
        "adjacent_frame_median_box_iou": f"{statistics.median(row['box_iou'] for row in adjacent):.6f}" if adjacent else "",
        "adjacent_frame_mean_normalized_center_displacement": f"{statistics.mean(row['center_displacement_normalized'] for row in adjacent):.6f}" if adjacent else "",
        "reappearance_transition_count": len(reappearances),
        "reappearance_mean_box_iou": f"{statistics.mean(row['box_iou'] for row in reappearances):.6f}" if reappearances else "",
        "reappearance_mean_normalized_center_displacement": f"{statistics.mean(row['center_displacement_normalized'] for row in reappearances):.6f}" if reappearances else "",
        "tracks_with_multiple_observation_runs_proxy": sum(value > 1 for value in fragments_per_id.values()),
        "extra_observation_runs_after_gaps_proxy": sum(value - 1 for value in fragments_per_id.values()),
        "interpretation": "box continuity and observation-run fragmentation are proxies, not object-identity ground truth",
    }
    summary_rows[1].update(
        {key: value for key, value in continuity_row.items() if key != "mode" and key != "interpretation"}
    )

    output_dir.mkdir(parents=True, exist_ok=False)
    summary_fields = list(summary_rows[0])
    write_rows(output_dir / "analysis_summary.csv", summary_rows, summary_fields)
    continuity_path = output_dir / "box_continuity.csv"
    transition_fields = [
        "track_id", "previous_frame", "current_frame", "missing_frames", "transition_type",
        "box_iou", "center_displacement_pixels", "center_displacement_normalized",
    ]
    write_rows(continuity_path, transitions, transition_fields)
    fragmentation_path = output_dir / "fragmentation_proxies.csv"
    write_rows(fragmentation_path, fragmentation, list(fragmentation[0]) if fragmentation else [
        "track_id", "observed_detection_runs_proxy", "extra_runs_after_gaps_proxy", "gap_episodes", "interpretation"
    ])
    create_plots(
        output_dir,
        [
            {**row, "frame_index": int(row["frame_index"]), "detection_count": int(row["detection_count"])}
            for row in frames
        ],
        durations_observed,
        gap_lengths,
        adjacent,
    )

    print(f"Analysis output: {output_dir}")
    print("Mode      Frames  Detections  Det/frame  Detection frequency")
    for row in summary_rows:
        print(
            f"{row['mode']:<9} {int(row['processed_frames']):>6}  "
            f"{int(row['total_detections']):>10}  {row['average_detections_per_frame']:>9}  "
            f"{row['detection_frequency_percent']:>18}%"
        )
    print(
        f"Track IDs={len(by_id)}; observed duration mean/median/max="
        f"{statistics.mean(durations_observed):.2f}/{statistics.median(durations_observed):.2f}/{max(durations_observed)} frames"
    )
    print(
        f"Gaps={len(gaps)}; missing track-frames={sum(gap_lengths)}; "
        f"mean/max gap={statistics.mean(gap_lengths):.2f}/{max(gap_lengths)} frames"
    )
    print(
        f"Adjacent-frame box transitions={len(adjacent)}; mean IoU="
        f"{statistics.mean(row['box_iou'] for row in adjacent):.4f}" if adjacent else "Adjacent-frame box transitions=0"
    )
    print(f"Box continuity report: {continuity_path}")
    print(f"Fragmentation proxy report: {fragmentation_path}")
    print("Plots: detections_by_frame.png, track_duration_distribution.png, gaps_and_box_continuity.png")
    print("No ground-truth annotations were used; these are descriptive outputs/proxies, not accuracy or identity validation.")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze existing paired pothole detection and ByteTrack CSV results."
    )
    parser.add_argument("results_dir", type=Path, help="Evaluation run folder containing the five CSV files")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="New directory for reports/plots (default: timestamped analysis folder under results_dir)",
    )
    args = parser.parse_args()

    results_dir = args.results_dir.expanduser().resolve()
    if not results_dir.is_dir():
        parser.error(f"evaluation results directory does not exist: {results_dir}")
    output_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir
        else results_dir / datetime.now().strftime("analysis_%Y%m%d_%H%M%S_%f")
    )
    try:
        analyze(results_dir, output_dir)
    except (OSError, ValueError, KeyError, csv.Error) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()