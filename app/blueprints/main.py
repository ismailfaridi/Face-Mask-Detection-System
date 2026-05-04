from flask import Blueprint, render_template, request, Response, flash, redirect, url_for
from app.services.detector import DetectionSystem
import base64

main_bp = Blueprint('main', __name__)

# Initialize system lazily or globally
detector_system = None

def get_system():
    global detector_system
    if detector_system is None:
        detector_system = DetectionSystem()
    return detector_system

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
            
        if file:
            try:
                system = get_system()
                image_bytes = file.read()
                annotated_bytes, status, conf, _ = system.uploadImage(image_bytes)
                
                # Convert back to base64 to show immediately on the page without another request
                encoded_img = base64.b64encode(annotated_bytes).decode('utf-8')
                
                flash('Image processed successfully', 'success')
                return render_template('upload.html', 
                                     result_image=encoded_img, 
                                     status=status, 
                                     confidence=conf)
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'error')
                return redirect(request.url)
                
    return render_template('upload.html')

@main_bp.route('/webcam')
def webcam():
    return render_template('webcam.html')

def gen_frames():
    system = get_system()
    system.startRealTimeDetection()
    try:
        while True:
            frame_bytes = system.get_realtime_frame()
            if frame_bytes is None:
                break
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        system.cameraManager.stopCamera()

@main_bp.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')