import argparse
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description="Run pothole detection on a video.")
    parser.add_argument("video", help="Path to a local input video, such as p.mp4")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the processed MP4, such as outputs/p_processed.mp4",
    )
    parser.add_argument(
        "--weights",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "best.pt",
        help="YOLO checkpoint path (default: best.pt in the project root)",
    )
    parser.add_argument(
        "--mode",
        choices=("baseline", "track"),
        default="track",
        help="Frame-by-frame detection baseline or ByteTrack-enhanced detection",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Detection confidence threshold (default: 0.25)",
    )
    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.is_file():
        parser.error(f"video file does not exist: {video_path}")
    weights_path = args.weights.expanduser().resolve()
    if not weights_path.is_file():
        parser.error(f"YOLO checkpoint does not exist: {weights_path}")
    if not 0.0 <= args.conf <= 1.0:
        parser.error("--conf must be between 0 and 1")

    try:
        model = YOLO(str(weights_path))
    except Exception as exc:
        parser.error(f"could not load YOLO checkpoint {weights_path}: {exc}")
    class_names = model.names
    print(f"Model checkpoint: {weights_path}")
    print(f"Model task: {model.task}")
    print(f"Model classes: {class_names}")
    print(f"Inference mode: {args.mode}; confidence threshold: {args.conf:.2f}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        cap.release()
        parser.error(f"could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    source_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    source_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Input video: {video_path.resolve()}")
    print(
        "Video metadata: "
        f"FPS={fps if fps > 0 else 'unavailable'}, "
        f"resolution={source_width}x{source_height} "
        f"(unavailable if zero), "
        f"frame_count={frame_count if frame_count > 0 else 'unavailable'}"
    )

    output = None
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        output_fps = fps if fps > 0 else 30.0
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        output = cv2.VideoWriter(str(args.output), fourcc, output_fps, (1020, 500))
        if not output.isOpened():
            cap.release()
            output.release()
            parser.error(f"could not create output video: {args.output}")

    processed_frames = 0
    total_detections = 0
    try:
        while True:
            ret, img = cap.read()
            if not ret:
                break

            img = cv2.resize(img, (1020, 500))
            height, width, _ = img.shape
            if args.mode == "track":
                results = model.track(
                    img,
                    persist=True,
                    tracker="bytetrack.yaml",
                    device="cpu",
                    conf=args.conf,
                    verbose=False,
                )
            else:
                results = model.predict(
                    img, device="cpu", conf=args.conf, verbose=False
                )

            for result in results:
                boxes = result.boxes
                masks = result.masks
                detection_count = 0 if boxes is None else len(boxes)
                total_detections += detection_count

                if boxes is not None:
                    mask_data = masks.data.cpu().numpy() if masks is not None else None
                    for index, box in enumerate(boxes):
                        class_id = int(box.cls.item())
                        class_name = (
                            class_names.get(class_id, str(class_id))
                            if isinstance(class_names, dict)
                            else class_names[class_id]
                        )
                        confidence = float(box.conf.item())
                        track_id = (
                            int(box.id.item())
                            if args.mode == "track" and box.id is not None
                            else None
                        )
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        label = f"{class_name} {confidence:.2f}"
                        if track_id is not None:
                            label += f" ID:{track_id}"
                        cv2.putText(
                            img,
                            label,
                            (x1, max(y1 - 10, 20)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (255, 255, 255),
                            2,
                        )

                        if mask_data is not None:
                            seg = cv2.resize(mask_data[index], (width, height))
                            contours, _ = cv2.findContours(
                                (seg > 0.5).astype(np.uint8),
                                cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE,
                            )
                            cv2.drawContours(img, contours, -1, (255, 0, 0), 2)

            if output is not None:
                output.write(img)
            processed_frames += 1
            if processed_frames % 30 == 0:
                print(
                    f"Frame {processed_frames}: "
                    f"{detection_count} detections; "
                    f"cumulative detections={total_detections}"
                )
            cv2.imshow("img", img)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        if output is not None:
            output.release()
        cv2.destroyAllWindows()

    print(f"Processed {processed_frames} frames in original order.")
    print(f"Total detections across processed frames: {total_detections}")
    if processed_frames and total_detections == 0:
        print(
            "No detections found. Check that the checkpoint is compatible and "
            "trained for potholes, inspect the video content and preprocessing, "
            "and try a lower --conf only if justified by validation data."
        )
    if args.output:
        print(f"Output video: {args.output.resolve()}")


if __name__ == "__main__":
    main()
