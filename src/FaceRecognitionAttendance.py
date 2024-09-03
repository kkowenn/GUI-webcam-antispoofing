import os
import cv2
import face_recognition
import numpy as np
from scipy.spatial import distance as dist
import datetime
import time
import csv
import pandas as pd
import pytz

class FaceRecognitionAttendance:
    def __init__(self, dataset_path, csv_file_path, mongo_collection=None):
        self.dataset_path = dataset_path
        self.csv_file_path = csv_file_path
        self.mongo_collection = mongo_collection
        self.known_face_encodings, self.known_face_names = self.load_face_encodings()

        # Blink detection parameters
        self.EYE_AR_THRESH = 0.25
        self.EYE_AR_CONSEC_FRAMES = 3  # Number of consecutive frames to consider for a blink
        self.RESET_TIME = 3  # Time in seconds after which the blink counter is reset if face is not detected

        # Counters and timers for blink detection
        self.blink_counter = {}
        self.has_logged_blink = {}
        self.last_seen_time = {}

    def load_face_encodings(self):
        known_face_encodings = []
        known_face_names = []

        for person_name in os.listdir(self.dataset_path):
            person_folder = os.path.join(self.dataset_path, person_name)
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

    def eye_aspect_ratio(self, eye):
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        ear = (A + B) / (2.0 * C)
        return ear

    def is_blinking(self, eye_landmarks, threshold=0.3):
        left_eye = eye_landmarks["left_eye"]
        right_eye = eye_landmarks["right_eye"]

        left_ear = self.eye_aspect_ratio(left_eye)
        right_ear = self.eye_aspect_ratio(right_eye)

        avg_ear = (left_ear + right_ear) / 2.0
        return avg_ear < threshold

    def log_attendance(self, name):
        # Log the attendance with the timestamp in CSV format
        filename = self.csv_file_path
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
        if self.mongo_collection is not None:
            query = {'Name': name, 'Timestamp': timestamp}
            update = {'$set': {'attendance': timestamp}}
            self.mongo_collection.update_one(query, update, upsert=True)

        print(f"Attendance logged for {name} at {timestamp}")

    def process_video_stream(self):
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
            for name in list(self.last_seen_time.keys()):
                if current_time - self.last_seen_time[name] > self.RESET_TIME:
                    self.blink_counter.pop(name, None)
                    self.has_logged_blink.pop(name, None)
                    self.last_seen_time.pop(name, None)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                name = "Unknown"
                confidence = 0.0

                if face_distances[best_match_index] < 0.6:
                    name = self.known_face_names[best_match_index]
                    confidence = 1 - face_distances[best_match_index]

                # Initialize counters for this face if not already set
                if name not in self.blink_counter:
                    self.blink_counter[name] = 0
                if name not in self.has_logged_blink:
                    self.has_logged_blink[name] = False

                # Update the last seen time for this face
                self.last_seen_time[name] = current_time

                # Get facial landmarks for blink detection
                face_landmarks_list = face_recognition.face_landmarks(rgb_frame)

                if face_landmarks_list:
                    face_landmarks = face_landmarks_list[0]

                    # Check for blinking (basic liveness detection)
                    if self.is_blinking(face_landmarks, threshold=self.EYE_AR_THRESH):
                        self.blink_counter[name] += 1
                    else:
                        if self.blink_counter[name] >= self.EYE_AR_CONSEC_FRAMES and not self.has_logged_blink[name]:
                            # Log attendance after the first blink and set the logged state to True
                            self.log_attendance(name)
                            self.has_logged_blink[name] = True
                            self.blink_counter[name] = 0  # Reset the blink counter after logging

                    accuracy = confidence * 100  # Convert to percentage
                    if self.has_logged_blink[name]:
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

    def verify_data_transfer(self):
        # Step 7: Verify the data transfer
        count_in_mongo = self.mongo_collection.count_documents({}) if self.mongo_collection else 0
        df = pd.read_csv(self.csv_file_path)
        count_in_csv = len(df)

        print(f"Number of documents in MongoDB: {count_in_mongo}")
        print(f"Number of rows in CSV: {count_in_csv}")

    def display_documents(self):
        if self.mongo_collection:
            documents = self.mongo_collection.find()
            print("Documents in the attendance collection:")
            for doc in documents:
                print(doc)
        else:
            print("MongoDB collection is not initialized.")

