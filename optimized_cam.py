import cv2
from yolov5 import YOLOv5
import threading
import time
import numpy as np

# Configuration
STREAM_URL = "http://192.168.1.19/stream"  # Your IP camera stream URL
MODEL_PATH = "/Users/vine/elco/DAIO/yolov5s.pt"
INFERENCE_SIZE = 320  # Smaller size for faster inference
CONF_THRESHOLD = 0.35  # Lower threshold to detect more objects
SKIP_FRAMES = 1  # Skip every other frame for speed

# Performance monitoring
frame_times = []
processing_times = []

# Load model once
print(f"Loading model from {MODEL_PATH}...")
try:
    model = YOLOv5(MODEL_PATH, device="cpu")
    print("Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {e}")
    raise

# Global variables
frame = None
lock = threading.Lock()
stopped = False
frame_count = 0

def capture_stream():
    global frame, stopped
    print(f"Connecting to stream at {STREAM_URL}...")
    cap = cv2.VideoCapture(STREAM_URL)
    
    # Try to improve camera buffer settings
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer size
    
    if not cap.isOpened():
        print(f"Error: Could not open stream at {STREAM_URL}")
        stopped = True
        return
    
    print("Stream connected successfully")
    
    while not stopped:
        ret, img = cap.read()
        if not ret:
            print("Error reading frame, attempting to reconnect...")
            cap.release()
            time.sleep(1)
            cap = cv2.VideoCapture(STREAM_URL)
            continue
        
        # Resize frame to reduce processing load (optional)
        # img = cv2.resize(img, (640, 480))
        
        with lock:
            frame = img

def detection_loop():
    global frame, stopped, frame_count
    last_fps_update = time.time()
    fps = 0
    frames_processed = 0
    
    while not stopped:
        start_time = time.time()
        
        # Skip frames if needed
        if frame_count % (SKIP_FRAMES + 1) != 0:
            frame_count += 1
            time.sleep(0.01)  # Small sleep to prevent CPU overload
            continue
        
        with lock:
            if frame is None:
                continue
            img = frame.copy()
        
        frame_count += 1
        
        # Fast prediction with smaller size for speed
        process_start = time.time()
        results = model.predict(img, size=INFERENCE_SIZE, conf=CONF_THRESHOLD)
        process_time = time.time() - process_start
        processing_times.append(process_time)
        
        # Get the rendered image (automatically draws boxes)
        img_result = results.render()[0]
        
        # Calculate and display FPS
        frames_processed += 1
        if time.time() - last_fps_update >= 1.0:  # Update FPS every second
            fps = frames_processed / (time.time() - last_fps_update)
            frames_processed = 0
            last_fps_update = time.time()
        
        # Add FPS display
        cv2.putText(img_result, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (0, 255, 0), 2, cv2.LINE_AA)
        
        # Show the image
        cv2.imshow("ESP32 YOLO Detection", img_result)
        
        # Calculate frame time
        frame_time = time.time() - start_time
        frame_times.append(frame_time)
        
        # Break on 'q' key
        if cv2.waitKey(1) & 0xFF == ord("q"):
            stopped = True
            break

def print_performance_stats():
    if frame_times:
        avg_frame_time = sum(frame_times) / len(frame_times)
        avg_fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
        avg_processing = sum(processing_times) / len(processing_times) if processing_times else 0
        
        print(f"\nPerformance Statistics:")
        print(f"Average FPS: {avg_fps:.2f}")
        print(f"Average frame processing time: {avg_frame_time*1000:.2f} ms")
        print(f"Average model inference time: {avg_processing*1000:.2f} ms")
        print(f"Frames processed: {len(frame_times)}")

if __name__ == "__main__":
    print("Starting optimized YOLO detection...")
    
    # Start capture thread
    capture_thread = threading.Thread(target=capture_stream, daemon=True)
    capture_thread.start()
    
    try:
        # Wait a bit for the first frame
        time.sleep(1)
        
        # Run detection in the main thread
        detection_loop()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error during execution: {e}")
    finally:
        stopped = True
        print_performance_stats()
        print("Shutting down...")
        cv2.destroyAllWindows()
