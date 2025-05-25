import cv2
import numpy as np
import threading
import requests
import time
import gc
from collections import deque
from roboflow import Roboflow

class RealTimeESP32Stream:
    def __init__(self, url, model):
        self.url = url
        self.model = model
        
        # CRITICAL: Use thread-safe locks and minimal buffering
        self.current_raw_frame = None
        self.current_processed_frame = None
        self.frame_lock = threading.Lock()
        self.process_lock = threading.Lock()
        
        self.running = True
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.display_fps = 0
        
        # High-frequency processing for low latency
        self.last_process_time = 0
        self.process_interval = 0.05  # Process every 50ms (20 FPS)
        
        # Performance monitoring
        self.frame_count = 0
        self.processed_count = 0
        self.session_start_time = time.time()
        self.last_performance_print = time.time()
        
        # Skip frame strategy for real-time performance
        self.frame_skip_counter = 0
        self.process_every_nth_frame = 2  # Process every 2nd frame for AI
        
    def grab_frames(self):
        """Ultra-fast frame grabber with minimal latency"""
        print("Starting real-time frame grabber...")
        
        while self.running:
            session_start = time.time()
            connection_frame_count = 0
            
            try:
                # Streamlined connection with minimal overhead
                with requests.get(self.url, stream=True, timeout=3, 
                                headers={'Connection': 'close'}) as response:
                    
                    # Ultra-small buffer for minimum latency
                    buffer = bytearray()
                    
                    for chunk in response.iter_content(chunk_size=512):  # Very small chunks
                        if not self.running:
                            break
                        
                        buffer.extend(chunk)
                        
                        # AGGRESSIVE: Keep buffer under 16KB
                        if len(buffer) > 16384:
                            # Find last JPEG start and discard everything before it
                            last_start = buffer.rfind(b'\xff\xd8')
                            if last_start > 0:
                                buffer = buffer[last_start:]
                            else:
                                buffer = buffer[-4096:]  # Keep only last 4KB
                        
                        # Extract frames with minimal processing
                        while True:
                            start = buffer.find(b'\xff\xd8')
                            if start == -1:
                                break
                            
                            end = buffer.find(b'\xff\xd9', start + 2)
                            if end == -1:
                                if start > 0:
                                    buffer = buffer[start:]
                                break
                            
                            # Extract JPEG
                            jpeg_bytes = buffer[start:end + 2]
                            buffer = buffer[end + 2:]
                            
                            # Quick validation
                            if 2000 < len(jpeg_bytes) < 51200:  # 2KB-50KB range
                                try:
                                    # CRITICAL: Fast decode without copies
                                    frame = cv2.imdecode(
                                        np.frombuffer(jpeg_bytes, dtype=np.uint8), 
                                        cv2.IMREAD_COLOR
                                    )
                                    
                                    if frame is not None and frame.size > 0:
                                        # ATOMIC UPDATE: Replace current frame immediately
                                        with self.frame_lock:
                                            self.current_raw_frame = frame
                                        
                                        connection_frame_count += 1
                                        self.frame_count += 1
                                        
                                        # Minimal logging
                                        if connection_frame_count % 100 == 0:
                                            elapsed = time.time() - session_start
                                            fps = connection_frame_count / elapsed
                                            print(f"Grab: {connection_frame_count} frames @ {fps:.1f} FPS")
                                
                                except:
                                    continue  # Skip bad frames silently
                        
                        # Quick reconnect for freshness
                        if time.time() - session_start > 10:  # Reconnect every 10s
                            break
                            
            except Exception as e:
                print(f"Grab error: {e}")
                time.sleep(0.1)
    
    def process_frames(self):
        """High-speed frame processor with smart skipping"""
        print("Starting real-time processor...")
        
        last_processed_frame_id = -1
        
        while self.running:
            current_time = time.time()
            
            # High frequency checking
            if current_time - self.last_process_time > self.process_interval:
                
                # Get current frame atomically
                with self.frame_lock:
                    current_frame = self.current_raw_frame
                
                if current_frame is not None and id(current_frame) != last_processed_frame_id:
                    try:
                        process_start = time.time()
                        
                        # SMART SKIPPING: Only process every Nth frame for AI
                        self.frame_skip_counter += 1
                        
                        if self.frame_skip_counter >= self.process_every_nth_frame:
                            self.frame_skip_counter = 0
                            
                            # Ultra-fast resize - smaller for speed
                            small = cv2.resize(current_frame, (256, 192), 
                                             interpolation=cv2.INTER_NEAREST)  # Fastest interpolation
                            
                            # Run inference
                            result = self.model.predict(small, confidence=45, overlap=25).json()
                            
                            # Scale factors
                            scale_x = current_frame.shape[1] / 256
                            scale_y = current_frame.shape[0] / 192
                            
                            # Draw on original frame
                            processed = current_frame.copy()
                            
                            for pred in result['predictions']:
                                x1 = int((pred['x'] - pred['width']/2) * scale_x)
                                y1 = int((pred['y'] - pred['height']/2) * scale_y)
                                x2 = int((pred['x'] + pred['width']/2) * scale_x)
                                y2 = int((pred['y'] + pred['height']/2) * scale_y)
                                
                                cv2.rectangle(processed, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                cv2.putText(processed, f"{pred['confidence']:.0f}%", 
                                          (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                            
                            # Atomic update
                            with self.process_lock:
                                self.current_processed_frame = processed
                            
                            self.processed_count += 1
                            
                            process_time = time.time() - process_start
                            if self.processed_count % 20 == 0:
                                print(f"Process: {process_time:.3f}s avg, {self.processed_count} processed")
                        
                        else:
                            # For skipped frames, just copy raw frame
                            with self.process_lock:
                                self.current_processed_frame = current_frame.copy()
                        
                        last_processed_frame_id = id(current_frame)
                        self.last_process_time = current_time
                        
                    except Exception as e:
                        print(f"Process error: {e}")
            
            time.sleep(0.005)  # Very short sleep - 5ms
    
    def get_display_frame(self):
        """Get the most current frame for display"""
        # Prefer processed frames, but fall back to raw for minimum latency
        with self.process_lock:
            if self.current_processed_frame is not None:
                return self.current_processed_frame
        
        with self.frame_lock:
            return self.current_raw_frame
    
    def calculate_fps(self):
        """Calculate display FPS"""
        self.fps_counter += 1
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.display_fps = self.fps_counter / (current_time - self.last_fps_time)
            self.fps_counter = 0
            self.last_fps_time = current_time
    
    def display_loop(self):
        """Ultra-responsive display loop"""
        print("Starting real-time display...")
        
        # Start worker threads with higher priority
        grabber_thread = threading.Thread(target=self.grab_frames, daemon=True)
        processor_thread = threading.Thread(target=self.process_frames, daemon=True)
        
        grabber_thread.start()
        processor_thread.start()
        
        # Minimal startup delay
        time.sleep(0.5)
        
        last_frame_time = time.time()
        
        while self.running:
            frame_start = time.time()
            
            frame = self.get_display_frame()
            
            if frame is not None:
                # Minimize display processing
                display_frame = frame  # Use frame directly when possible
                
                # Lightweight status overlay
                current_time = time.time()
                total_elapsed = current_time - self.session_start_time
                grab_fps = self.frame_count / total_elapsed if total_elapsed > 0 else 0
                
                # Simple status text
                cv2.putText(display_frame, f"FPS: {self.display_fps:.0f}", 
                          (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.putText(display_frame, f"Grab: {grab_fps:.0f}", 
                          (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                
                # Show latency info
                frame_age = current_time - last_frame_time
                cv2.putText(display_frame, f"Lag: {frame_age*1000:.0f}ms", 
                          (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                
                cv2.imshow("ESP32 Real-Time Stream", display_frame)
                self.calculate_fps()
                
                last_frame_time = current_time
                
                # Performance reporting
                if current_time - self.last_performance_print > 3.0:
                    print(f"REALTIME: Display={self.display_fps:.1f} FPS, "
                          f"Grab={grab_fps:.1f} FPS, "
                          f"Processed={self.processed_count}, "
                          f"Lag={frame_age*1000:.0f}ms")
                    self.last_performance_print = current_time
            
            # Check for quit
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('+'):
                self.process_every_nth_frame = max(1, self.process_every_nth_frame - 1)
                print(f"AI processing every {self.process_every_nth_frame} frames")
            elif key == ord('-'):
                self.process_every_nth_frame = min(5, self.process_every_nth_frame + 1)
                print(f"AI processing every {self.process_every_nth_frame} frames")
            
            # Target 60 FPS display
            frame_time = time.time() - frame_start
            target_frame_time = 1.0 / 60.0
            if frame_time < target_frame_time:
                time.sleep(target_frame_time - frame_time)
        
        self.running = False
        cv2.destroyAllWindows()

def main():
    print("Initializing Roboflow...")
    rf = Roboflow(api_key="VOq8sJmvFwsiBItcJJmR")
    model = rf.workspace().project("eye-xp87l").version(1).model
    
    print("Starting REAL-TIME ESP32-CAM stream...")
    print("Controls:")
    print("  'q' - quit")
    print("  '+' - process more frames with AI (higher CPU)")
    print("  '-' - process fewer frames with AI (lower CPU)")
    print("\nThis version prioritizes REAL-TIME display over AI processing!")
    
    stream = RealTimeESP32Stream("http://192.168.1.19/stream", model)
    
    try:
        stream.display_loop()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        stream.running = False
        print("Cleanup complete.")

if __name__ == "__main__":
    main()