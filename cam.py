import cv2
import numpy as np
import threading
import requests
import time
from collections import deque
from roboflow import Roboflow

class SmoothESP32Stream:
    def __init__(self, url, model):
        self.url = url
        self.model = model
        
        # Use deques instead of queues for better performance
        self.raw_frames = deque(maxsize=2)  # Only keep 2 raw frames
        self.processed_frames = deque(maxsize=2)  # Only keep 2 processed frames
        
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        self.running = True
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.display_fps = 0
        
        # Processing control
        self.last_process_time = 0
        self.process_interval = 0.1  # Process every 100ms (10 FPS)
        
    def grab_frames(self):
        """Continuously grab frames from ESP32-CAM"""
        print("Starting frame grabber...")
        try:
            stream = requests.get(self.url, stream=True, timeout=5)
            bytes_data = b""
            frame_count = 0
            
            for chunk in stream.iter_content(chunk_size=8192):  # Larger chunks
                if not self.running:
                    break
                    
                bytes_data += chunk
                
                # Limit buffer size
                if len(bytes_data) > 1024 * 512:  # 512KB limit
                    bytes_data = bytes_data[-1024 * 256:]  # Keep last 256KB
                
                # Find complete JPEG frames
                while True:
                    start = bytes_data.find(b'\xff\xd8')
                    if start == -1:
                        break
                        
                    end = bytes_data.find(b'\xff\xd9', start)
                    if end == -1:
                        bytes_data = bytes_data[start:]
                        break
                    
                    jpg = bytes_data[start:end+2]
                    bytes_data = bytes_data[end+2:]
                    
                    if len(jpg) < 1000:  # Skip tiny frames
                        continue
                        
                    try:
                        frame = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
                        if frame is not None:
                            # Always keep only the newest frame
                            if len(self.raw_frames) >= self.raw_frames.maxlen:
                                try:
                                    self.raw_frames.popleft()  # Remove oldest
                                except:
                                    pass
                            self.raw_frames.append(frame)
                            frame_count += 1
                            
                            if frame_count % 100 == 0:
                                print(f"Grabbed {frame_count} frames")
                                
                    except Exception as e:
                        if frame_count % 50 == 0:
                            print(f"Decode error: {e}")
                        continue
                        
        except Exception as e:
            print(f"Stream error: {e}")
    
    def process_frames(self):
        """Process frames with AI inference at controlled rate"""
        print("Starting frame processor...")
        
        while self.running:
            current_time = time.time()
            
            # Check if we have raw frames and if it's time to process
            if (len(self.raw_frames) > 0 and 
                current_time - self.last_process_time > self.process_interval):
                
                try:
                    # Get the newest frame
                    frame = self.raw_frames[-1]  # Get newest frame
                    
                    # Resize for faster inference
                    small = cv2.resize(frame, (320, 240))  # Fixed smaller size
                    
                    # Run inference
                    result = self.model.predict(small, confidence=40, overlap=30).json()
                    
                    # Scale factors
                    scale_x = frame.shape[1] / small.shape[1]
                    scale_y = frame.shape[0] / small.shape[0]
                    
                    # Draw predictions on original frame
                    processed_frame = frame.copy()
                    for pred in result['predictions']:
                        x = int((pred['x'] - pred['width']/2) * scale_x)
                        y = int((pred['y'] - pred['height']/2) * scale_y)
                        w = int(pred['width'] * scale_x)
                        h = int(pred['height'] * scale_y)
                        
                        cv2.rectangle(processed_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.putText(processed_frame, f"Eye {pred['confidence']:.1f}", 
                                  (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    # Store processed frame
                    if len(self.processed_frames) >= self.processed_frames.maxlen:
                        try:
                            self.processed_frames.popleft()
                        except:
                            pass
                    self.processed_frames.append(processed_frame)
                    self.last_process_time = current_time
                    
                except Exception as e:
                    print(f"Processing error: {e}")
            
            time.sleep(0.01)  # Small sleep to prevent busy waiting
    
    def get_display_frame(self):
        """Get the best frame for display"""
        # Prefer processed frames, fall back to raw frames
        if len(self.processed_frames) > 0:
            return self.processed_frames[-1]  # Newest processed frame
        elif len(self.raw_frames) > 0:
            return self.raw_frames[-1]  # Newest raw frame
        return None
    
    def calculate_fps(self):
        """Calculate display FPS"""
        self.fps_counter += 1
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.display_fps = self.fps_counter / (current_time - self.last_fps_time)
            self.fps_counter = 0
            self.last_fps_time = current_time
    
    def display_loop(self):
        """Main display loop"""
        print("Starting display...")
        
        # Start worker threads
        grabber_thread = threading.Thread(target=self.grab_frames, daemon=True)
        processor_thread = threading.Thread(target=self.process_frames, daemon=True)
        
        grabber_thread.start()
        processor_thread.start()
        
        # Wait a moment for first frames
        time.sleep(1)
        
        while self.running:
            frame = self.get_display_frame()
            
            if frame is not None:
                # Add FPS counter
                display_frame = frame.copy()
                cv2.putText(display_frame, f"FPS: {self.display_fps:.1f}", 
                          (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, f"Raw: {len(self.raw_frames)} Proc: {len(self.processed_frames)}", 
                          (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                
                cv2.imshow("ESP32 Eye Detection", display_frame)
                self.calculate_fps()
            
            # Check for quit
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            
            # Small sleep for smooth display
            time.sleep(0.016)  # ~60 FPS max display rate
        
        self.running = False
        cv2.destroyAllWindows()

def main():
    print("Initializing Roboflow...")
    rf = Roboflow(api_key="VOq8sJmvFwsiBItcJJmR")
    model = rf.workspace().project("eye-xp87l").version(1).model
    
    print("Starting ESP32-CAM stream...")
    stream = SmoothESP32Stream("http://192.168.1.19/stream", model)
    
    try:
        stream.display_loop()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        stream.running = False
        print("Cleanup complete.")

if __name__ == "__main__":
    main()