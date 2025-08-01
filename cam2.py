import cv2
from yolov5 import YOLOv5
import threading
import numpy as np

# Load model once
model = YOLOv5("/Users/vine/elco/DAIO/yolov5/runs/train/eye_model2/weights/best.pt", device="cpu")

frame = None
lock = threading.Lock()
stopped = False

def capture_stream():
    global frame, stopped
    cap = cv2.VideoCapture("http://172.20.10.2/stream")
    while not stopped:
        ret, img = cap.read()
        if not ret:
            continue
        with lock:
            frame = img

def detection_loop():
    global frame, stopped
    while not stopped:
        with lock:
            if frame is None:
                continue
            img = frame.copy()

        # Fast prediction (smaller size)
        results = model.predict(img, size=320)
        
        # Get detection data
        detections = results.pred[0]  # predictions for first image
        img_display = img.copy()
        
        # Process each detection
        for *xyxy, conf, cls in detections:
            if conf > 0.5:  # confidence threshold
                # Get bounding box coordinates
                x1, y1, x2, y2 = map(int, xyxy)
                
                # Calculate eye center
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                # Draw bounding box
                cv2.rectangle(img_display, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Draw eye center
                cv2.circle(img_display, (center_x, center_y), 5, (0, 0, 255), -1)
                cv2.circle(img_display, (center_x, center_y), 10, (0, 0, 255), 2)
                
                # Add labels
                label = f"Eye {conf:.2f}"
                cv2.putText(img_display, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.putText(img_display, f"Center: ({center_x},{center_y})", (x1, y2+20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

        cv2.imshow("ESP32 YOLO Eye Detection with Center", img_display)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            stopped = True
            break

if __name__ == "__main__":
    print("Starting threads...")
    threading.Thread(target=capture_stream, daemon=True).start()
    detection_loop()
    print("Shutting down...")
    cv2.destroyAllWindows()
