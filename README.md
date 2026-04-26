# Face-Mask-Detection-System
This project aims to develop an automated face mask detection system using deep learning techniques. The system will identify whether a person in an image is wearing a mask or not wearing a mask. A Convolutional Neural Network (CNN) model will be trained on a dataset containing face images with and without masks.

**Playlist:** https://www.youtube.com/playlist?list=PLEQQipl_9di-GzYMfJdXOZIV_9mLdbP2N

````bash
python -m venv myenv # py -3.10 -m venv myenv310
env\Scripts\activate
pip install flask


pip install tensorflow==2.15.0
pip install mediapipe==0.10.11
pip install opencv-python==4.9.0.80
pip install flask==3.0.0

# pip uninstall numpy -y # 2.2.6 (not compatiable with tensorflow)
# pip install numpy==1.26.4


pip freeze > requirements.txt

--
pip install -r requirements.txt
```

WORK DONE:
- run.py
- app/__init__.py
- app/services/detector.py (continue...)
REMAINING:
- SQLite3 DB for detection & admin
- Blueprints
- Add dot-env pkg into requirement.txt



notes::::
Pages/Routes:
- Homepage with two options upload image, and Start-real time detection, and below these option put some text about the tool and how you can use it.
- By clicking on upload image, and start real time detection, a new page for each of them shows where the results image/live detection with bounding box shows with confidence interval. Note for the small images that only has face it become very hard to detect face region and put confidence interval bez it go out of image, so kindly handle it.
- There is also a Login page for adminstrator with default admin, admin credentials which stored in another MYSQL database table.
- After adminstrator login, it can see the dashboard with some charts above and below there are database records which shows.
header: header has title and logo on left side, on right side it has login and download button.
footer: make good footer accordingly

We have to store images in a file not in a database, db only contain URL to this file.
database structure:
- DETECTION: detection_id, mask_status, confidence_score, image_path, timestamp, media_source(uploadimage/webcam)
- ADMIN: admin_id, username, password

For the tech stack for web app, you have to use FLASK as backend, and MYSQL database, HTML, CSS, Tailwind etc for Frontend. For webcam use OpenCV and mediapipe.
For webapp, please use good structured with flask blueprints and also the directory strucutre.

NOTE: Don't touch to Documentation, CS619 - Final Project, README.md folders and files which are already in the current directory.