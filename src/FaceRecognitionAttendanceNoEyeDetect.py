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

    def process_video_stream(self):
        video_capture = cv2.VideoCapture(0)

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
                accuracy = confidence * 100  # Convert to percentage
                if user_id != "Unknown":
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame, f"{user_id} - Real ({accuracy:.2f}%)",
                                (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
                    # Log attendance when recognized
                    self.log_attendance(user_id)
                else:
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                    cv2.putText(frame, f"{user_id} - Fake ({accuracy:.2f}%)",
                                (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
            cv2.imshow('Video', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        video_capture.release()
        cv2.destroyAllWindows()

    def log_attendance(self, user_id):
        timestamp = datetime.datetime.now(pytz.UTC)  # Use UTC timezone for consistency
        cooldown_period = datetime.timedelta(minutes=3)  # Set cooldown period of 3 minutes

        try:
            if self.mongo_collection is not None:
                # Check if the user document already exists
                user_doc = self.mongo_collection.find_one({'UserID': user_id})

                if user_doc:
                    # If 'attendance' exists and is not an array, convert it to an array
                    if not isinstance(user_doc.get('attendance'), list):
                        self.mongo_collection.update_one(
                            {'UserID': user_id},
                            {'$set': {'attendance': [user_doc['attendance']]}}
                        )
                        user_doc = self.mongo_collection.find_one({'UserID': user_id})  # Refresh user document

                    # Get the latest timestamp in the attendance array
                    if 'attendance' in user_doc and user_doc['attendance']:
                        last_timestamp = user_doc['attendance'][-1]

                        # Convert the last_timestamp to be timezone-aware if it's naive
                        if last_timestamp.tzinfo is None:
                            last_timestamp = last_timestamp.replace(tzinfo=pytz.UTC)

                        # Skip logging if the last timestamp is within the cooldown period (2-3 minutes)
                        if last_timestamp + cooldown_period > timestamp:
                            print(f"Attendance for {user_id} was already logged within the last 3 minutes.")
                            return

                # Log the new attendance timestamp by appending to the 'attendance' array
                self.mongo_collection.update_one(
                    {'UserID': user_id},
                    {'$push': {'attendance': timestamp}},
                    upsert=True
                )
                print(f"Attendance logged in MongoDB for {user_id} at {timestamp}")

        except Exception as e:
            print(f"Error logging attendance in MongoDB: {e}")

