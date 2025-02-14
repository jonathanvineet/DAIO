import cv2
from inference import InferencePipeline

def my_sink(result, video_frame):
    if result.get("output_image"):  # Display an image from the workflow response
        cv2.imshow("Workflow Image", result["output_image"].numpy_image)
        cv2.waitKey(1)
    print(result)  # Handle predictions of each frame

# Initialize the pipeline
pipeline = InferencePipeline.init_with_workflow(
    api_key="VOq8sJmvFwsiBItcJJmR",
    workspace_name="personal-dj7nt",
    workflow_id="detect-count-and-visualize",
    max_fps=30,
    on_prediction=my_sink
)

# Use OpenCV with DirectShow backend to capture frames
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("Error: Unable to access the camera.")
else:
    print("Camera accessed successfully. Starting pipeline...")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame.")
            break

        # Process the frame with the pipeline
        pipeline.infer(frame)

        # Display the frame (optional, for debugging purposes)
        cv2.imshow("Raw Frame", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
            break

cap.release()
cv2.destroyAllWindows()
