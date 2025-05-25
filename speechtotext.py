from flask import Flask, render_template_string, Response
import cv2
import threading
import time
import os
import numpy as np
from datetime import datetime

app = Flask(__name__)

# Initialize video capture
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Shared resources
frame_lock = threading.Lock()
latest_frame = None
green_contours = []
last_detection_time = 0
screenshot_taken = False
screenshot_cooldown = 2.0  # Seconds between screenshots

# Ensure snapshots directory exists
os.makedirs("snapshots", exist_ok=True)

# Green color range in HSV
# These values may need adjustment based on lighting conditions and exact shade of green
lower_green = np.array([35, 100, 100])
upper_green = np.array([85, 255, 255])

def capture_frames():
    """Thread for capturing frames from camera"""
    global latest_frame
    
    while True:
        success, frame = camera.read()
        if success:
            with frame_lock:
                latest_frame = frame.copy()
        
        time.sleep(0.01)  # Small delay to prevent CPU overuse

def process_frames():
    """Thread for processing frames and detecting green objects"""
    global latest_frame, green_contours, last_detection_time, screenshot_taken
    
    while True:
        # Get the latest frame
        current_frame = None
        with frame_lock:
            if latest_frame is not None:
                current_frame = latest_frame.copy()
        
        if current_frame is None:
            time.sleep(0.01)
            continue
        
        try:
            # Convert to HSV color space for better color detection
            hsv_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2HSV)
            
            # Create a mask for green color
            green_mask = cv2.inRange(hsv_frame, lower_green, upper_green)
            
            # Apply morphological operations to remove noise
            kernel = np.ones((5, 5), np.uint8)
            green_mask = cv2.erode(green_mask, kernel, iterations=1)
            green_mask = cv2.dilate(green_mask, kernel, iterations=2)
            
            # Find contours in the mask
            contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by size to remove small noise
            significant_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # Minimum area threshold
                    significant_contours.append(contour)
            
            # Update global contours
            green_contours = significant_contours
            
            # Take screenshot if green objects are detected and cooldown has passed
            current_time = time.time()
            if significant_contours and (current_time - last_detection_time > screenshot_cooldown):
                # Create annotated frame
                annotated_frame = draw_boxes(current_frame.copy(), significant_contours)
                
                # Save screenshot
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"snapshots/green_detected_{timestamp}.jpg"
                cv2.imwrite(filename, annotated_frame)
                
                print(f"Screenshot saved: {filename}")
                last_detection_time = current_time
                
        except Exception as e:
            print(f"Error during processing: {str(e)}")
        
        # Sleep to reduce CPU usage
        time.sleep(0.03)

def draw_boxes(frame, contours):
    """Draw bounding boxes around detected green objects"""
    result = frame.copy()
    
    for i, contour in enumerate(contours):
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)
        
        # Draw rectangle
        cv2.rectangle(result, (x, y), (x+w, y+h), (0, 255, 0), 3)
        
        # Add label
        label = f"Green Object {i+1}"
        cv2.putText(
            result,
            label,
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )
        
        # Draw contour for better visualization
        cv2.drawContours(result, [contour], -1, (0, 255, 0), 2)
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(
        result,
        timestamp,
        (10, result.shape[0] - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1
    )
    
    return result

def generate_frames():
    """Generate frames for video streaming"""
    global latest_frame, green_contours
    
    while True:
        frame_to_send = None
        
        # Get the latest frame
        with frame_lock:
            if latest_frame is not None:
                frame_to_send = latest_frame.copy()
        
        if frame_to_send is None:
            time.sleep(0.01)
            continue
        
        # Draw bounding boxes if green objects are detected
        if green_contours:
            frame_to_send = draw_boxes(frame_to_send, green_contours)
            
            # Add indicator that green is detected
            cv2.putText(
                frame_to_send,
                "GREEN DETECTED",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
        
        # Encode with moderate compression
        _, buffer = cv2.imencode('.jpg', frame_to_send, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Control streaming rate
        time.sleep(0.03)

# HTML template
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Green Object Detection</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin: 20px;
            background-color: #f0f0f0;
        }
        h1 {
            color: #2e8b57;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .video-container {
            margin: 20px auto;
        }
        #video {
            max-width: 100%;
            border: 2px solid #2e8b57;
            border-radius: 5px;
        }
        .info {
            background-color: #e8f5e9;
            padding: 10px;
            border-radius: 5px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Green Object Detection</h1>
        <div class="video-container">
            <img id="video" src="{{ url_for('video_feed') }}">
        </div>
        <div class="info">
            <p>Hold up a green object to be detected. Screenshots are automatically saved when green objects are detected.</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # Start background threads
    threading.Thread(target=capture_frames, daemon=True).start()
    threading.Thread(target=process_frames, daemon=True).start()
    
    print("Starting green detection server. Access at http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, threaded=True)