import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk # Used to bridge OpenCV images with Tkinter widgets
import cv2
import os
import sys
import time

# Ensure root directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.detector import DetectionSystem

# Minimalist Color Palette
COLORS = {
    "bg": "#FFFFFF",
    "header_bg": "#F8F9FA",
    "primary": "#1A73E8",
    "primary_hover": "#E8F0FE",
    "text": "#202124",
    "text_secondary": "#5F6368",
    "border": "#DADCE0",
    "success": "#34A853",
    "danger": "#D93025"
}

class FaceMaskApp:
    """
    A Tkinter-based desktop application for real-time face mask detection.
    Supports both static image analysis and live webcam monitoring.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Face Mask Detector")
        self.root.geometry("1100x800")
        self.root.configure(bg=COLORS["bg"])

        self.detector = DetectionSystem()
        self.is_camera_on = False
        
        self.create_layout()
        self.show_image_mode()

    def create_layout(self):
        """
        Initializes the application layout, including the navigation header,
        main viewport, and bottom status bar.
        """
        # 1. TOP HEADER (Navigation)
        self.header = tk.Frame(self.root, bg=COLORS["header_bg"], height=70, highlightbackground=COLORS["border"], highlightthickness=1)
        self.header.pack(side="top", fill="x")
        self.header.pack_propagate(False)

        # Title on Left
        tk.Label(self.header, text="Face Mask Detector", font=("Product Sans", 14, "bold"), 
                 bg=COLORS["header_bg"], fg=COLORS["primary"], padx=20).pack(side="left")

        # Nav Buttons Container
        nav_container = tk.Frame(self.header, bg=COLORS["header_bg"])
        nav_container.pack(side="right", padx=20)

        self.img_btn = tk.Button(nav_container, text="Image Analysis", font=("Roboto", 10, "bold"),
                                bg=COLORS["header_bg"], fg=COLORS["text_secondary"], relief="flat", 
                                padx=20, pady=10, cursor="hand2", command=self.show_image_mode)
        self.img_btn.pack(side="left", padx=5)

        self.cam_btn = tk.Button(nav_container, text="Live Webcam", font=("Roboto", 10, "bold"),
                                bg=COLORS["header_bg"], fg=COLORS["text_secondary"], relief="flat", 
                                padx=20, pady=10, cursor="hand2", command=self.show_camera_mode)
        self.cam_btn.pack(side="left", padx=5)

        # 2. MAIN VIEWPORT
        self.content_area = tk.Frame(self.root, bg=COLORS["bg"])
        self.content_area.pack(expand=True, fill="both", padx=30, pady=20)
        
        # 3. STATS BAR (BOTTOM)
        self.stats_bar = tk.Frame(self.root, bg=COLORS["header_bg"], height=50, highlightbackground=COLORS["border"], highlightthickness=1)
        self.stats_bar.pack(side="bottom", fill="x")
        self.stats_bar.pack_propagate(False)

        self.stats_lbl = tk.Label(self.stats_bar, text="Ready to scan", font=("Roboto", 10, "bold"),
                                 bg=COLORS["header_bg"], fg=COLORS["text_secondary"])
        self.stats_lbl.pack(expand=True)

        self.current_frame = None

    def update_nav(self, active_btn):
        """
        Updates the UI state of the navigation buttons to highlight the active mode.
        
        Args:
            active_btn (tk.Button): The button representing the current active mode.
        """
        for btn in [self.img_btn, self.cam_btn]:
            btn.configure(bg=COLORS["header_bg"], fg=COLORS["text_secondary"])
        active_btn.configure(bg=COLORS["primary_hover"], fg=COLORS["primary"])

    def clear_content(self):
        """
        Cleans up the main viewport and stops the camera if it's currently running.
        """
        if self.is_camera_on:
            self.stop_camera()
        if self.current_frame:
            self.current_frame.destroy()

    def show_image_mode(self):
        """
        Configures the UI for the static image analysis mode.
        """
        self.clear_content()
        self.update_nav(self.img_btn)
        
        self.current_frame = tk.Frame(self.content_area, bg=COLORS["bg"])
        self.current_frame.pack(expand=True, fill="both")
        
        # Upload Button
        tk.Button(self.current_frame, text="Select Image", bg=COLORS["primary"], fg="white", 
                  font=("Roboto", 10, "bold"), relief="flat", padx=30, pady=12, 
                  command=self.handle_upload).pack(pady=(0, 20))

        # Image Display Area
        self.display = tk.Label(self.current_frame, text="No image selected", 
                               bg="#F1F3F4", fg=COLORS["text_secondary"], font=("Roboto", 12),
                               highlightbackground=COLORS["border"], highlightthickness=1)
        self.display.pack(expand=True, fill="both")

    def show_camera_mode(self):
        """
        Configures the UI for the real-time camera monitoring mode.
        """
        self.clear_content()
        self.update_nav(self.cam_btn)
        
        self.current_frame = tk.Frame(self.content_area, bg=COLORS["bg"])
        self.current_frame.pack(expand=True, fill="both")

        # Camera Display
        self.display = tk.Label(self.current_frame, text="Camera Offline", 
                               bg="black", fg="#5F6368", font=("Roboto", 14),
                               highlightbackground=COLORS["border"], highlightthickness=1)
        self.display.pack(expand=True, fill="both", pady=(0, 20))

        # Toggle Button
        self.toggle_btn = tk.Button(self.current_frame, text="Start Camera", bg=COLORS["success"], fg="white", 
                                   font=("Roboto", 10, "bold"), relief="flat", padx=40, pady=12, 
                                   command=self.toggle_camera)
        self.toggle_btn.pack()

    def handle_upload(self):
        """
        Opens a file dialog to select an image, processes it for face mask detection,
        and displays the annotated result.
        """
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg")])
        if not path: return
        
        img = cv2.imread(path)
        if img is None: return
        
        annotated, status, conf, face_results = self.detector.processFrame(img)
        self.detector.save_results(img, face_results, "Image Upload")
        
        # Stats
        total = len(face_results)
        masks = sum(1 for _, l, _ in face_results if l == "Mask")
        self.stats_lbl.configure(text=f"Faces Found: {total} | Masks Detected: {masks} | Status: {status.upper()}", fg=COLORS["primary"])
        
        # Show
        self.update_display(annotated)

    def toggle_camera(self):
        """
        Starts or stops the live webcam feed based on the current state.
        """
        if not self.is_camera_on:
            self.is_camera_on = True
            self.toggle_btn.configure(text="Stop Camera", bg=COLORS["danger"])
            self.detector.startRealTimeDetection()
            self.update_video()
        else:
            self.stop_camera()

    def stop_camera(self):
        """
        Safely stops the camera feed and updates the UI to an offline state.
        """
        self.is_camera_on = False
        if hasattr(self, 'toggle_btn'):
            self.toggle_btn.configure(text="Start Camera", bg=COLORS["success"])
        self.stats_lbl.configure(text="Camera Stopped", fg=COLORS["text_secondary"])
        self.display.configure(image="", text="Camera Offline")
        self.detector.cameraManager.stopCamera()

    def update_video(self):
        """
        Continuously captures frames from the webcam, processes them, and 
        updates the display in a loop using the Tkinter event loop.
        """
        if self.is_camera_on:
            frame = self.detector.cameraManager.getFrame()
            if frame is not None:
                annotated, status, conf, face_results = self.detector.processFrame(frame)
                
                # Auto-save logic
                current_time = time.time()
                if face_results and (current_time - self.detector.last_db_save_time > 5):
                    self.detector.last_db_save_time = current_time
                    self.detector.save_results(frame, face_results, "Live Camera")
                
                # Update Stats
                total = len(face_results)
                masks = sum(1 for _, l, _ in face_results if l == "Mask")
                self.stats_lbl.configure(text=f"Live Stats - Faces: {total} | Masks: {masks} | Status: {status.upper()}", fg=COLORS["primary"])
                
                self.update_display(annotated)
            
            self.root.after(10, self.update_video)

    def update_display(self, frame):
        """
        Converts a BGR image array into a format compatible with Tkinter
        and updates the central display widget.
        
        Args:
            frame (numpy.ndarray): The BGR image frame to display.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        
        # Dynamic resizing to fit display area
        w, h = self.display.winfo_width(), self.display.winfo_height()
        if w > 10 and h > 10:
            pil_img.thumbnail((w, h))
        
        tk_img = ImageTk.PhotoImage(pil_img)
        self.display.configure(image=tk_img, text="")
        self.display.image = tk_img

if __name__ == "__main__":
    root = tk.Tk()
    def on_closing():
        sys.exit()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    app = FaceMaskApp(root)
    root.mainloop()
