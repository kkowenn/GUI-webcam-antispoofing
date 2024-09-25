import os
import cv2
import face_recognition
import numpy as np
from scipy.spatial import distance as dist
import datetime
import pandas as pd
import pytz
import time

class FaceRecognitionAttendance:
    def __init__(self, dataset_path, mongo_collection=None):
        self.dataset_path = dataset_path
        self.mongo_collection = mongo_collection
        self.known_face_encodings, self.known_user_ids = self.load_face_encodings()

    def load_face_encodings(self):
        known_face_encodings = []
        known_user_ids = []
        for user_id in os.listdir(self.dataset_path):
            user_folder = os.path.join(self.dataset_path, user_id)
            if os.path.isdir(user_folder):
                for filename in os.listdir(user_folder):
                    if filename.endswith(".jpg") or filename.endswith(".png"):
                        img_path = os.path.join(user_folder, filename)
                        img = cv2.imread(img_path)
                        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        img_encodings = face_recognition.face_encodings(rgb_img)
                        if img_encodings:
                            img_encoding = img_encodings[0]
                            known_face_encodings.append(img_encoding)
                            known_user_ids.append(user_id)
        return known_face_encodings, known_user_ids

    def fetch_data_from_mongo(self):
        try:
            mongo_data = list(self.mongo_collection.find({}, {'_id': 0}))  # Exclude MongoDB-specific '_id' field
            if len(mongo_data) == 0:
                print("No data found in MongoDB.")
            else:
                print(f"Fetched {len(mongo_data)} records from MongoDB.")
            mongo_df = pd.DataFrame(mongo_data)
            return mongo_df
        except Exception as e:
            print(f"Error fetching data from MongoDB: {e}")
            return None

    def eye_aspect_ratio(self, eye):
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        ear = (A + B) / (2.0 * C)
        return ear

    def is_blinking(self, face_landmarks, threshold=0.3):
        left_eye = face_landmarks["left_eye"]
        right_eye = face_landmarks["right_eye"]
        left_ear = self.eye_aspect_ratio(left_eye)
        right_ear = self.eye_aspect_ratio(right_eye)
        avg_ear = (left_ear + right_ear) / 2.0
        return avg_ear < threshold

    def process_video_stream(self, matched_class_code):
        video_capture = cv2.VideoCapture(0)
        EYE_AR_THRESH = 0.25
        EYE_AR_CONSEC_FRAMES = 3
        blink_counter = {}
        has_logged_blink = {}

        while True:
            ret, frame = video_capture.read()
            if frame is None:
                print("Failed to capture video frame.")
                continue
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            current_time = time.time()

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                user_id = "Unknown"
                confidence = 0.0

                if face_distances[best_match_index] < 0.6:
                    user_id = self.known_user_ids[best_match_index]
                    confidence = 1 - face_distances[best_match_index]

                face_landmarks_list = face_recognition.face_landmarks(rgb_frame)

                if face_landmarks_list:
                    face_landmarks = face_landmarks_list[0]
                    if user_id not in blink_counter:
                        blink_counter[user_id] = 0
                    if user_id not in has_logged_blink:
                        has_logged_blink[user_id] = False

                    # Check for blinking
                    if self.is_blinking(face_landmarks, threshold=EYE_AR_THRESH):
                        blink_counter[user_id] += 1
                    else:
                        if blink_counter[user_id] >= EYE_AR_CONSEC_FRAMES and not has_logged_blink[user_id]:
                            # Log attendance with both user_id and matched_class_code
                            self.log_attendance(user_id, matched_class_code)
                            has_logged_blink[user_id] = True
                            blink_counter[user_id] = 0

                    accuracy = confidence * 100
                    if has_logged_blink[user_id]:
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        cv2.putText(frame, f"{user_id} - Real ({accuracy:.2f}%)",
                                    (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
                    else:
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                        cv2.putText(frame, f"{user_id} - Fake ({accuracy:.2f}%)",
                                    (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)

            cv2.imshow('Video', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()

    def log_attendance(self, user_id, matched_class_code):
        # Get the current time in UTC and convert it to Thailand timezone
        timestamp_utc = datetime.datetime.now(pytz.UTC)
        thailand_tz = pytz.timezone('Asia/Bangkok')
        timestamp_thailand = timestamp_utc.astimezone(thailand_tz)

        try:
            if self.mongo_collection is not None:
                # Check if document exists for the given userID and classID
                user_doc = self.mongo_collection.find_one({'UserID': user_id, 'classID': matched_class_code})

                print(f"Found document for UserID: {user_id}, ClassID: {matched_class_code}: {user_doc}")

                if not user_doc:
                    # Insert a new document if none exists for this user and class
                    result = self.mongo_collection.insert_one({
                        'UserID': user_id,
                        'attendance': [timestamp_thailand],
                        'classID': matched_class_code
                    })
                    print(f"Insertion result: {result.inserted_id}")
                else:
                    # If the document exists, push the new attendance timestamp
                    update_result = self.mongo_collection.update_one(
                        {'UserID': user_id, 'classID': matched_class_code},
                        {'$push': {'attendance': timestamp_thailand}}  # Push attendance to the array
                    )

                    # Debugging: Check the result of the update operation
                    print(f"Matched count: {update_result.matched_count}, Modified count: {update_result.modified_count}")

                print(f"Attendance logged for {user_id} in class {matched_class_code}")

        except Exception as e:
            print(f"Error logging attendance for {user_id}: {e}")
