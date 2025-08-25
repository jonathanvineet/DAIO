import cv2
import torch
import threading
import time
import os
import sys

# Add yolov5 directory to path if needed
sys.path.append(os.path.join(os.path.dirname(__file__), 'yolov5'))

# IP camera stream URL - Update this to your camera's URL
STREAM_URL = "http://192.168.1.19/stream"
MODEL_PATH = "/Users/vine/elco/DAIO/yolov5s.pt"
INFERENCE_SIZE = 320

# Set environment variable to disable safety checks for loading YOLOv5 models
os.environ['TORCH_DISABLE_UNSAFE_SERIALIZATION'] = '1'

# Global variables
frame = None
lock = threading.Lock()
stopped = False
fps = 0
frame_count = 0
last_fps_update = time.time()

print("Setting up YOLOv5 model...")

try:
    # Import directly from yolov5 repo to avoid the helper class issues
    from yolov5.models.experimental import attempt_load
    from yolov5.utils.general import non_max_suppression, scale_boxes
    from yolov5.utils.plots import Annotator, colors
    from yolov5.utils.torch_utils import select_device
    
    # Select device (CPU in this case)
    device = select_device('cpu')
    
    # Load model with weights_only=False to avoid serialization issues
    model = torch.load(MODEL_PATH, map_location=device, weights_only=False)
    
    # Extract model from the checkpoint dictionary
    if isinstance(model, dict) and 'model' in model:
        model = model['model']
    
    model = model.float().to(device)  # Convert to FP32
    model.eval()  # Set to evaluation mode
    
    print("Model loaded successfully!")

except Exception as e:
    print(f"Error loading model: {str(e)}")
    raise

def capture_stream():
    global frame, stopped
    print(f"Connecting to stream at {STREAM_URL}...")
    cap = cv2.VideoCapture(STREAM_URL)
    
    # Set buffer size to 1 to minimize latency
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    if not cap.isOpened():
        print(f"Error: Could not open stream at {STREAM_URL}")
        stopped = True
        return
    
    print(f"Stream connected successfully")
    
    # Capture loop
    while not stopped:
        ret, img = cap.read()
        if not ret:
            print("Error reading frame, attempting to reconnect...")
            cap.release()
            time.sleep(1)
            cap = cv2.VideoCapture(STREAM_URL)
            continue
        
        with lock:
            frame = img

def detection_loop():
    global frame, stopped, fps, frame_count, last_fps_update
    
    while not stopped:
        # Check if we have a frame
        with lock:
            if frame is None:
                time.sleep(0.01)  # Short sleep if no frame
                continue
            img = frame.copy()
        
        # Prepare image for model
        img_tensor = prepare_image(img, INFERENCE_SIZE)
        
        # Inference
        with torch.no_grad():
            pred = model(img_tensor)[0]
        
        # Apply NMS
        detections = non_max_suppression(pred, conf_thres=0.25, iou_thres=0.45)
        
        # Process detections
        annotated_img = process_detections(img, detections, img_tensor.shape)
        
        # Update FPS calculation
        frame_count += 1
        current_time = time.time()
        if current_time - last_fps_update >= 1.0:
            fps = frame_count / (current_time - last_fps_update)
            frame_count = 0
            last_fps_update = current_time
        
        # Add FPS to the image
        cv2.putText(annotated_img, f"FPS: {fps:.1f}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Show the result
        cv2.imshow("ESP32 YOLO Detection", annotated_img)
        
        # Exit if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stopped = True
            break

def prepare_image(img, size):
    """Prepare image for the model"""
    # Resize
    img_resized = cv2.resize(img, (size, size))
    
    # Convert BGR to RGB and HWC to CHW format
    img_rgb = img_resized[:, :, ::-1].transpose(2, 0, 1)
    img_tensor = torch.from_numpy(img_rgb).to(device)
    
    # Normalize
    img_tensor = img_tensor.float() / 255.0
    
    # Add batch dimension if needed
    if img_tensor.ndimension() == 3:
        img_tensor = img_tensor.unsqueeze(0)
    
    return img_tensor

def process_detections(img, detections, input_shape):
    """Process and visualize detections"""
    img_copy = img.copy()
    
    # Create annotator
    annotator = Annotator(img_copy, line_width=2)
    
    for i, det in enumerate(detections):
        if len(det):
            # Rescale boxes from model size to original image size
            det[:, :4] = scale_boxes(input_shape[2:], det[:, :4], img_copy.shape).round()
            
            # Draw bounding boxes and labels
            for *xyxy, conf, cls in det:
                c = int(cls)  # class
                label = f"Object {conf:.2f}"
                
                # Get integer coordinates
                x1, y1, x2, y2 = map(int, xyxy)
                
                # Calculate center
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                # Draw box
                annotator.box_label(xyxy, label, color=colors(c, True))
                
                # Draw center point
                cv2.circle(img_copy, (center_x, center_y), 5, (0, 0, 255), -1)
                
                # Add center coordinates
                cv2.putText(img_copy, f"({center_x},{center_y})", (x1, y2+20), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    
    return img_copy

if __name__ == "__main__":
    print("Starting camera detection system...")
    
    try:
        # Start camera thread
        capture_thread = threading.Thread(target=capture_stream, daemon=True)
        capture_thread.start()
        
        # Wait briefly for camera to initialize
        time.sleep(1)
        
        # Run detection loop on main thread
        detection_loop()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        stopped = True
        print("Shutting down...")
        cv2.destroyAllWindows()
