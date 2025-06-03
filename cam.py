import cv2
from yolov5 import YOLOv5
import threading

# Load YOLOv5 model
model = YOLOv5("/Users/vine/elco/DAIO/yolov5/runs/train/eye_model2/weights/best.pt", device="cpu")

frame = None
lock = threading.Lock()
stopped = False

def capture_stream():
    global frame, stopped
    cap = cv2.VideoCapture("http://192.168.1.19/stream")
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

        # YOLOv5 prediction
        results = model.predict(img, size=320)
        detections = results.xyxy[0]  # tensor of detections: (x1, y1, x2, y2, conf, cls)

        # Draw bounding boxes and compute center
        for det in detections:
            x1, y1, x2, y2, conf, cls = det.tolist()
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            # Draw center point
            cv2.circle(img, (cx, cy), 5, (0, 0, 255), -1)
            # Draw label and box
            cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cv2.putText(img, f"Iris ({cx}, {cy})", (cx - 40, cy - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            print(f"[INFO] Iris center at: ({cx}, {cy})")

        # Show result
        cv2.imshow("ESP32 Iris Detection", img)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            stopped = True
            break

if __name__ == "__main__":
    print("Starting threads...")
    threading.Thread(target=capture_stream, daemon=True).start()
    detection_loop()
    print("Shutting down...")
    cv2.destroyAllWindows()
