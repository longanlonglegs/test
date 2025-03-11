import os
import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks import python

# Check if the model exists
model_path = os.path.abspath(r"test\uplink\src\bright.task")
if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model file not found at {model_path}")

# Create a GestureRecognizer object
recognizer = vision.GestureRecognizer.create_from_model_path(model_path)

# Initialize webcam
cap = cv2.VideoCapture(0)  # 0 is usually the default webcam

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

print("Press 'q' to quit.")

def process_frame(frame):
    """
    Process each frame for gesture recognition.
    """
    # Convert the frame to the format required by MediaPipe (MP Image)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)

    # Run gesture recognition
    recognition_result = recognizer.recognize(mp_image)

    # Check if gestures are recognized
    if recognition_result.gestures and recognition_result.gestures[0]:
        top_gesture = recognition_result.gestures[0][0]
        # Display the gesture name and score
        gesture_text = f"Gesture: {top_gesture.category_name} ({top_gesture.score:.2f})"
        print(gesture_text)
        cv2.putText(frame, gesture_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    else:
        cv2.putText(frame, "No gesture recognized", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    return frame

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame.")
        break

    # Process the frame (gesture recognition)
    processed_frame = process_frame(frame)

    # Display the processed frame
    cv2.imshow('Processed Stream', processed_frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()