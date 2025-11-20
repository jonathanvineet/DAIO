import cv2

print("Scanning for cameras...")

available = []

# Try indices 0–10
for i in range(11):
    cap = cv2.VideoCapture(i, cv2.CAP_AVFOUNDATION)
    if cap is not None and cap.isOpened():
        available.append(i)
        cap.release()

print("\nAvailable camera indices:")
print(available if available else "None found")
