import numpy as np
import sounddevice as sd
import time
import tflite_runtime.interpreter as tflite
import librosa
import json

# ================= LOAD TINYML MODEL =================
interpreter = tflite.Interpreter(model_path="door_model.tflite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# ================= SETTINGS =================
SAMPLE_RATE = 16000
DURATION = 1  # seconds
CONFIDENCE_THRESHOLD = 0.80
cooldown = 3
last_action_time = 0

labels = ["open door", "close door", "unknown"]

print("TinyML Voice Door System Ready")

# ================= FEATURE EXTRACTION =================
def extract_features(audio):
    mfcc = librosa.feature.mfcc(
        y=audio,
        sr=SAMPLE_RATE,
        n_mfcc=13
    )
    mfcc = np.mean(mfcc.T, axis=0)
    return mfcc.reshape(1, -1).astype(np.float32)

# ================= MAIN LOOP =================
try:
    while True:

        # Record 1 second audio
        audio = sd.rec(int(SAMPLE_RATE * DURATION),
                       samplerate=SAMPLE_RATE,
                       channels=1,
                       dtype='float32')
        sd.wait()

        audio = audio.flatten()

        # Extract MFCC features
        features = extract_features(audio)

        # Run TinyML Inference
        interpreter.set_tensor(input_details[0]['index'], features)
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]['index'])[0]

        prediction_index = np.argmax(output)
        confidence = output[prediction_index]
        predicted_label = labels[prediction_index]

        print("Prediction:", predicted_label,
              "| Confidence:", round(float(confidence), 2))

        # Confidence filter
        if confidence < CONFIDENCE_THRESHOLD:
            continue

        # Cooldown protection
        if time.time() - last_action_time < cooldown:
            continue

        # ---------------- OPEN ----------------
        if predicted_label == "open door":
            lcd.clear()
            lcd.write_string("Door System")
            lcd.cursor_pos = (1, 0)
            lcd.write_string("Status: OPEN   ")
            set_servo(175)
            last_action_time = time.time()

        # ---------------- CLOSE ----------------
        elif predicted_label == "close door":
            lcd.clear()
            lcd.write_string("Door System")
            lcd.cursor_pos = (1, 0)
            lcd.write_string("Status: CLOSED ")
            set_servo(0)
            last_action_time = time.time()

except KeyboardInterrupt:
    print("Stopped")

finally:
    servo.stop()
    GPIO.cleanup()
    lcd.clear()