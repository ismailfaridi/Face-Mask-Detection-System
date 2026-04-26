import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
# from app.models.db import DatabaseManager
import os
import uuid
import datetime
import time

# Detect faces using MediaPipe
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class FaceDetector:
    def __init__(self):
        self.MODEL_PATH = os.path.join('./blaze_face_full_range.tflite') # os.path.join(os.path.dirname(__file__), 'blaze_face_full_range.tflite')

        base_options = python.BaseOptions(model_asset_path=self.MODEL_PATH)
        options = vision.FaceDetectorOptions(
            base_options=base_options,
            min_detection_confidence=0.5,   # Adjust threshold (0.0 to 1.0)
            min_suppression_threshold=0.3   # Prevents overlapping boxes
        )

        # Initialize the Face Detector
        self.face_detection = vision.FaceDetector.create_from_options(options)
        print('✅ Face Detection model loaded successfully!')

    def detectFaces(self, image):
        # MediaPipe expects RGB via mp.Image
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb) # Convert image (typically numpy array) to MediaPipe image object to process with the model
        
        # Run face detection
        results = self.face_detection.detect(mp_image)
        
        coordinates = []
        if results.detections:
            h, w, _ = image.shape
            for detection in results.detections:
                bbox = detection.bounding_box
                xmin = int(bbox.origin_x)
                ymin = int(bbox.origin_y)
                width = int(bbox.width)
                height = int(bbox.height)
                
                # Expand box slightly and clamp coordinates (box never goes out of image bounds)
                ymin = max(0, ymin - 10)
                xmin = max(0, xmin - 10)
                ymax = min(h, ymin + height + 20)
                xmax = min(w, xmin + width + 20)
                
                if xmax > xmin and ymax > ymin:
                    coordinates.append((xmin, ymin, xmax, ymax))
        return coordinates


# Class to handle CNN model loading and prediction
class CNNModel:
    def __init__(self):
        self.IMG_SIZE = (224, 224) # MobileNetV2 standard input size
        self.MODEL_PATH = './face_mask_detector_mobile-net-v2_model.keras' # os.path.join(os.path.dirname(__file__), '../../face_mask_detector_mobile-net-v2_model.keras')

        print('📦 Loading CNN model from:', self.MODEL_PATH)
        self.cnnModel = tf.keras.models.load_model(self.MODEL_PATH)
        print('✅ CNN model loaded successfully!')

    def preprocess(self, face_img): # Preprocess single face image for MobileNetV2
        face_img = cv2.resize(face_img, self.IMG_SIZE)
        face_img = face_img.astype("float32")
        # Normalize (common for MobileNetV2)
        face_img = face_img / 255.0
        # Add batch dimension
        face_img = np.expand_dims(face_img, axis=0)
        return face_img

    def classifyMaskStatus(self, face_images):
        predictions = []
        for face in face_images:
            face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            face = cv2.resize(face, (224, 224))
            # Model specific preprocessing based on MobileNetV2 (typically -1 to 1) or /255
            # We will use /255 as it's common for custom models trained on mask data unless MobileNetV2 preprocess input is required
            face = tf.keras.applications.mobilenet_v2.preprocess_input(face)
            face = np.expand_dims(face, axis=0)
            
            pred = self.cnnModel.predict(face, verbose=0)[0][0]
            # Output node might be sigmoid where 0=Mask, 1=No Mask, or vice-versa
            # Assuming standard threshold 0.5. 
            # We'll need to interpret it. Let's assume sigmoid returning probability of 'No Mask' if trained that way,
            # or probability of 'Mask'. We'll adjust as needed. Often it's probability of Without Mask.
            # For this context, let's say < 0.5 is Mask, > 0.5 is No Mask.
            label = "Mask" if pred < 0.5 else "No Mask"
            confidence = (1 - pred) if label == "Mask" else pred
            predictions.append((label, float(confidence * 100)))
        return predictions


