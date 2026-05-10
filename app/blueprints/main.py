from flask import Blueprint, render_template, Response, redirect, request, url_for, flash
from app.services.detector import DetectionSystem
import base64 # For encoding processed images for HTML display

main_bp = Blueprint('main', __name__)

# Initialize the detection system globally for eager loading
detector_system = DetectionSystem()

@main_bp.route('/')
def index():
    """
    Renders the landing page of the application.
    
    Returns:
        str: Rendered HTML for the index page.
    """
    return render_template('index.html')

@main_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    """
    Handles image uploads for face mask detection.
    
    In POST: Processes the uploaded image and displays detection results.
    In GET: Renders the upload form page.
    
    Returns:
        str: Rendered HTML for the upload page with or without results.
    """
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        
        file = request.files.get('file')
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
            
        if file:
            try:
                system = detector_system
                image_bytes = file.read()
                annotated_bytes, status, conf, _, total_faces, masks_count = system.uploadImage(image_bytes)
                
                # Convert back to base64 to show immediately on the page without another request
                encoded_img = base64.b64encode(annotated_bytes).decode('utf-8')
                
                flash('Image processed successfully', 'success')
                return render_template('upload.html', 
                                     result_image=encoded_img, 
                                     status=status, 
                                     confidence=conf,
                                     total_faces=total_faces,
                                     masks_count=masks_count)
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'error')
                return redirect(request.url)
                
    return render_template('upload.html')

@main_bp.route('/webcam')
def webcam():
    """
    Renders the real-time webcam detection page.
    
    Returns:
        str: Rendered HTML for the webcam monitoring page.
    """
    return render_template('webcam.html')

def gen_frames():
    """
    Generator function that captures frames from the camera system and yields 
    them as a multipart/x-mixed-replace stream for the browser.
    
    Yields:
        bytes: JPEG image frame formatted as a multipart response chunk.
    """
    system = detector_system
    system.startRealTimeDetection()
    
    try:
        while True:
            frame_bytes = system.get_realtime_frame()
            if frame_bytes is None:
                break
            # yield 'pauses' here, sends the frame to the browser, and waits to be called again for the next frame.
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        system.cameraManager.stopCamera()

@main_bp.route('/video_feed')
def video_feed():
    """
    Endpoint for the video streaming feed used in the webcam page.
    
    Returns:
        Response: A Flask Response object streaming multipart JPEG frames.
    """
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')