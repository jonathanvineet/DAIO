from inference import InferencePipeline
import cv2
import numpy as np
import time

# Define screen size and center
screen_width = 640
screen_height = 480
screen_center = (screen_width // 2, screen_height // 2)

# Initialize variables
dynamic_center = (0, 0)  # Starting position of the light (marker)
threshold = 5  # Threshold for detecting if eyes moved (adjust as needed)
eyes_centered = False  # Flag for eye center status
calibrated_center = None  # To store the calibrated (recorded) center of the eyes
error_triggered = False  # Flag to check if error has been triggered

# Function to check if the eyes are centered relative to the recorded center
def check_if_eyes_centered(eye_centers):
    global eyes_centered, calibrated_center, error_triggered

    if calibrated_center is None:
        return  # No calibrated center yet, no need to check

    # Calculate the average distance between both eye centers and the calibrated center
    avg_eye_center = np.mean(eye_centers, axis=0)
    distance = np.sqrt((avg_eye_center[0] - calibrated_center[0])**2 + (avg_eye_center[1] - calibrated_center[1])**2)
    
    # If the eyes move away from the defined center
    if eyes_centered and distance > threshold and not error_triggered:
        print("Error: Eyes moved from the center!")
        error_triggered = True  # Trigger error only once

# Function to move the light (marker) across the screen to the target center
def move_center():
    global dynamic_center

    # Define a simple movement strategy: move from initial position to the target center
    x1, y1 = dynamic_center
    x2, y2 = screen_center  # Target center position

    # Gradually move the light to the target center
    if x1 < x2:
        x1 += 2  # Move right
    elif x1 > x2:
        x1 -= 2  # Move left

    if y1 < y2:
        y1 += 2  # Move down
    elif y1 > y2:
        y1 -= 2  # Move up

    dynamic_center = (x1, y1)

    return dynamic_center

# Function to handle the detected eyes and draw a light in the center
def my_sink(result, video_frame):
    global dynamic_center, eyes_centered, calibrated_center

    if result.get("output_image"):
        # Convert WorkflowImageData to a numpy image for drawing
        image = result["output_image"].numpy_image

        # Move the dynamic light to the center position
        dynamic_center = move_center()

        # Initialize a list to store the centers of detected eyes
        eye_centers = []

        # Check if there are predictions (i.e., eyes detected)
        if "predictions" in result and result["predictions"] is not None:
            detections = result["predictions"].xyxy  # Extract coordinates of the bounding box
            class_names = result["predictions"].data.get("class_name")  # Get class names
            
            for i, detection in enumerate(detections):
                x1, y1, x2, y2 = map(int, detection)  # Convert to integers
                # Calculate the center of the eye
                eye_center = ((x1 + x2) / 2, (y1 + y2) / 2)
                
                # Print debug information for eye location
                print(f"Eye {i + 1} location: {eye_center}")
                
                # Add the detected eye center to the list
                eye_centers.append(eye_center)
                
                # Draw a circle at the eye center
                cv2.circle(image, (int(eye_center[0]), int(eye_center[1])), 5, (0, 0, 255), -1)

        # If the light is at the center and both eyes are detected, calibrate
        if not eyes_centered and dynamic_center == screen_center and len(eye_centers) >= 2:
            # Calculate the average center of both eyes
            calibrated_center = np.mean(eye_centers, axis=0)
            print(f"Calibrated center of the eyes: {calibrated_center}")
            eyes_centered = True

        # Check if the eyes are centered (relative to the calibrated center)
        if len(eye_centers) >= 2:
            check_if_eyes_centered(eye_centers)

        # Draw a light (marker) at the dynamic center position
        cv2.circle(image, dynamic_center, 10, (0, 255, 0), -1)  # Green light

        # Display the image
        cv2.imshow("Eye Centering", image)

        # Stop the pipeline when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            pipeline.stop()  # Stop the pipeline if 'q' is pressed

# Initialize the pipeline with the workflow
pipeline = InferencePipeline.init_with_workflow(
    api_key="VOq8sJmvFwsiBItcJJmR",
    workspace_name="personal-dj7nt",
    workflow_id="detect-count-and-visualize",
    video_reference=0,  # Use webcam (0 for default camera)
    max_fps=30,
    on_prediction=my_sink  # Call my_sink function on each prediction
)

pipeline.start()  # Start the pipeline
pipeline.join()   # Wait for the pipeline to finish
cv2.destroyAllWindows()  # Close all OpenCV windows