# 
class CameraManager:
    def __init__(self):
        self.camera = None

    def startCamera(self):
        if self.camera is None or not self.camera.isOpened():
            self.camera = cv2.VideoCapture(0)

    def stopCamera(self):
        if self.camera is not None:
            self.camera.release()
            self.camera = None

    def getFrame(self):
        if self.camera is not None and self.camera.isOpened():
            success, frame = self.camera.read()
            if success:
                return frame
        return None


# MAIN CLASS TO MANAGE DETECTION, DATABASE, AND IMAGE HANDLING
class DetectionSystem:
    def __init__(self):
        self.cameraManager = CameraManager()
        self.faceDetector = FaceDetector()
        self.cnnModel = CNNModel()
        self.dbManager = DatabaseManager()
        
        self.base_upload_path = os.path.join(os.path.dirname(__file__), '../static/uploads')
        os.makedirs(os.path.join(self.base_upload_path, 'mask'), exist_ok=True)
        os.makedirs(os.path.join(self.base_upload_path, 'no-mask'), exist_ok=True)
        
        self.last_db_save_time = 0

    def processFrame(self, frame_bgr):
        # Create a copy for drawing
        annotated_frame = frame_bgr.copy()
        coords = self.faceDetector.detectFaces(frame_bgr)
        
        overall_status = "Mask" # default
        highest_conf = 0
        
        if coords:
            faces = [frame_bgr[y1:y2, x1:x2] for x1, y1, x2, y2 in coords]
            predictions = self.cnnModel.classifyMaskStatus(faces)
            
            for (xmin, ymin, xmax, ymax), (label, conf) in zip(coords, predictions):
                color = (0, 255, 0) if label == "Mask" else (0, 0, 255)
                
                # Ensure label box fits on screen
                y_label = ymin - 10 if ymin - 10 > 10 else ymin + 20
                text = f"{label}: {conf:.2f}%"
                cv2.rectangle(annotated_frame, (xmin, ymin), (xmax, ymax), color, 2)
                cv2.putText(annotated_frame, text, (xmin, y_label), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # Keep stats for saving
                if label == "No Mask":
                    overall_status = "No Mask"
                highest_conf = max(highest_conf, conf)

        return annotated_frame, overall_status, highest_conf, len(coords) > 0

    def uploadImage(self, image_bytes):
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        annotated_frame, status, conf, face_found = self.processFrame(img)
        
        output_filename = f"{uuid.uuid4().hex}.jpg"
        folder = "mask" if status == "Mask" else "no-mask"
        
        save_path = os.path.join(self.base_upload_path, folder, output_filename)
        # Store original image as requested: "stored images should be original image not the annotated one"
        cv2.imwrite(save_path, img) 
        
        db_path = f"uploads/{folder}/{output_filename}"
        
        if face_found:
            self.dbManager.storeRecord(status, conf, db_path, "uploadimage")
            
        # Encode annotated for viewing
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        return buffer.tobytes(), status, conf, db_path

    def startRealTimeDetection(self):
        self.cameraManager.startCamera()

    def get_realtime_frame(self):
        frame = self.cameraManager.getFrame()
        if frame is None:
            return None
        
        annotated_frame, status, conf, face_found = self.processFrame(frame)
        
        # Save every 5 seconds to prevent spam
        current_time = time.time()
        if face_found and (current_time - self.last_db_save_time > 5):
            self.last_db_save_time = current_time
            output_filename = f"{uuid.uuid4().hex}.jpg"
            folder = "mask" if status == "Mask" else "no-mask"
            save_path = os.path.join(self.base_upload_path, folder, output_filename)
            
            # Store original 
            cv2.imwrite(save_path, frame)
            db_path = f"uploads/{folder}/{output_filename}"
            self.dbManager.storeRecord(status, conf, db_path, "webcam")
            
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        return buffer.tobytes()

import time