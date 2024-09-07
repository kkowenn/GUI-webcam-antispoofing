import cv2
import os
import numpy as np
import random

class FaceCaptureAndAugmentation:
    def __init__(self, user_id, output_dir="data/dataset_faces", num_faces_to_save=500, augmentation_limits=None):
        self.user_id = user_id
        self.output_dir = os.path.join(output_dir, user_id)
        self.num_faces_to_save = num_faces_to_save
        self.captured_faces = []
        self.face_count = 0
        self.augmentation_types = ["bright", "dark", "revert", "erase", "rotate"]

        # Set default augmentation limits if not provided
        if augmentation_limits is None:
            self.augmentation_limits = {aug: 100 for aug in self.augmentation_types}
        else:
            self.augmentation_limits = augmentation_limits

        # Create directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Load the Haar cascade for face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def capture_faces(self):
        # Initialize the webcam
        cap = cv2.VideoCapture(0)

        while True:
            # Capture frame-by-frame
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture image")
                break

            # Convert the frame to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect faces in the frame
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            # Draw rectangle around the faces and save them
            for (x, y, w, h) in faces:
                # Draw rectangle around the face
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                # Extract the face
                face = frame[y:y + h, x:x + w]

                # Save the face to the list
                self.captured_faces.append(face)
                self.face_count += 1

                # Stop if we have enough faces
                if self.face_count >= self.num_faces_to_save:
                    break

            # Display the resulting frame
            cv2.imshow('Video', frame)

            # Break the loop with 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Stop if we have enough faces
            if self.face_count >= self.num_faces_to_save:
                print(f"Captured {self.face_count} faces. Stopping.")
                break

        # Release the webcam and close windows
        cap.release()
        cv2.destroyAllWindows()

        self.save_faces()

    def save_faces(self):
        # Save non-augmented faces
        for idx, face in enumerate(self.captured_faces):
            face_filename = os.path.join(self.output_dir, f"face_{idx}.jpg")
            cv2.imwrite(face_filename, face)

    def apply_augmentation(self, image, aug_type):
        if aug_type == "bright":
            return self.adjust_brightness(image, 1.5)
        elif aug_type == "dark":
            return self.adjust_brightness(image, 0.5)
        elif aug_type == "revert":
            return self.revert_colors(image)
        elif aug_type == "erase":
            return self.random_erasing(image)
        elif aug_type == "rotate":
            return self.random_rotation(image)
        else:
            return image

    def augment_faces(self):
        augmented_count = 0
        for aug_type in self.augmentation_types:
            count = 0
            for face in self.captured_faces:
                if count >= self.augmentation_limits[aug_type]:
                    break
                augmented_face = self.apply_augmentation(face, aug_type)
                face_filename = os.path.join(self.output_dir, f"{aug_type}_face_{count}.jpg")
                cv2.imwrite(face_filename, augmented_face)
                count += 1
                augmented_count += 1

        print(f"Saved {self.face_count} non-augmented and {augmented_count} augmented faces.")

    # Augmentation functions
    @staticmethod
    def adjust_brightness(image, factor):
        return cv2.convertScaleAbs(image, alpha=factor, beta=0)

    @staticmethod
    def revert_colors(image):
        return cv2.bitwise_not(image)

    @staticmethod
    def random_erasing(image):
        h, w, _ = image.shape
        x1, y1 = random.randint(0, w // 2), random.randint(0, h // 2)
        x2, y2 = random.randint(w // 2, w), random.randint(h // 2, h)
        image[y1:y2, x1:x2] = np.random.randint(0, 256, (y2 - y1, x2 - x1, 3), dtype=np.uint8)
        return image

    @staticmethod
    def random_rotation(image):
        angle = random.uniform(-10, 10)  # Small random rotation
        h, w = image.shape[:2]
        matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1)
        return cv2.warpAffine(image, matrix, (w, h))


# Example usage:
# face_capture = FaceCaptureAndAugmentation(person_ID=6420063)
# face_capture.capture_faces()
# face_capture.augment_faces()
