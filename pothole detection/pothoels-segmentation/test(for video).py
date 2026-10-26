from ultralytics import YOLO
import cv2
import numpy as np
import cvzone

# Load the trained YOLO model (make sure best.pt is in the same folder)
model = YOLO("best.pt")
class_names = model.names

# Load the video file (make sure p.mp4 is in the same folder)
cap = cv2.VideoCapture('p.mp4')
count = 0

while True:
    ret, img = cap.read()
    if not ret:
        break

    count += 1
    # Skip every 3rd frame to reduce CPU load
    if count % 3 != 0:
        continue

    # Resize the image for display/performance
    img = cv2.resize(img, (1020, 500))
    h, w, _ = img.shape

    # Run YOLO prediction (forced to CPU for compatibility)
    results = model.predict(img, device='cpu')

    for r in results:
      boxes = r.boxes
      masks = r.masks

      if masks is not None:
        masks = masks.data.cpu().numpy()

        for seg, box in zip(masks, boxes):
            seg = cv2.resize(seg, (w, h))
            contours, _ = cv2.findContours((seg > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                # 🔢 Calculate pothole area percentage
                mask_area = cv2.contourArea(contour)
                frame_area = w * h
                area_percent = (mask_area / frame_area) * 100

                percent_text = f"Pothole: {area_percent:.2f}%"

                x, y, x1, y1 = cv2.boundingRect(contour)

                # 🔵 Draw blue contour
                x, y, w_box, h_box = cv2.boundingRect(contour)
                cv2.rectangle(img, (x, y), (x + w_box, y + h_box), (0, 255, 0), 2)


                # 🧾 Show percentage instead of label
                cv2.putText(img, percent_text, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)


    # Show the processed frame
    cv2.imshow('img', img)

    # Exit if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
