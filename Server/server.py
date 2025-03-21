from flask import Flask, request, jsonify, Response, render_template
from picamera2 import Picamera2
from flask_cors import CORS
import cv2
import threading
import smbus2  # I²C communication
import time
import struct


# Flask app setup
app = Flask(__name__)
CORS(app)

# Initialize the camera
picam2 = Picamera2()
video_config = picam2.create_video_configuration(
    main={"size": (2000, 2000)},
    controls={"FrameRate": 60, "NoiseReductionMode": 2}
)
picam2.configure(video_config)
picam2.start()

# I²C Addresses
ARDUINO_PAN_TILT = 0x10  # Arduino controlling the servos
ARDUINO_SENSORS = 0x20    # Arduino reading sensors

# I²C Bus
bus = smbus2.SMBus(1)  # Use I²C bus 1 (default for Raspberry Pi)

# Servo Position (default)
servo_pan = 90
servo_tilt = 90

# Sensor Data
sensor_data = {
    "temperature_dht": 0.0,
    "humidity": 0.0,
    "temperature_ds18b20": 0.0,
    "soil_moisture": 0
}


# ======= CAMERA STREAM FUNCTION ===========
def generate_frames():
    while True:
        frame = picam2.capture_array()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rotated = cv2.rotate(frame_rgb, cv2.ROTATE_180)
        _, buffer = cv2.imencode('.jpg', frame_rotated)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# ======= SERVO CONTROL FUNCTION ===========
@app.route('/set_servo', methods=['POST'])
def set_servo():
    global servo_pan, servo_tilt
    data = request.get_json()

    print("Set Servos")
    print(servo_pan)
    print(servo_tilt)
    print(" ")


    if 'pan' in data and 'tilt' in data:
        servo_pan = max(0, min(180, int(data['pan'])))   # Limit range 0-180
        servo_tilt = max(0, min(180, int(data['tilt'])))

        try:
            # Send data to Arduino over I²C
            bus.write_i2c_block_data(ARDUINO_PAN_TILT, 0, [servo_pan, servo_tilt])
            print("write ")

            return jsonify({"message": "Servo positions updated",
                            "pan": servo_pan, "tilt": servo_tilt})
        except Exception as e:
            return jsonify({"error": f"Failed to send I²C data: {e}"}), 500
    else:
        return jsonify({"error": "Missing pan or tilt value"}), 400


# ======= READ SENSOR DATA FROM ARDUINO ===========
def read_sensors():
    global sensor_data
    while True:
        try:
            # Request 12 bytes of data (float values + int for soil moisture)
            raw_data_list = bus.read_i2c_block_data(ARDUINO_SENSORS, 0, 14)
            # Convert list to bytes
            raw_data = bytes(raw_data_list)  # Convert list to bytes object
            # Unpack data using correct format
            temperature_dht, humidity, temperature_ds18b20, soil_moisture = struct.unpack('<fffH', raw_data[:14])

            # print(f"Temperature (DHT22): {temperature_dht:.2f}°C")
            # print(f"Humidity: {humidity:.2f}%")
            # print(f"Temperature (DS18B20): {temperature_ds18b20:.2f}°C")
            # print(f"Soil Moisture: {soil_moisture}")


            # Convert bytes to floats (4 bytes per float, 2 bytes for int)
            # temperature_dht = int.from_bytes(raw_data[0:4], 'little') / 100.0
            # humidity = int.from_bytes(raw_data[4:8], 'little') / 100.0
            # temperature_ds18b20 = int.from_bytes(raw_data[8:12], 'little') / 100.0
            # soil_moisture = raw_data[12]  # Single byte value

            # Update global sensor data
            sensor_data = {
                "temperature_dht": temperature_dht,
                "humidity": humidity,
                "temperature_ds18b20": temperature_ds18b20,
                "soil_moisture": soil_moisture
            }
        except Exception as e:
            print(f"Error reading I²C sensor data: {e}")

        time.sleep(1)  # Read sensors every 5 seconds


@app.route('/get_sensors', methods=['GET'])
def get_sensors():
    return jsonify({
        "temperature_dht": round(sensor_data["temperature_dht"], 2),
        "humidity": round(sensor_data["humidity"], 2),
        "temperature_ds18b20": round(sensor_data["temperature_ds18b20"], 2),
        "soil_moisture": sensor_data["soil_moisture"]
    })

# Start sensor reading in a separate thread
sensor_thread = threading.Thread(target=read_sensors, daemon=True)
sensor_thread.start()


# ======= RUN FLASK SERVER ===========
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
