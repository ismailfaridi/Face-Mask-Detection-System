# Face Mask Detection System

An AI-powered real-time face mask detection system using deep learning. Built with Flask, TensorFlow, MediaPipe, and OpenCV. Features both image upload and live webcam detection with an admin dashboard for analytics.

**Features:**
- 🎥 Real-time webcam mask detection with live bounding boxes
- 📸 Image upload for mask detection
- 📊 Admin dashboard with statistics and detection history
- 🔐 Secure admin login
- 📈 Chart.js visualizations (distribution & trends)
- 🎨 Clean, responsive UI with Tailwind CSS
- 💾 SQLite database for detection records

---

## Project Structure

```
Face-Mask-Detection-System/
├── app/
│   ├── __init__.py              # Flask app initialization
│   ├── blueprints/
│   │   ├── admin.py             # Admin login/logout routes
│   │   └── main.py              # Upload, webcam, dashboard routes
│   ├── models/
│   │   └── db.py                # DatabaseManager & Admin classes
│   ├── services/
│   │   ├── detector.py          # Face detection & mask classification
│   │   ├── blaze_face_full_range.tflite  # Face detection model (DEPRECATED)
│   │   └── face_mask_detector_mobile-net-v2_model.keras  # Mask classifier
│   ├── static/
│   │   ├── css/                 # Stylesheets
│   │   ├── js/                  # Client-side scripts
│   │   └── uploads/
│   │       ├── mask/            # Detected mask images
│   │       └── no-mask/         # Detected no-mask images
│   └── templates/
│       ├── base.html            # Base template with header/footer
│       ├── index.html           # Homepage
│       ├── login.html           # Admin login
│       ├── upload.html          # Image upload page
│       ├── webcam.html          # Webcam detection page
│       └── dashboard.html       # Admin dashboard
├── instance/
│   └── detection.db             # SQLite database (local, not committed)
├── scratch/                     # Development scripts
├── run.py                       # Flask app entry point
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (not committed)
├── .gitignore                   # Git ignore rules
└── README.md                    # Project documentation
---

## 🛠️ Database Management

The system uses SQLite, and the database file is located at `instance/detection.db`.

### How to open the database
1.  **VS Code**: Install the "SQLite Viewer" or "SQLite" extension. Right-click `instance/detection.db` and select "Open with...".
2.  **External Tool**: Use [DB Browser for SQLite](https://sqlitebrowser.org/) to view and edit the database with a user-friendly interface.
3.  **Command Line**: Run `sqlite3 instance/detection.db` (requires SQLite CLI installed).

### Common SQL Queries
To manage your records, you can run the following SQL queries inside your database tool:

*   **Remove a specific record**:
    ```sql
    DELETE FROM DETECTION WHERE id = [ID_NUMBER];
    ```
*   **Remove all records**:
    ```sql
    DELETE FROM DETECTION;
    ```
*   **Reset the ID counter (after deleting all records)**:
    ```sql
    DELETE FROM sqlite_sequence WHERE name='DETECTION';
    ```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Flask 3.0.0 |
| **Face Detection** | MediaPipe 0.10.14 |
| **Mask Classification** | TensorFlow 2.18.0 + Keras 3.14.0 |
| **Image Processing** | OpenCV 4.9.0.80 |
| **Database** | SQLite3 |
| **Frontend** | HTML5, Tailwind CSS 3 |
| **Charts** | Chart.js |
| **Python Version** | 3.12.6 |

---

## Installation & Setup

### 1. Clone the Repository
```bash
cd Face-Mask-Detection-System
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
DB_NAME=instance/detection.db

# Flask Configuration
SECRET_KEY=super_secret_key_123
```

**Note:** The `.env` file is automatically added to `.gitignore` for security.

### 5. Run the Application
```bash
python run.py
```

The app will start at: `http://127.0.0.1:5000`

---

## Database Schema

### DETECTION Table
```sql
CREATE TABLE DETECTION (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mask_status TEXT,              -- "Mask" or "No Mask"
    confidence_score REAL,         -- 0.0 to 1.0
    image_path TEXT,               -- Path to uploaded/saved image
    media_source TEXT,             -- "upload" or "webcam"
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### ADMIN Table
```sql
CREATE TABLE ADMIN (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
);
```

**Default Admin Credentials:**
- Username: `admin`
- Password: `admin`

---

## Usage

### 1. **Homepage**
- Access at `/`
- Two main options: Upload image or start webcam detection
- Displays feature overview and how-to information

### 2. **Upload Image**
- Navigate to `/upload`
- Drag & drop or click to select an image
- System detects faces and classifies mask status
- Results shown with confidence percentage

### 3. **Webcam Detection**
- Navigate to `/webcam`
- Allow browser permission to access webcam
- Real-time detection with bounding boxes
- Frames saved every 5 seconds to database

### 4. **Admin Dashboard**
- Login at `/login` (default: `admin`/`admin`)
- View statistics: total masks, total no-masks, all records
- Doughnut chart: mask distribution
- Line chart: detection trends over time
- Full detection history table

---

## Key Features

### Face Detection
- Uses **MediaPipe** face detection (model_selection=1, full range)
- Detects multiple faces in a single image
- Returns bounding box coordinates

### Mask Classification
- **MobileNetV2** CNN model for binary classification
- Threshold: >= 0.5 → "Mask", < 0.5 → "No Mask"
- Confidence score: 0-100%

### Image Storage
- Upload images stored in `app/static/uploads/mask/` or `app/static/uploads/no-mask/`
- Database stores only the relative file path
- Webcam frames saved with timestamps

### Responsive Design
- Mobile-friendly UI with Tailwind CSS
- Header hidden elements on small screens
- Glass-morphism design pattern
- Smooth transitions and hover effects

---

## API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Homepage |
| `/upload` | GET/POST | Image upload & detection |
| `/webcam` | GET | Webcam streaming page |
| `/video_feed` | GET | MJPEG video stream for webcam |
| `/login` | GET/POST | Admin login |
| `/dashboard` | GET | Admin statistics & history |
| `/logout` | GET | Admin logout |

---

## Important Notes

### MediaPipe Version
- **Must use v0.10.14** — Other versions don't include `mp.solutions` API
- Version v0.10.35+ removed the `solutions` module

### Keras 3 Compatibility
- TensorFlow 2.18.0 includes Keras 3.14.0
- No special configuration needed; model loads directly

### Database Location
- Database file is in `instance/detection.db` (not committed to git)
- Auto-created on first run if it doesn't exist

### Browser Permissions
- Webcam feature requires browser permission for camera access
- Upload accepts PNG, JPG, JPEG (max 5MB)

---

## Troubleshooting

**Issue:** ImportError: cannot import name 'mp.solutions.face_detection'
- **Solution:** Ensure MediaPipe 0.10.14 is installed: `pip install mediapipe==0.10.14`

**Issue:** Database file not found
- **Solution:** Run `python run.py` once to auto-initialize; check `instance/` folder exists

**Issue:** Model loading fails
- **Solution:** Verify `.keras` model file exists in `app/services/` directory

---

## Future Enhancements

- [ ] Multi-face tracking with ID persistence
- [ ] Mask type classification (N95, surgical, cloth)
- [ ] Export detection reports (PDF/CSV)
- [ ] REST API for external integrations
- [ ] Real-time alerts on mask violations
- [ ] PostgreSQL support for production

---

## License

CS619 - Final Project

**Developer:** Muhammad Ismail

**YouTube Playlist:** https://www.youtube.com/playlist?list=PLEQQipl_9di-GzYMfJdXOZIV_9mLdbP2N