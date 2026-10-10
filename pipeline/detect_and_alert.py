import os
import sys
import time

# Force TensorFlow to use the legacy Keras 2 engine for Teachable Machine models
os.environ["TF_USE_LEGACY_KERAS"] = "1"

# Prevent macOS pyarrow threading crash when loading TensorFlow
sys.modules["pyarrow"] = None

import cv2
import numpy as np
import serial
from tf_keras.models import load_model

# ----------------------------------------------------------------------
# Hardware & Serial Settings
# ----------------------------------------------------------------------

# Map Teachable Machine class indices:
# Class 0: Background/Empty Desk -> sends "off" (Green LED ON, alarm OFF)
# Class 1: Target Object Detected -> sends "on" (Red LED ON, Buzzer ON)
MESSAGE_FOR_LABEL = {
    0: "off",
    1: "on",
}

BAUD_RATE = 9600
CONFIDENCE_THRESHOLD = 0.80

# Replace with your actual port from Arduino IDE > Tools > Port
SERIAL_PORT = "/dev/cu.usbmodem3101"

board = None
try:
    board = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Allow Arduino Mega time to reset after opening port
    print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
except serial.SerialException as error:
    print(f"Could not open {SERIAL_PORT}: {error}")
    print("Ensure the Serial Monitor is closed in Arduino IDE.")


def send(message):
    """Send command to Arduino over Serial."""
    if board is None:
        return
    board.write((message + "\n").encode())
    print(f"Sent state: {message}")


# ----------------------------------------------------------------------
# Vision Model & Camera Setup
# ----------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))

model = load_model(os.path.join(HERE, "keras_model.h5"), compile=False)

with open(os.path.join(HERE, "labels.txt"), "r") as f:
    class_names = [line.strip().split(" ", 1)[1] for line in f if line.strip()]

camera = cv2.VideoCapture(0)
if not camera.isOpened():
    sys.exit("Could not open webcam. Check index (try 1) or terminal privacy permissions.")

print("Webcam active. Press 'q' or 'Esc' in the preview window to exit.")

last_message = None

while True:
    ret, frame = camera.read()
    if not ret:
        print("Camera frame dropped.")
        break

    # Center crop square to match Teachable Machine aspect ratio
    h, w = frame.shape[:2]
    size = min(h, w)
    top, left = (h - size) // 2, (w - size) // 2
    frame = frame[top:top + size, left:left + size]

    # Resize to standard 224x224 input
    frame = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_AREA)
    cv2.imshow("Pipeline Camera Stream", frame)

    # Preprocess image
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = np.asarray(image, dtype=np.float32).reshape(1, 224, 224, 3)
    image = (image / 127.5) - 1  # Normalize to [-1, 1]

    # Run inference
    prediction = model.predict(image, verbose=0)
    index = np.argmax(prediction[0])
    class_name = class_names[index]
    confidence_score = prediction[0][index]

    print(f"Class: {class_name:<15} Confidence: {confidence_score * 100:.1f}%")

    # Determine command based on confidence
    message = None
    if confidence_score >= CONFIDENCE_THRESHOLD:
        message = MESSAGE_FOR_LABEL.get(int(index))

    # Send trigger only when the state changes
    if message is not None and message != last_message:
        send(message)
        last_message = message

    key = cv2.waitKey(1) & 0xFF
    if key == 27 or key == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
if board is not None:
    board.close()