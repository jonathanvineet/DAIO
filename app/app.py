from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from inference import InferencePipeline
import cv2
import base64
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Define the sink function for handling predictions
def my_sink(result, video_frame):
    if result.get("output_image"):
        # Encode the output image as base64
        _, buffer = cv2.imencode('.jpg', result["output_image"].numpy_image)
        frame_data = base64.b64encode(buffer).decode('utf-8')
        socketio.emit('frame', {"image": frame_data})
    print(result)  # You can log or handle the prediction here

def start_pipeline():
    pipeline = InferencePipeline.init_with_workflow(
        api_key="VOq8sJmvFwsiBItcJJmR",
        workspace_name="personal-dj7nt",
        workflow_id="detect-count-and-visualize",
        video_reference=0,  # Use webcam
        max_fps=30,
        on_prediction=my_sink
    )
    pipeline.start()
    pipeline.join()

# Start the pipeline in a separate thread
threading.Thread(target=start_pipeline).start()

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
