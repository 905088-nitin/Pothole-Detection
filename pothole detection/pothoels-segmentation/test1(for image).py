from ultralytics import YOLO
import cv2
import numpy as np
import os

#  Load your segmentation model
model = YOLO("best.pt")  # or "yolov8n-seg.pt"
class_names = model.names

#  Load the image
image_path = "1.jpg"  # change to your image file
if not os.path.exists(image_path):
    print(f"❌ Image not found: {image_path}")
    exit()

img = cv2.imread(image_path)
h, w, _ = img.shape

#  Run prediction
results = model.predict(img, device='cpu')[0]

boxes = results.boxes
masks = results.masks

if masks is not None:
    masks = masks.data.cpu().numpy()

    for seg, box in zip(masks, boxes):
        seg = cv2.resize(seg, (w, h))
        contours, _ = cv2.findContours((seg > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            # Calculate % area
            mask_area = cv2.contourArea(contour)
            frame_area = w * h
            area_percent = (mask_area / frame_area) * 100
            percent_text = f"Pothole: {area_percent:.2f}%"

            x, y, x1, y1 = cv2.boundingRect(contour)

            # 🔵 Draw contour in blue
            cv2.polylines(img, [contour], True, (255, 0, 0), 2)

            # 🧾 Show area %
            cv2.putText(img, percent_text, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

# ✅ Show image
cv2.imshow("YOLOv8 Segmentation", img)
cv2.waitKey(0)
cv2.destroyAllWindows()
