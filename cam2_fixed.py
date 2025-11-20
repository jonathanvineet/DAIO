import cv2
import torch
import threading
import numpy as np
import os
import sys
import time

# Add YOLOv5 directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'yolov5'))

from utils.general import non_max_suppression, scale_boxes
from utils.torch_utils import select_device

# Load YOLO model
device = select_device("cpu")
ckpt = torch.load("/Users/vine/elco/DAIO/yolov5m.pt", map_location=device, weights_only=False)
model = ckpt["model"].float().eval()

# SHARED VARIABLES
frame = None
display_frame = None
lock = threading.Lock()
stopped = False

def open_webcam():
    cap = cv2.VideoCapture(0)
    # Try alternate backend on macOS if default fails
    if not cap.isOpened():
        cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)

    if cap.isOpened():
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
        return cap

    return None

def capture_thread_fn():
    global frame, stopped
    cap = open_webcam()
    if cap is None:
        print("No webcam found")
        stopped = True
        return

    print("Using webcam index 0")
    while not stopped:
        ret, img = cap.read()
        if ret:
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            with lock:
                frame = img
        time.sleep(0.005)

    cap.release()

def detection_thread_fn():
    global frame, display_frame, stopped

    while not stopped:
        with lock:
            if frame is None:
                time.sleep(0.01)
                continue
            img = frame.copy()

        # format for YOLO
        inp = cv2.resize(img, (640, 640))
        inp = inp[:, :, ::-1].transpose(2, 0, 1)
        inp = np.ascontiguousarray(inp)
        inp = torch.from_numpy(inp).float().to(device) / 255
        inp = inp.unsqueeze(0)

        with torch.no_grad():
            pred = model(inp)[0]

        pred = non_max_suppression(pred, 0.25, 0.45)

        out = img.copy()
        for det in pred:
            if len(det):
                det[:, :4] = scale_boxes(inp.shape[2:], det[:, :4], out.shape).round()

                for *xyxy, conf, cls in det:
                    if conf > 0.5:
                        x1, y1, x2, y2 = map(int, xyxy)
                        cv2.rectangle(out, (x1, y1), (x2, y2), (0,255,0), 2)

        with lock:
            display_frame = out

        time.sleep(0.001)


if __name__ == "__main__":

    # Start threads
    threading.Thread(target=capture_thread_fn, daemon=True).start()
    threading.Thread(target=detection_thread_fn, daemon=True).start()

    # MAIN THREAD = GUI ONLY
    cv2.namedWindow("YOLOv5", cv2.WINDOW_NORMAL)

    while not stopped:
        with lock:
            show = None if display_frame is None else display_frame.copy()

        if show is not None:
            cv2.imshow("YOLOv5", show)

        key = cv2.waitKey(1)
        if key == ord("q"):
            stopped = True
            break

    cv2.destroyAllWindows()
