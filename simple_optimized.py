import cv2
from yolov5 import YOLOv5
import threading
import time

# Load model once
model = YOLOv5("/Users/vine/elco/DAIO/yolov5s.pt", device="cpu")

frame = None
lock = threading.Lock()
stopped = False
last_time = time.time()
fps = 0

def capture_stream():
    global frame, stopped
    cap = cv2.VideoCapture("http://192.168.1.19/stream")
    
    # Set buffer size to 1 to get the most recent frame
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    while not stopped:
        ret, img = cap.read()
        if not ret:
            continue
        with lock:
            frame = img

def detection_loop():
    global frame, stopped, last_time, fps
    frame_count = 0
    
    while not stopped:
        with lock:
            if frame is None:
                continue
            img = frame.copy()

        # Fast prediction (smaller size)
        results = model.predict(img, size=320)
        img_result = results.render()[0]
        
        # Calculate FPS
        current_time = time.time()
        frame_count += 1
        if current_time - last_time >= 1.0:
            fps = frame_count / (current_time - last_time)
            frame_count = 0
            last_time = current_time
        
        # Display FPS
        cv2.putText(img_result, f"FPS: {fps:.1f}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("ESP32 YOLO Detection", img_result)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            stopped = True
            break

if __name__ == "__main__":
    print("Starting threads...")
    threading.Thread(target=capture_stream, daemon=True).start()
    detection_loop()
    print("Shutting down...")
    cv2.destroyAllWindows()
