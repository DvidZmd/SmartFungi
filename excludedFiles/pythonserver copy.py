from flask import Flask, request, jsonify, Response, render_template
#import serial
import time
from picamera2 import Picamera2
import cv2
import threading
from flask_cors import CORS

#import Adafruit_DHT
import time


# Global variables to store the pan, tilt, and temperature data
current_pan = None
current_tilt = None
current_temp = None
current_hum = None
current_step = None


#logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
CORS(app)

# Configure serial connection
arduino_port = "/dev/ttyACM0"  # Replace with your Arduino's serial port
baud_rate = 9600
#arduino = serial.Serial(arduino_port, baud_rate, timeout=1)
# Initialize the camera
picam2 = Picamera2()

# Set the resolution (e.g., 1920x1080 for Full HD)
# Configure for high-quality video
video_config = picam2.create_video_configuration(
    main={"size": (1920, 1080)},
    controls={
        "FrameRate": 30,
        #"ExposureTime": 10000,
        #"AnalogueGain": 1.0,
        #"Sharpness": 1.5,
        "NoiseReductionMode": 2
        #"DynamicRangeCompression": 2
    }
)
# Apply the configuration
picam2.configure(video_config)
# Start the camera
picam2.start()



# def periodically():
#     global current_pan, current_tilt, current_temp, current_hum, current_step
#     while True:
#         try:
#             # Clear the serial buffer to remove any old messages
#             arduino.flushInput()
#             time.sleep(0.7)
#             # Send the movement command to the Arduino
#             arduino.write(("STATUS\n").encode())
#             #time.sleep(1)  # Delay for 1 second (adjust as needed

#             # Read the serial data from Arduino
#             #if arduino.in_waiting > 0:  # Check if data is available
#             response = arduino.readline().decode().strip()

#             # If the response contains PAN, TILT, and TEMP data
#             if response.startswith("PAN:"):
#                 pan, tilt, temp, hum, step = response.split(", ")
#                 current_pan = pan.split(":")[1].strip()
#                 current_tilt = tilt.split(":")[1].strip()
#                 current_temp = temp.split(":")[1].strip()
#                 current_hum = hum.split(":")[1].strip()
#                 current_step = step.split(":")[1].strip()

#                 # Print the values to the console for debugging
#                 print(f"Pan: {current_pan}, Tilt: {current_tilt}, Temp: {current_temp}, Humidity: {current_hum}, Step: {current_step}")

#         except Exception as e:
#             print(f"Error reading serial: {e}")
        
#         # Sleep for a short time to avoid busy-waiting
#         time.sleep(0.2)

# # Start the periodic reading in a separate thread
# thread = threading.Thread(target=periodically, daemon=True)
# thread.start()



def generate_frames():
    while True:
        frame = picam2.capture_array()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        _, buffer = cv2.imencode('.jpg', frame_rgb)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def home():
    try:
        # Try to render the HTML template
        return render_template('index.html')  # Render the index.html file
    except Exception as e:
        # If an error occurs, log it and return a meaningful error message
        print(f"Error rendering template: {e}")
        return jsonify({"error": "Failed to load the page"}), 500

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# @app.route("/move", methods=["POST"])
# def move_servo():
#     command = request.json.get("command", "").upper()
#     try:
#         if command in ["UP", "DOWN", "LEFT", "RIGHT"]:

#         # Clear the serial buffer to remove any old messages
#             arduino.flushInput()

#         # Send the movement command to the Arduino
#             arduino.write((command + "\n").encode())
        
#         # Add a delay before sending the "STATUS" command
#         #time.sleep(0.1)  # Delay for 1 second (adjust as needed
        
#         # Wait for the Arduino to respond with the positions
#         #response = arduino.readline().decode().strip()  # Read the response from Arduino
        
#         # # Check if the response contains PAN and TILT data
#         # if response.startswith("PAN:"):
#         #     pan, tilt, temp, step = response.split(", ")
#         #     pan_position = pan.split(":")[1].strip()
#         #     tilt_position = tilt.split(":")[1].strip()
#         #     current_temp = temp.split(":")[1].strip()
            
#         #     # Return the response with the current pan and tilt positions
#         #     response = {
#         #         "status": "success",
#         #         "pan": current_pan,
#         #         "tilt": current_tilt,
#         #         "temp": current_temp,
#         #         "step": current_step
#         #     }

#         #     # Print the response to the console
#         #     print("Response:", response)

#         #     # Return the response as JSON
#         #     return jsonify(response) 
#         return jsonify({"status": "ok"})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def read_serial():
    try:
        # Return the current pan, tilt, and temp values as JSON
        response = {
            "status": "success",
            "pan": current_pan,
            "tilt": current_tilt,
            "temp": current_temp,
            "hum": current_hum,
            "step": current_step
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @app.route("/step", methods=["POST"])
# def set_step():
#     step = request.json.get("step", None)
#     if isinstance(step, int) and 1 <= step <= 180:
#         arduino.flushInput()
#         arduino.write((f"STEP {step}\n").encode())

#         return jsonify({"status": "success", "message": f"Step size set to {step}"})
#     return jsonify({"status": "error", "message": "Invalid step size"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)