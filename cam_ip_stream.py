import cv2
import torch
import threading
import numpy as np
import os
import sys

# Add YOLOv5 directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'yolov5'))

# Import YOLOv5 modules directly
from models.experimental import attempt_load
from utils.general import non_max_suppression, scale_boxes
from utils.torch_utils import select_device

# IP Camera stream URL
STREAM_URL = "http://172.20.10.2/stream"

# Initialize variables
frame = None
lock = threading.Lock()
stopped = False

def load_model():
    try:
        # Use CPU for inference
        device = select_device('cpu')
        
        # Load the model directly with attempt_load
        model = attempt_load('/Users/vine/elco/DAIO/yolov5m.pt', device=device)
        
        # Set model to evaluation mode
        model.eval()
        
        print("Model loaded successfully")
        return model, device
    except Exception as e:
        print(f"Error loading model: {e}")
        return None, None

def capture_stream():
    global frame, stopped
    print(f"Attempting to connect to stream at {STREAM_URL}")
    
    # Try to open the IP camera stream
    cap = cv2.VideoCapture(STREAM_URL)
    
    # Check if connection is successful
    if not cap.isOpened():
        print(f"Error: Could not open stream at {STREAM_URL}")
        stopped = True
        return
        
    print(f"Successfully connected to stream at {STREAM_URL}")
    
    # Stream capture loop
    while not stopped:
        ret, img = cap.read()
        if not ret:
            print("Failed to read frame from stream. Attempting to reconnect...")
            cap.release()
            cap = cv2.VideoCapture(STREAM_URL)
            continue
            
        with lock:
            frame = img

def detection_loop(model, device):
    global frame, stopped
    
    print("Waiting for first frame from stream...")
    # Wait for first frame
    while not stopped:
        with lock:
            if frame is not None:
                break
        if cv2.waitKey(100) == ord('q'):  # Check for quit every 100ms
            stopped = True
            return
    
    print("Starting detection loop...")
    
    while not stopped:
        with lock:
            if frame is None:
                continue
            img = frame.copy()

        # Process image for model
        img_size = 640  # inference size
        img_for_model = cv2.resize(img, (img_size, img_size))
        img_for_model = img_for_model[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, HWC to CHW
        img_for_model = np.ascontiguousarray(img_for_model)
        img_for_model = torch.from_numpy(img_for_model).to(device)
        img_for_model = img_for_model.float() / 255.0
        if img_for_model.ndimension() == 3:
            img_for_model = img_for_model.unsqueeze(0)
            
        # Inference
        with torch.no_grad():
            pred = model(img_for_model)[0]
        
        # Apply NMS (Non-Maximum Suppression)
        pred = non_max_suppression(pred, conf_thres=0.25, iou_thres=0.45)
        
        # Process detections
        img_display = img.copy()
        for i, det in enumerate(pred):  # detections per image
            if len(det):
                # Rescale boxes from img_size to original image size
                det[:, :4] = scale_boxes(img_for_model.shape[2:], det[:, :4], img_display.shape).round()
                
                # Draw detections
                for *xyxy, conf, cls in det:
                    if conf > 0.5:  # confidence threshold
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
                        
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
        
        # Display results
        cv2.imshow('ESP32 Camera YOLO Eye Detection', img_display)
        if cv2.waitKey(1) == ord('q'):
            stopped = True

if __name__ == '__main__':
    # Load the YOLO model
    model, device = load_model()
    
    if model is None:
        print("Failed to load model. Exiting...")
        sys.exit(1)
    
    try:
        # Start stream capture thread
        capture_thread = threading.Thread(target=capture_stream)
        capture_thread.daemon = True
        capture_thread.start()
        
        # Run detection loop in main thread
        detection_loop(model, device)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        stopped = True
        print("Shutting down...")
        cv2.destroyAllWindows()
