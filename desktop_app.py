import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import os
import sys

# Ensure root directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.detector import DetectionSystem

# Modern Color Palette
COLORS = {
    "sidebar_bg": "#F8F9FA",
    "main_bg": "#FFFFFF",
    "primary": "#1A73E8",
    "primary_hover": "#E8F0FE",
    "success": "#34A853",
    "danger": "#D93025",
    "text_main": "#202124",
    "text_secondary": "#5F6368",
    "border": "#DADCE0"
}

class FaceMaskApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Mask Detection System")
        self.root.geometry("1280x720")
        self.root.configure(bg=COLORS["main_bg"])

        self.detector = DetectionSystem()
        self.is_camera_on = False
        
        self.create_layout()
        self.show_image_mode() # Set Image Mode as Default

    def create_layout(self):
        # 1. SIDEBAR
        self.sidebar = tk.Frame(self.root, bg=COLORS["sidebar_bg"], width=260, highlightbackground=COLORS["border"], highlightthickness=1)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Sidebar Title
        tk.Label(self.sidebar, text="FACE MASK\nDETECTION", font=("Product Sans", 18, "bold"), 
                 bg=COLORS["sidebar_bg"], fg=COLORS["primary"], pady=40).pack()

        # Sidebar Buttons
        self.img_btn = tk.Button(self.sidebar, text="📁  Image Upload", font=("Roboto", 11, "bold"),
                                bg=COLORS["sidebar_bg"], fg=COLORS["text_secondary"], relief="flat", 
                                padx=20, pady=15, anchor="w", cursor="hand2", command=self.show_image_mode)
        self.img_btn.pack(fill="x", padx=10, pady=5)

        self.cam_btn_nav = tk.Button(self.sidebar, text="📷  Live Detection", font=("Roboto", 11, "bold"),
                                bg=COLORS["sidebar_bg"], fg=COLORS["text_secondary"], relief="flat", 
                                padx=20, pady=15, anchor="w", cursor="hand2", command=self.show_camera_mode)
        self.cam_btn_nav.pack(fill="x", padx=10, pady=5)

        # 2. MAIN CONTENT AREA
        self.content_area = tk.Frame(self.root, bg=COLORS["main_bg"])
        self.content_area.pack(side="right", expand=True, fill="both")
        
        self.current_frame = None

    def update_sidebar_selection(self, active_btn):
        # Reset all
        for btn in [self.img_btn, self.cam_btn_nav]:
            btn.configure(bg=COLORS["sidebar_bg"], fg=COLORS["text_secondary"])
        
        # Highlight active
        active_btn.configure(bg=COLORS["primary_hover"], fg=COLORS["primary"])

    def clear_content(self):
        if self.is_camera_on:
            self.stop_camera()
        if self.current_frame:
            self.current_frame.destroy()

    def show_image_mode(self):
        self.clear_content()
        self.update_sidebar_selection(self.img_btn)
        
        self.current_frame = tk.Frame(self.content_area, bg=COLORS["main_bg"])
        self.current_frame.pack(expand=True, fill="both", padx=40, pady=40)
        
        # Title
        tk.Label(self.current_frame, text="Analyze Image", font=("Product Sans", 22, "bold"), 
                 bg=COLORS["main_bg"], fg=COLORS["text_main"]).pack(anchor="w", pady=(0, 30))

        # Upload Area
        self.upload_area = tk.Frame(self.current_frame, bg=COLORS["sidebar_bg"], highlightbackground=COLORS["border"], highlightthickness=1)
        self.upload_area.pack(expand=True, fill="both")

        # Controls in Upload Area
        controls = tk.Frame(self.upload_area, bg=COLORS["sidebar_bg"], pady=20)
        controls.pack(fill="x", padx=20)
        
        tk.Button(controls, text="Select Image to Detect", bg=COLORS["primary"], fg="white", 
                  font=("Roboto", 11, "bold"), relief="flat", padx=25, pady=10, 
                  command=self.handle_upload).pack(side="left")
        
        self.filename_lbl = tk.Label(controls, text="No file selected", bg=COLORS["sidebar_bg"], 
                                     fg=COLORS["text_secondary"], font=("Roboto", 10))
        self.filename_lbl.pack(side="left", padx=20)

        # Image Display
        self.img_display = tk.Label(self.upload_area, text="Please upload an image to begin", 
                                    bg=COLORS["sidebar_bg"], fg=COLORS["text_secondary"], font=("Roboto", 14))
        self.img_display.pack(expand=True, fill="both", padx=20, pady=(0, 20))
        
        # Bottom Result Bar
        self.result_box = tk.Frame(self.upload_area, bg="#EEEEEE", height=70)
        self.result_box.pack(side="bottom", fill="x")
        self.result_lbl = tk.Label(self.result_box, text="DETECTION STATUS: PENDING", bg="#EEEEEE", 
                                   fg=COLORS["text_secondary"], font=("Roboto", 13, "bold"))
        self.result_lbl.pack(pady=22)

    def show_camera_mode(self):
        self.clear_content()
        self.update_sidebar_selection(self.cam_btn_nav)
        
        self.current_frame = tk.Frame(self.content_area, bg=COLORS["main_bg"])
        self.current_frame.pack(expand=True, fill="both", padx=40, pady=40)
        
        # Title
        tk.Label(self.current_frame, text="Real-time Detection", font=("Product Sans", 22, "bold"), 
                 bg=COLORS["main_bg"], fg=COLORS["text_main"]).pack(anchor="w", pady=(0, 30))

        # Main View
        self.view_container = tk.Frame(self.current_frame, bg=COLORS["main_bg"])
        self.view_container.pack(expand=True, fill="both")

        # Video
        video_wrap = tk.Frame(self.view_container, bg="black", highlightbackground=COLORS["border"], highlightthickness=1)
        video_wrap.pack(side="left", expand=True, fill="both")
        
        self.video_lbl = tk.Label(video_wrap, text="Camera Offline", bg="black", fg="#5F6368", font=("Roboto", 16))
        self.video_lbl.pack(expand=True, fill="both")
        
        # Right Control Panel
        panel = tk.Frame(self.view_container, bg=COLORS["main_bg"], width=300)
        panel.pack(side="right", fill="y", padx=(30, 0))
        
        self.cam_toggle_btn = tk.Button(panel, text="START SCANNER", bg=COLORS["success"], fg="white", 
                                 font=("Roboto", 11, "bold"), relief="flat", padx=20, pady=15, 
                                 command=self.toggle_camera)
        self.cam_toggle_btn.pack(fill="x", pady=(0, 30))
        
        # Detection Card
        card = tk.Frame(panel, bg=COLORS["sidebar_bg"], highlightbackground=COLORS["border"], highlightthickness=1, padx=25, pady=30)
        card.pack(fill="x")
        
        tk.Label(card, text="LIVE STATUS", bg=COLORS["sidebar_bg"], fg=COLORS["text_secondary"], font=("Roboto", 9, "bold")).pack()
        self.cam_status = tk.Label(card, text="READY", bg=COLORS["sidebar_bg"], fg=COLORS["text_main"], font=("Roboto", 24, "bold"))
        self.cam_status.pack(pady=15)
        self.cam_conf = tk.Label(card, text="-", bg=COLORS["sidebar_bg"], fg=COLORS["text_secondary"], font=("Roboto", 13))
        self.cam_conf.pack()

    def handle_upload(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg")])
        if not path: return
        
        self.filename_lbl.configure(text=os.path.basename(path))
        img = cv2.imread(path)
        if img is None: return
        
        annotated, status, conf, found = self.detector.processFrame(img)
        
        # Update UI
        if status == "No Face":
            color = "#EEEEEE"
            self.result_box.configure(bg=color)
            self.result_lbl.configure(text="NO FACES DETECTED", bg=color, fg=COLORS["text_secondary"])
        else:
            color = COLORS["success"] if status == "Mask" else COLORS["danger"]
            self.result_box.configure(bg=color)
            # If multiple faces were found, it might be more accurate to say 'Scan Complete' 
            # especially if there's a mix of mask/no-mask
            display_status = status.upper() if status == "Mask" else "NO MASK DETECTED"
            self.result_lbl.configure(text=f"DETECTED: {display_status} ({conf:.1f}%)", bg=color, fg="white")
        
        # Show Image
        rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        
        w, h = self.img_display.winfo_width(), self.img_display.winfo_height()
        if w > 10 and h > 10:
            pil_img.thumbnail((w, h))
        
        tk_img = ImageTk.PhotoImage(pil_img)
        self.img_display.configure(image=tk_img, text="")
        self.img_display.image = tk_img

    def toggle_camera(self):
        if not self.is_camera_on:
            self.is_camera_on = True
            self.cam_toggle_btn.configure(text="STOP SCANNER", bg=COLORS["danger"])
            self.detector.startRealTimeDetection()
            self.update_video()
        else:
            self.stop_camera()

    def stop_camera(self):
        self.is_camera_on = False
        self.cam_toggle_btn.configure(text="START SCANNER", bg=COLORS["success"])
        self.cam_status.configure(text="READY", fg=COLORS["text_main"])
        self.cam_conf.configure(text="-")
        self.video_lbl.configure(image="", text="Camera Offline")
        self.detector.cameraManager.stopCamera()

    def update_video(self):
        if self.is_camera_on:
            frame = self.detector.cameraManager.getFrame()
            if frame is not None:
                annotated, status, conf, found = self.detector.processFrame(frame)
                
                if status == "No Face":
                    self.cam_status.configure(text="SCANNING...", fg=COLORS["text_secondary"])
                    self.cam_conf.configure(text="No faces detected")
                else:
                    color = COLORS["success"] if status == "Mask" else COLORS["danger"]
                    self.cam_status.configure(text=status.upper(), fg=color)
                    self.cam_conf.configure(text=f"Confidence: {conf:.1f}%")
                
                rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb)
                
                w, h = self.video_lbl.winfo_width(), self.video_lbl.winfo_height()
                if w > 10 and h > 10:
                    pil_img.thumbnail((w, h))
                
                tk_img = ImageTk.PhotoImage(pil_img)
                self.video_lbl.configure(image=tk_img)
                self.video_lbl.image = tk_img
            
            self.root.after(10, self.update_video)

if __name__ == "__main__":
    root = tk.Tk()
    def on_closing():
        sys.exit()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    app = FaceMaskApp(root)
    root.mainloop()
