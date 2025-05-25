import cv2
from yolov5 import YOLOv5
import threading

# Load model once
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

        # Fast prediction (smaller size)
        results = model.predict(img, size=320)
        img = results.render()[0]

        cv2.imshow("ESP32 YOLO Detection", img)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            stopped = True
            break

if __name__ == "__main__":
    print("Starting threads...")
    threading.Thread(target=capture_stream, daemon=True).start()
    detection_loop()
    print("Shutting down...")
    cv2.destroyAllWindows()
