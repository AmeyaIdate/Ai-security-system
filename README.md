# AI Theft Alarm: Teachable Machine → Python → Arduino

IT 254 individual project: an AI-to-hardware pipeline.

A webcam watches the scene. An image classifier trained in [Google Teachable Machine](https://teachablemachine.withgoogle.com/) labels each frame as **Innocent bystander** or **Weaponized thief**. When it detects a threat with at least 80% confidence, Python sends a command over USB serial to an Arduino Mega. The Arduino then turns on a red LED and sounds a buzzer. When the scene is clear, the green LED is on and the buzzer is silent.

```
Webcam ──► Python (OpenCV + Keras model) ──"on"/"off"──► Arduino Mega ──► Red/Green LEDs + Buzzer
              224×224 frame, classify          USB serial, 9600 baud
```

## Demo

<!-- TODO: add your own photos / video to media/ and update these links -->
| Innocent bystander → green LED | Weaponized thief → red LED + buzzer |
|---|---|
| ![All clear](media/all_clear.jpg) | ![Alarm](media/alarm.jpg) |

Video: [media/demo.mp4](media/demo.mp4)

## Repository layout

| Path | Contents |
|---|---|
| `pipeline/detect_and_alert.py` | Webcam capture, model inference, serial output |
| `pipeline/keras_model.h5` | Teachable Machine image model, exported as Keras (2 classes, 224×224 input) |
| `pipeline/labels.txt` | Class names (`0 Innocent bystander`, `1 Weaponized thief`) |
| `arduino/theft_alarm/theft_alarm.ino` | Arduino sketch that listens for `on`/`off` and drives the LEDs and buzzer |
| `requirements.txt` | Python package versions the pipeline was tested with |
| `media/` | Photos and video of the working pipeline |

## Data

The model was trained in Teachable Machine on webcam images I captured myself, in two classes:

- **Class 0 – Innocent bystander:** a person, or an empty desk, with no weapon <!-- TODO: confirm/describe -->
- **Class 1 – Weaponized thief:** a person holding a prop "weapon" <!-- TODO: describe what object you used -->

The trained model is included as `pipeline/keras_model.h5`. The raw training images are not included. <!-- TODO: add them, or link your Teachable Machine project, if you want -->

## Hardware

- Arduino Mega 2560 (any Uno-class board also works)
- Red LED and green LED, each with a 220 Ω resistor
- Active or passive buzzer
- Breadboard, jumper wires, USB cable
- Laptop webcam

| Component | Arduino pin |
|---|---|
| Red LED (+) | 12 |
| Green LED (+) | 11 |
| Buzzer (+) | 8 |
| All (–) | GND |

If you wire it differently, change the pin constants at the top of `theft_alarm.ino`.

## Setup & run

1. **Flash the Arduino.** Open `arduino/theft_alarm/theft_alarm.ino` in the Arduino IDE, select the board and port, and upload it. Then **close the Serial Monitor**, because Python needs the port.
2. **Install the Python packages** (tested with Python 3.12):
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Set the serial port.** In `pipeline/detect_and_alert.py`, set `SERIAL_PORT` to the port shown under Arduino IDE → Tools → Port. Mine is `/dev/cu.usbmodem3101`. On Windows it looks like `COM3`.
4. **Run the pipeline:**
   ```bash
   python pipeline/detect_and_alert.py
   ```
   A preview window opens, and the terminal prints the predicted class and confidence for every frame. Press `q` or `Esc` to quit.

### How the pipeline works

1. Each webcam frame is center-cropped to a square and resized to 224×224, which matches how Teachable Machine trains.
2. Pixels are converted from BGR to RGB and normalized to the range [-1, 1].
3. The model predicts the class. If confidence is at least `CONFIDENCE_THRESHOLD` (0.80), the class maps to `off` (class 0) or `on` (class 1).
4. A command is sent only when the state **changes**, so the serial line isn't flooded with messages.

## Tips, tricks & bottlenecks

<!-- TODO: rewrite these in your own words and add anything else you hit — error messages, screenshots, how long things took. -->

- **Keras 3 vs. Teachable Machine models:** Teachable Machine exports Keras 2 `.h5` models, but TensorFlow 2.16+ ships with Keras 3, which fails to load them. Fix: `pip install tf_keras`, set `TF_USE_LEGACY_KERAS=1` *before* importing TensorFlow, and load the model with `from tf_keras.models import load_model`.
- **macOS crash on import:** importing TensorFlow crashed because of a threading conflict with `pyarrow`. Setting `sys.modules["pyarrow"] = None` before the import works around it.
- **"Resource busy" on the serial port:** only one program can hold the port at a time, so close the Arduino IDE Serial Monitor before running Python.
- **Arduino resets when the port opens:** opening the serial connection reboots the Mega, so the script waits 2 seconds before sending anything. Without the wait, the first command gets lost.
- **Webcam won't open:** on macOS, grant camera permission to Terminal or VS Code under System Settings → Privacy & Security → Camera. If you have several cameras, try `cv2.VideoCapture(1)`.
- **Flickering alarm:** sending a command on every frame, with no confidence threshold, made the LEDs flicker between states. The 80% threshold plus send-only-on-change fixed it.
- **Preprocessing must match training:** the center crop, 224×224 resize, RGB order, and [-1, 1] normalization all have to match Teachable Machine. Otherwise predictions are unreliable.

## Tested versions

macOS, Python 3.12.10, TensorFlow 2.21.0, tf_keras 2.21.0, NumPy 2.5.3, OpenCV 5.0.0, pyserial 3.5.
