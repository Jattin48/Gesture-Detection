import cv2
import mediapipe as mp
from gtts import gTTS
import pygame
import time
import os
import datetime
import threading
import numpy as np
import csv
import speech_recognition as sr

# === Configuration ===
LANGUAGE = "hi"
LOG_FILE = "gesture_log.csv"

# === Init ===
mp_hands = mp.solutions.hands
mp_face = mp.solutions.face_mesh
hands = mp_hands.Hands()
face_mesh = mp_face.FaceMesh()
mp_draw = mp.solutions.drawing_utils

pygame.init()
pygame.mixer.init()
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

paused = False
last_spoken = ""
last_time = 0
person_detected = False

# === Logging ===
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Name", "Detected", "Language"])

# === Load OpenCV face detector ===
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# === Gesture Library ===
gesture_library = {
    (0,0,0,0,0): "Stop",
    (0,1,1,0,0): "Peace",
    (1,1,0,0,1): "I Love You",
    (1,0,0,0,0): "Thumbs Up",
    (0,1,0,0,0): "Point",
    (1,1,1,1,1): "Open Palm"
}
import itertools
for idx, pattern in enumerate(itertools.product([0, 1], repeat=5)):
    if pattern not in gesture_library and idx < 100:
        gesture_library[pattern] = f"Gesture #{idx+1}"

def speak(text):
    try:
        filename = "temp.mp3"
        tts = gTTS(text=text, lang=LANGUAGE)
        tts.save(filename)
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        time.sleep(0.5)
        os.remove(filename)
    except Exception as e:
        print("TTS error:", e)

def log_to_csv(name, text):
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.datetime.now().isoformat(), name, text, LANGUAGE])

def get_finger_states(hand_landmarks):
    fingers = []
    fingers.append(1 if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x else 0)
    for tip, base in zip([8, 12, 16, 20], [6, 10, 14, 18]):
        fingers.append(1 if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[base].y else 0)
    return tuple(fingers)

def detect_expression(landmarks, img_shape):
    h, w = img_shape
    lm = lambda i: (int(landmarks[i].x * w), int(landmarks[i].y * h))
    mouth_top = lm(13); mouth_bottom = lm(14)
    mouth_open = abs(mouth_bottom[1] - mouth_top[1])
    brow_left = lm(70); eye_left = lm(159)
    brow_raise = abs(brow_left[1] - eye_left[1])
    if mouth_open > 25 and brow_raise > 15: return "Surprised"
    elif mouth_open < 10 and brow_raise < 10: return "Neutral"
    elif mouth_open > 15 and brow_raise < 5: return "Happy"
    elif mouth_open < 10 and brow_raise > 15: return "Sad"
    elif brow_raise < 5 and mouth_open < 10: return "Angry"
    return ""

def listen_for_commands():
    global paused, LANGUAGE
    r = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source: r.adjust_for_ambient_noise(source)
    while True:
        try:
            with mic as source:
                print("[Voice] Listening...")
                audio = r.listen(source, timeout=5)
                command = r.recognize_google(audio).lower()
                print("[Voice] Command:", command)
                if "exit" in command: os._exit(0)
                elif "pause" in command or "stop" in command: paused = True; speak("Detection paused")
                elif "resume" in command or "start" in command: paused = False; speak("Resumed")
                elif "language to hindi" in command: LANGUAGE = "hi"; speak("Hindi")
                elif "language to english" in command: LANGUAGE = "en"; speak("English")
        except Exception: continue

# Start voice command listener
threading.Thread(target=listen_for_commands, daemon=True).start()

while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    word = ""
    identity = "My lord"

    if not paused:
        # === Detect face (OpenCV) ===
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        if len(faces) > 0:
            identity = "My lord"

        # === Gesture Detection ===
        results_hand = hands.process(img_rgb)
        if results_hand.multi_hand_landmarks:
            for handLms in results_hand.multi_hand_landmarks:
                mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)
                finger_state = get_finger_states(handLms)
                if finger_state in gesture_library:
                    word = gesture_library[finger_state]

        # === Expression Detection ===
        results_face = face_mesh.process(img_rgb)
        if results_face.multi_face_landmarks:
            for face_landmarks in results_face.multi_face_landmarks:
                expression = detect_expression(face_landmarks.landmark, img.shape[:2])
                if expression:
                    word = expression

        # === Speak + Log ===
        if word and (word != last_spoken or (time.time() - last_time > 3)):
            print(f"Detected [{identity}]: {word}")
            threading.Thread(target=speak, args=(f"{identity} is {word}",), daemon=True).start()
            log_to_csv(identity, word)
            last_spoken = word
            last_time = time.time()

        if word:
            cv2.putText(img, f"{identity}: {word}", (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("AI Tool (OpenCV Identity + Gesture + Expression)", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
