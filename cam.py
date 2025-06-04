import cv2
from yolov5 import YOLOv5
import threading
import time

# Load model
print("[Init] Loading YOLOv5 model...")
model = YOLOv5("/Users/vine/elco/DAIO/yolov5/runs/train/eye_model2/weights/best.pt", device="cpu")
print("[Init] Model loaded.")

# Shared data
frame = None
lock = threading.Lock()
stopped = False

def capture_stream():
    global frame, stopped
    print("[Capture] Connecting to stream...")
    cap = cv2.VideoCapture("http://192.168.1.19/stream")
    if not cap.isOpened():
        print("[Error] Cannot open ESP32 stream.")
        stopped = True
        return

    print("[Capture] Stream connected.")
    while not stopped:
        ret, img = cap.read()
        if not ret:
            print("[Warning] Failed to read frame.")
            time.sleep(0.05)
            continue
        with lock:
            frame = img
    cap.release()
    print("[Capture] Stopped.")

def get_iris_center(predictions):
    for obj in predictions:
        if obj['name'].lower() == 'eye':
            cx = int(obj['x'])
            cy = int(obj['y'])
            return (cx, cy)
    return None

def detection_loop():
    global frame, stopped
    print("[Main] Starting detection loop...")

    reference_center = None
    stable_counter = 0
    stability_required_frames = 5 * 30  # 5 seconds @ ~30 fps
    tolerance = 30  # pixels

    while not stopped:
        with lock:
            if frame is None:
                continue
            img = frame.copy()

        try:
            results = model.predict(img, size=320)
            prediction = results.json()
            detections = prediction["predictions"]

            # Draw all detections
            img = results.render()[0]

            current_center = get_iris_center(detections)
            if current_center:
                cv2.circle(img, current_center, 5, (255, 0, 0), -1)
                if reference_center is None:
                    stable_counter += 1
                    cv2.putText(img, f"Stabilizing... {stable_counter}/{stability_required_frames}",
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    if stable_counter >= stability_required_frames:
                        reference_center = current_center
                        print(f"[Stabilized] Eye center recorded at {reference_center}")
                else:
                    dx = abs(current_center[0] - reference_center[0])
                    dy = abs(current_center[1] - reference_center[1])
                    if dx > tolerance or dy > tolerance:
                        cv2.putText(img, "WARNING: Eye moved!", (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        print(f"[Error] Eye moved! Current: {current_center}, Reference: {reference_center}")
                    else:
                        cv2.putText(img, f"Eye Center: {current_center}", (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                stable_counter = 0
                if reference_center is None:
                    cv2.putText(img, "Waiting for stable eye detection...",
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                else:
                    cv2.putText(img, "WARNING: Eye not detected!",
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        except Exception as e:
            print(f"[Detection Error] {e}")

        cv2.imshow("ESP32 Eye Tracker", img)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            stopped = True
            break

    print("[Main] Detection loop stopped.")

if __name__ == "__main__":
    print("[System] Starting stream thread...")
    threading.Thread(target=capture_stream, daemon=True).start()

    # Wait until the first frame is available
    for _ in range(50):
        with lock:
            if frame is not None:
                break
        time.sleep(0.1)
    else:
        print("[Startup Error] No frames received. Exiting.")
        stopped = True
        exit(1)

    detection_loop()
    cv2.destroyAllWindows()
    print("[System] Shutdown complete.")
