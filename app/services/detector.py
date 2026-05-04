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
    def __init__(self):
        # Setup MediaPipe face detection
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detector = self.mp_face_detection.FaceDetection(
            model_selection=1,  # 1 for full range (within 5 meters), 0 for short range (within 2 meters)
            min_detection_confidence=0.5
        )
        print('Face Detection model (MediaPipe) loaded successfully!')

    def detectFaces(self, image):
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
    def __init__(self):
        self.IMG_SIZE = (224, 224) # MobileNetV2 standard input size
        self.MODEL_PATH = os.path.join(os.path.dirname(__file__), 'face_mask_detector_mobile-net-v2_model.keras')

        print('Loading CNN model from:', self.MODEL_PATH)
        self.cnnModel = tf.keras.models.load_model(self.MODEL_PATH, compile=False)
        print('CNN model loaded successfully!')

    def preprocess_image(self, face_img): # Preprocess single face image for MobileNetV2
        face_img = cv2.resize(face_img, self.IMG_SIZE)
        face_img = face_img.astype("float32")
        face_img = face_img / 255.0 # Normalize to [0, 1] range
        face_img = np.expand_dims(face_img, axis=0) # Add batch dimension
        return face_img

    def classifyMaskStatus(self, face_images):
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
        
        overall_status = "No Face" 
        highest_conf = 0
        
        if coords:
            overall_status = "Mask" # Reset to Mask if faces found, will change to No Mask if any face has no mask
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