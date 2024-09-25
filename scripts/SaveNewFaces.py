import cv2
import os
import numpy as np
import random

# Prompt for the person's name
person_name = input("Enter the name of the person: ")

# Create a directory to save the faces
output_dir = os.path.join("data/dataset_faces", person_name)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Initialize the webcam
cap = cv2.VideoCapture(0)

# Load the Haar cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml') #openCV

# Counter for saved faces
face_count = 0

# Number of non-augmentation faces to save
num_faces_to_save = 500
captured_faces = []

# Capture faces
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture image")
        break

    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces in the frame
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # Draw rectangle around the faces and save them
    for (x, y, w, h) in faces:
        # Draw rectangle around the face
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # Extract the face
        face = frame[y:y + h, x:x + w]

        # Save the face to the list
        captured_faces.append(face)
        face_count += 1

        # Stop if we have enough faces
        if face_count >= num_faces_to_save:
            break

    # Display the resulting frame
    cv2.imshow('Video', frame)

    # Break the loop with 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    # Stop if we have enough faces
    if face_count >= num_faces_to_save:
        print(f"Captured {face_count} faces. Stopping.")
        break

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()

# Save non-augmented faces
for idx, face in enumerate(captured_faces):
    face_filename = os.path.join(output_dir, f"face_{idx}.jpg")
    cv2.imwrite(face_filename, face)

# Augmentation functions
def adjust_brightness(image, factor):
    return cv2.convertScaleAbs(image, alpha=factor, beta=0)

def revert_colors(image):
    return cv2.bitwise_not(image)

def random_erasing(image):
    h, w, _ = image.shape
    x1, y1 = random.randint(0, w // 2), random.randint(0, h // 2)
    x2, y2 = random.randint(w // 2, w), random.randint(h // 2, h)
    image[y1:y2, x1:x2] = np.random.randint(0, 256, (y2 - y1, x2 - x1, 3), dtype=np.uint8)
    return image

def random_rotation(image):
    angle = random.uniform(-10, 10)  # Small random rotation
    h, w = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1)
    return cv2.warpAffine(image, matrix, (w, h))

# Augmentation selection function
def apply_augmentation(image, aug_type):
    if aug_type == "bright":
        return adjust_brightness(image, 1.5)
    elif aug_type == "dark":
        return adjust_brightness(image, 0.5)
    elif aug_type == "revert":
        return revert_colors(image)
    elif aug_type == "erase":
        return random_erasing(image)
    elif aug_type == "rotate":
        return random_rotation(image)
    else:
        return image

# Define augmentation types

# Adjust number of augmentation images
augmentation_types = ["bright", "dark", "revert", "erase", "rotate"]
augmentation_limits = {aug: 100 for aug in augmentation_types}

# Perform augmentations
augmented_count = 0
for aug_type in augmentation_types:
    count = 0
    for face in captured_faces:
        if count >= augmentation_limits[aug_type]:
            break
        augmented_face = apply_augmentation(face, aug_type)
        face_filename = os.path.join(output_dir, f"{aug_type}_face_{count}.jpg")
        cv2.imwrite(face_filename, augmented_face)
        count += 1
        augmented_count += 1

print(f"Saved {face_count} non-augmented and {augmented_count} augmented faces.")
