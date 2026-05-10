import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
from app.models.db import DatabaseManager
import os
import uuid
import time

# Detect faces using MediaPipe
class FaceDetector:
    """
    Handles face localization using the MediaPipe Face Detection solution.
    """
    def __init__(self):
        # Setup MediaPipe face detection
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detector = self.mp_face_detection.FaceDetection(
            model_selection=1,  # 1 for full range (within 5 meters), 0 for short range (within 2 meters)
            min_detection_confidence=0.5
        )
        print('Face Detection model (MediaPipe) loaded successfully!')

    def detectFaces(self, image):
        """
        Detects faces in an image and returns their bounding box coordinates.
        
        Args:
            image (numpy.ndarray): The input BGR image.
            
        Returns:
            list: A list of tuples (xmin, ymin, xmax, ymax) for each detected face.
        """
        h, w, _ = image.shape
        rgb_frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_detector.process(rgb_frame)

        coordinates = []
        if results.detections:
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                bw = int(bbox.width * w)
                bh = int(bbox.height * h)
                
                # Boundary clipping
                x = max(0, x)
                y = max(0, y)
                
                # Clamp to image bounds
                x_max = min(w, x + bw)
                y_max = min(h, y + bh)
                
                if x_max > x and y_max > y:
                    coordinates.append((x, y, x_max, y_max))
        
        return coordinates


# Class to handle CNN model loading and prediction
class CNNModel:
    """
    Handles the loading and execution of the pre-trained Keras model for 
    face mask classification.
    """
    def __init__(self):
        self.IMG_SIZE = (224, 224) # MobileNetV2 standard input size
        self.MODEL_PATH = os.path.join(os.path.dirname(__file__), 'face_mask_detector_mobile-net-v2_model.keras')

        print('Loading CNN model from:', self.MODEL_PATH)
        self.cnnModel = tf.keras.models.load_model(self.MODEL_PATH, compile=False)
        print('CNN model loaded successfully!')

    def preprocess_image(self, face_img):
        """
        Prepares a single face ROI for input into the MobileNetV2 model.
        
        Args:
            face_img (numpy.ndarray): The cropped face image.
            
        Returns:
            numpy.ndarray: Preprocessed image with normalized pixels and batch dimension.
        """
        face_img = cv2.resize(face_img, self.IMG_SIZE)
        face_img = face_img.astype("float32")
        face_img = face_img / 255.0 # Normalize to [0, 1] range
        face_img = np.expand_dims(face_img, axis=0) # Add batch dimension
        return face_img

    def classifyMaskStatus(self, face_images):
        """
        Classifies multiple face images as 'Mask' or 'No Mask'.
        
        Args:
            face_images (list): List of cropped face images (numpy arrays).
            
        Returns:
            list: List of tuples (label, confidence_percentage) for each face.
        """
        predictions = []

        for face in face_images:
            face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            face = cv2.resize(face, (224, 224))
            face = np.expand_dims(face, axis=0)  # Model expects (1, 224, 224, 3)
            
            # Prediction logic - using the same as your working code
            prediction = self.cnnModel.predict(face, verbose=0)[0][0]
            label = "No Mask" if prediction >= 0.7 else "Mask"
            conf = prediction if label == "No Mask" else 1 - prediction
            
            predictions.append((label, float(conf * 100)))

        return predictions


# Class to manage camera operations
class CameraManager:
    """
    Manages webcam access and frame acquisition using OpenCV.
    """
    def __init__(self):
        self.camera = None

    def startCamera(self):
        """
        Initializes and opens the default system camera.
        """
        if self.camera is None or not self.camera.isOpened():
            self.camera = cv2.VideoCapture(0)

    def stopCamera(self):
        """
        Releases the camera resource and closes the device.
        """
        if self.camera is not None:
            self.camera.release()
            self.camera = None

    def getFrame(self):
        """
        Captures a single frame from the active camera.
        
        Returns:
            numpy.ndarray: The captured BGR frame, or None if unsuccessful.
        """
        if self.camera is not None and self.camera.isOpened():
            success, frame = self.camera.read()
            if success:
                return frame
        return None


