// Theft alarm controlled by the Python vision pipeline over Serial.
//   "on"  -> Red LED ON, Green LED OFF, buzzer sounding (threat detected)
//   "off" -> Green LED ON, Red LED OFF, buzzer silent (all clear)
//
// Change the pin numbers below to match your wiring.

const int RED_LED_PIN = 12;
const int GREEN_LED_PIN = 11;
const int BUZZER_PIN = 8;

const long BAUD_RATE = 9600;  // Must match BAUD_RATE in detect_and_alert.py

bool alarmOn = false;

void setAlarm(bool on) {
  alarmOn = on;
  digitalWrite(RED_LED_PIN, on ? HIGH : LOW);
  digitalWrite(GREEN_LED_PIN, on ? LOW : HIGH);
  if (!on) {
    noTone(BUZZER_PIN);
  }
}

void setup() {
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  Serial.begin(BAUD_RATE);
  setAlarm(false);
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    if (command == "on") {
      setAlarm(true);
    } else if (command == "off") {
      setAlarm(false);
    }
  }

  // Two-tone siren while the alarm is active
  if (alarmOn) {
    tone(BUZZER_PIN, (millis() / 300) % 2 ? 1000 : 1500);
  }
}
