import cv2
import torch
import threading
import numpy as np
import os
import sys

# Add YOLOv5 directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'yolov5'))

# Import YOLOv5 modules directly
from models.yolo import Model
from models.experimental import attempt_load
from utils.general import non_max_suppression, scale_boxes
from utils.torch_utils import select_device

# Load model with weights_only=False (to avoid serialization security issues)
device = select_device('cpu')
model_path = '/Users/vine/elco/DAIO/yolov5s.pt'
model = torch.load(model_path, map_location=device, weights_only=False)
model = model['model'].float().eval()  # extract model from checkpoint

frame = None
lock = threading.Lock()
stopped = False

def capture_stream():
    global frame, stopped
    # Try to use the default camera (0) instead of IP camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera. Trying camera 1...")
        cap = cv2.VideoCapture(1)  # Try camera 1 if camera 0 fails
    
    if not cap.isOpened():
        print("Error: Could not open any camera. Exiting...")
        stopped = True
        return
        
    print("Camera opened successfully!")
    while not stopped:
        ret, img = cap.read()
        if not ret:
            print("Error reading frame")
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

        # Process image for model
        img_for_model = cv2.resize(img, (640, 640))
        img_for_model = img_for_model[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, HWC to CHW
        img_for_model = np.ascontiguousarray(img_for_model)
        img_for_model = torch.from_numpy(img_for_model).to(device)
        img_for_model = img_for_model.float() / 255.0
        if img_for_model.ndimension() == 3:
            img_for_model = img_for_model.unsqueeze(0)
            
        # Inference
        with torch.no_grad():
            pred = model(img_for_model)[0]
        
        # Apply NMS
        pred = non_max_suppression(pred, 0.25, 0.45)
        
        # Process detections
        img_display = img.copy()
        for i, det in enumerate(pred):  # detections per image
            if len(det):
                # Rescale boxes from img_size to im0 size
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
        
        # Display results
        cv2.imshow('YOLOv5 Object Detection', img_display)
        if cv2.waitKey(1) == ord('q'):
            stopped = True

if __name__ == '__main__':
    # Start capture thread
    capture_thread = threading.Thread(target=capture_stream)
    capture_thread.daemon = True
    capture_thread.start()
    
    # Start detection thread
    detection_thread = threading.Thread(target=detection_loop)
    detection_thread.daemon = True
    detection_thread.start()
    
    try:
        while not stopped:
            # Keep the main thread alive
            if cv2.waitKey(1) == ord('q'):
                stopped = True
    except KeyboardInterrupt:
        stopped = True
    finally:
        cv2.destroyAllWindows()
