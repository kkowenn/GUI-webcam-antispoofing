import os
import cv2
import face_recognition
import numpy as np
from scipy.spatial import distance as dist
import datetime
import time
import csv
import pandas as pd
from pymongo import MongoClient
import certifi
import pytz

# MongoDB Configuration
client = MongoClient(
    'mongodb+srv://6420015:afterfallSP1@clusteraf.lcvf3mb.mongodb.net/?retryWrites=true&w=majority&appName=ClusterAF',
    tlsCAFile=certifi.where()
)
db = client['afterfall']
collection = db['attendance']

# Step 1: Read the CSV file
csv_file_path = 'attendancecheck.csv'
df = pd.read_csv(csv_file_path)

def load_face_encodings(dataset_path):
    known_face_encodings = []
    known_face_names = []

    for person_name in os.listdir(dataset_path):
        person_folder = os.path.join(dataset_path, person_name)
        if os.path.isdir(person_folder):
            for filename in os.listdir(person_folder):
                if filename.endswith(".jpg") or filename.endswith(".png"):
                    img_path = os.path.join(person_folder, filename)
                    img = cv2.imread(img_path)
                    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img_encodings = face_recognition.face_encodings(rgb_img)

                    if img_encodings:
                        img_encoding = img_encodings[0]
                        known_face_encodings.append(img_encoding)
                        known_face_names.append(person_name)

    return known_face_encodings, known_face_names

def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def is_blinking(eye_landmarks, threshold=0.3):
    left_eye = eye_landmarks["left_eye"]
    right_eye = eye_landmarks["right_eye"]

    left_ear = eye_aspect_ratio(left_eye)
    right_ear = eye_aspect_ratio(right_eye)

    avg_ear = (left_ear + right_ear) / 2.0
    return avg_ear < threshold

def log_attendance(name):
    # Log the attendance with the timestamp in CSV format
    filename = "attendancecheck.csv"
    file_exists = os.path.isfile(filename)

    timestamp = datetime.datetime.now(pytz.UTC)

    with open(filename, "a", newline='') as csvfile:
        fieldnames = ["Name", "Timestamp"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()  # Write header only if the file doesn't exist

        writer.writerow({
            "Name": name,
            "Timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })

    # Update or insert into MongoDB
    query = {'Name': name, 'Timestamp': timestamp}
    update = {'$set': {'attendanace': timestamp}}
    collection.update_one(query, update, upsert=True)

    print(f"Attendance logged for {name} at {timestamp}")

# Path to the dataset of faces
dataset_path = 'data/dataset_faces'

# Load known face encodings
known_face_encodings, known_face_names = load_face_encodings(dataset_path)

# Blink detection parameters
EYE_AR_THRESH = 0.25
EYE_AR_CONSEC_FRAMES = 3  # Number of consecutive frames to consider for a blink
RESET_TIME = 3  # Time in seconds after which the blink counter is reset if face is not detected

# Counters and timers for blink detection
blink_counter = {}
has_logged_blink = {}
last_seen_time = {}

# Open the video capture
video_capture = cv2.VideoCapture(0)

while True:
    # Grab a single frame of video
    ret, frame = video_capture.read()

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Find all the faces and face encodings in the current frame of video
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    current_time = time.time()

    # Reset blink counters and log state for faces that have not been seen recently
    for name in list(last_seen_time.keys()):
        if current_time - last_seen_time[name] > RESET_TIME:
            blink_counter.pop(name, None)
            has_logged_blink.pop(name, None)
            last_seen_time.pop(name, None)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)
        name = "Unknown"
        confidence = 0.0

        if face_distances[best_match_index] < 0.6:
            name = known_face_names[best_match_index]
            confidence = 1 - face_distances[best_match_index]

        # Initialize counters for this face if not already set
        if name not in blink_counter:
            blink_counter[name] = 0
        if name not in has_logged_blink:
            has_logged_blink[name] = False

        # Update the last seen time for this face
        last_seen_time[name] = current_time

        # Get facial landmarks for blink detection
        face_landmarks_list = face_recognition.face_landmarks(rgb_frame)

        if face_landmarks_list:
            face_landmarks = face_landmarks_list[0]

            # Check for blinking (basic liveness detection)
            if is_blinking(face_landmarks, threshold=EYE_AR_THRESH):
                blink_counter[name] += 1
            else:
                if blink_counter[name] >= EYE_AR_CONSEC_FRAMES and not has_logged_blink[name]:
                    # Log attendance after the first blink and set the logged state to True
                    log_attendance(name)
                    has_logged_blink[name] = True
                    blink_counter[name] = 0  # Reset the blink counter after logging

            accuracy = confidence * 100  # Convert to percentage
            if has_logged_blink[name]:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, f"{name} - Real ({accuracy:.2f}%)",
                            (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
            else:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.putText(frame, f"{name} - Fake ({accuracy:.2f}%)",
                            (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
        else:
            accuracy = confidence * 100  # Convert to percentage
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.putText(frame, f"{name} - No landmarks ({accuracy:.2f}%)",
                        (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)

    # Display the resulting image
    cv2.imshow('Video', frame)

    # Hit 'q' on the keyboard to quit!
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release handle to the webcam
video_capture.release()
cv2.destroyAllWindows()

# Step 7: Verify the data transfer
count_in_mongo = collection.count_documents({})
count_in_csv = len(df)

print(f"Number of documents in MongoDB: {count_in_mongo}")
print(f"Number of rows in CSV: {count_in_csv}")

# Step 8: Display the documents in the collection
documents = collection.find()
print("Documents in the attendance collection:")
for doc in documents:
    print(doc)