# MAIN CLASS TO MANAGE DETECTION, DATABASE, AND IMAGE HANDLING
class DetectionSystem:
    """
    Orchestrates the entire face mask detection pipeline, integrating the camera,
    face detector, CNN classifier, and database manager.
    """
    def __init__(self):
        self.cameraManager = CameraManager()
        self.faceDetector = FaceDetector()
        self.cnnModel = CNNModel()
        self.dbManager = DatabaseManager()
        
        self.base_upload_path = os.path.join(os.path.dirname(__file__), '../static/uploads')
        os.makedirs(os.path.join(self.base_upload_path, 'mask'), exist_ok=True)
        os.makedirs(os.path.join(self.base_upload_path, 'no-mask'), exist_ok=True)
        
        self.last_db_save_time = 0

    def _save_face_roi(self, frame, xmin, ymin, xmax, ymax, label, conf, source):
        """
        Crops a face ROI from a frame, saves it to disk, and records it in the database.
        
        Args:
            frame (numpy.ndarray):          The full image frame.
            xmin, ymin, xmax, ymax (int):   Bounding box coordinates.
            label (str):                    Classification label ('Mask' or 'No Mask').
            conf (float):                   Confidence score.
            source (str):                   Source identifier for the record.
            
        Returns:
            str: Relative database path to the saved image, or None if ROI was empty.
        """
        # Crop ROI
        roi = frame[ymin:ymax, xmin:xmax]
        if roi.size == 0:
            return None
        
        output_filename = f"{uuid.uuid4().hex}.jpg"
        folder = "mask" if label == "Mask" else "no-mask"
        save_path = os.path.join(self.base_upload_path, folder, output_filename)
        
        # Store cropped ROI instead of the whole image
        cv2.imwrite(save_path, roi)
        
        db_path = f"uploads/{folder}/{output_filename}"
        self.dbManager.storeRecord(label, conf, db_path, source)
        return db_path

    def save_results(self, frame, face_results, source):
        """Helper to save multiple face ROIs and their DB records."""
        db_paths = []
        for (xmin, ymin, xmax, ymax), label, conf in face_results:
            path = self._save_face_roi(frame, xmin, ymin, xmax, ymax, label, conf, source)
            if path:
                db_paths.append(path)
        return db_paths

    def processFrame(self, frame_bgr):
        """
        Runs the full detection pipeline on a single BGR frame.
        
        Args:
            frame_bgr (numpy.ndarray): The input image frame.
            
        Returns:
            tuple: (annotated_frame, overall_status, highest_conf, face_results)
        """
        # Create a copy for drawing
        annotated_frame = frame_bgr.copy()
        coords = self.faceDetector.detectFaces(frame_bgr)
        
        overall_status = "No Face" 
        highest_conf = 0
        face_results = [] # Detailed results for each face: ((xmin, ymin, xmax, ymax), label, conf)
        
        if coords:
            overall_status = "Mask" # Default to Mask, will change to No Mask if any face has no mask
            faces = [frame_bgr[y1:y2, x1:x2] for x1, y1, x2, y2 in coords]
            predictions = self.cnnModel.classifyMaskStatus(faces)
            
            for (xmin, ymin, xmax, ymax), (label, conf) in zip(coords, predictions):
                color = (0, 255, 0) if label == "Mask" else (0, 0, 255)
                
                # Ensure label box fits on screen
                y_label = ymin - 10 if ymin - 10 > 10 else ymin + 20
                text = f"{label}: {conf:.2f}%"
                cv2.rectangle(annotated_frame, (xmin, ymin), (xmax, ymax), color, 2)
                cv2.putText(annotated_frame, text, (xmin, y_label), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # Add to detailed results
                face_results.append(((xmin, ymin, xmax, ymax), label, conf))
                
                # Keep stats for UI
                if label == "No Mask":
                    overall_status = "No Mask"
                highest_conf = max(highest_conf, conf)

        return annotated_frame, overall_status, highest_conf, face_results

    def uploadImage(self, image_bytes):
        """
        Processes an uploaded image byte stream.
        
        Args:
            image_bytes (bytes): Raw image data from file upload.
            
        Returns:
            tuple: (annotated_bytes, overall_status, highest_conf, db_path, total_faces, masks_count)
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        annotated_frame, status, conf, face_results = self.processFrame(img)
        
        # Calculate counts
        total_faces = len(face_results)
        masks_count = sum(1 for _, label, _ in face_results if label == "Mask")
        
        # Save each face ROI and add to DB
        db_paths = self.save_results(img, face_results, "Image Upload")
            
        # For the web response, we use the first path or a placeholder if multiple (the web UI expects one path)
        main_db_path = db_paths[0] if db_paths else ""
        
        # Encode annotated for viewing
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        return buffer.tobytes(), status, conf, main_db_path, total_faces, masks_count

    def startRealTimeDetection(self):
        """
        Prepares the system for real-time camera processing.
        """
        self.cameraManager.startCamera()

    def get_realtime_frame(self):
        """
        Captures and processes a single frame for real-time streaming,
        handling throttling for database storage.
        
        Returns:
            bytes: Encoded JPEG image data for the processed frame.
        """
        frame = self.cameraManager.getFrame()
        if frame is None:
            return None
        
        annotated_frame, status, conf, face_results = self.processFrame(frame)
        
        # Save every 5 seconds to prevent spam
        current_time = time.time()
        if face_results and (current_time - self.last_db_save_time > 5):
            self.last_db_save_time = current_time
            self.save_results(frame, face_results, "Live Camera")
            
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        return buffer.tobytes()