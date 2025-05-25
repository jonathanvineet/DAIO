import cv2
import numpy as np
import requests
from io import BytesIO
from PIL import Image
import threading

class ESP32_CAM_Stream:
    def __init__(self, ip_address="192.168.1.19"):
        self.frame = None
        self.stopped = False
        self.stream = None
        self.url = f"http://{ip_address}/stream"
        
    def start(self):
        threading.Thread(target=self.update, args=()).start()
        return self
    
    def update(self):
        try:
            print(f"Connecting to stream at {self.url}")
            self.stream = requests.get(self.url, stream=True, timeout=5)
            bytes_data = bytes()
            
            for chunk in self.stream.iter_content(chunk_size=1024):
                bytes_data += chunk
                a = bytes_data.find(b'\xff\xd8')  # JPEG start
                b = bytes_data.find(b'\xff\xd9')  # JPEG end
                
                if a != -1 and b != -1:
                    jpg = bytes_data[a:b+2]
                    bytes_data = bytes_data[b+2:]
                    try:
                        self.frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    except Exception as e:
                        print(f"Frame decode error: {e}")
                        continue
                
                if self.stopped:
                    self.stream.close()
                    break
                    
        except Exception as e:
            print(f"Stream error: {e}")
            self.stop()
    
    def read(self):
        return self.frame
    
    def stop(self):
        self.stopped = True
        if self.stream:
            self.stream.close()

def main():
    # Replace with your ESP32-CAM's IP
    esp_ip = "192.168.1.19"
    
    print(f"Starting ESP32-CAM stream from {esp_ip}")
    stream = ESP32_CAM_Stream(esp_ip).start()
    
    try:
        while True:
            frame = stream.read()
            
            if frame is not None:
                cv2.imshow('ESP32-CAM Stream', frame)
            
            # Press 'q' to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        stream.stop()
        cv2.destroyAllWindows()
        print("Stream stopped")

if __name__ == "__main__":
    main()