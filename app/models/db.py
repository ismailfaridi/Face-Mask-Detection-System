import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    """
    Handles all interactions with the SQLite database, including initialization,
    storing detection records, and retrieving statistics.
    """
    def __init__(self):
        """
        Initializes the DatabaseManager by setting the database path and ensuring
        the database schema exists.
        """
        # Default to instance/detection.db to keep database outside app/templates/static folders
        self.db_path = os.getenv('DB_NAME', os.path.join('instance', 'detection.db'))
        self._init_db()

    def get_connection(self):
        """
        Establishes and returns a connection to the SQLite database.
        
        Returns:
            sqlite3.Connection: A database connection with Row factory enabled.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """
        Private method to initialize the database tables and create a default 
        admin user if they don't already exist.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS DETECTION (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mask_status TEXT,
                confidence_score REAL,
                image_path TEXT,
                media_source TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ADMIN (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')
        
        cursor.execute('SELECT * FROM ADMIN WHERE username="admin"')
        if not cursor.fetchone():
            cursor.execute('INSERT INTO ADMIN (username, password) VALUES ("admin", "admin")')
            
        conn.commit()
        conn.close()

    def storeRecord(self, mask_status, confidence_score, image_path, media_source):
        """
        Stores a face mask detection record in the database.
        
        Args:
            mask_status (str):          The status ('Mask' or 'No Mask').
            confidence_score (float):   The detection confidence score.
            image_path (str):           The path or identifier for the associated image.
            media_source (str):         The source of the image (e.g., 'Webcam', 'Upload').
            
        Returns:
            bool: True if storage was successful, False otherwise.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            sql = "INSERT INTO DETECTION (mask_status, confidence_score, image_path, media_source) VALUES (?, ?, ?, ?)"
            # Ensure confidence_score is float to avoid sqlite type errors with numpy types
            cursor.execute(sql, (mask_status, float(confidence_score), image_path, media_source))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"DB Error storeRecord: {e}")
            return False

    def getAllRecords(self):
        """
        Retrieves all detection records from the database, ordered by timestamp.
        
        Returns:
            list: A list of dictionaries representing each detection record.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            sql = "SELECT * FROM DETECTION ORDER BY timestamp DESC"
            cursor.execute(sql)
            result = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return result
        except Exception as e:
            print(f"DB Error getAllRecords: {e}")
            return []

    def getRecentRecords(self, limit=50):
        """
        Retrieves the most recent detection records up to a specified limit.
        
        Args:
            limit (int): The maximum number of records to retrieve. Defaults to 50.
            
        Returns:
            list: A list of dictionaries representing the recent detection records.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            sql = f"SELECT * FROM DETECTION ORDER BY timestamp DESC LIMIT {limit}"
            cursor.execute(sql)
            result = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return result
        except Exception as e:
            print(f"DB Error getRecentRecords: {e}")
            return []

    def getStatistics(self):
        """
        Calculates total detection counts for statistics visualization.
        
        Returns:
            dict: A dictionary containing 'mask' and 'no_mask' counts.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            sql_mask = "SELECT COUNT(*) as c FROM DETECTION WHERE mask_status='Mask'"
            cursor.execute(sql_mask)
            mask_count = cursor.fetchone()['c']
            
            sql_nomask = "SELECT COUNT(*) as c FROM DETECTION WHERE mask_status='No Mask'"
            cursor.execute(sql_nomask)
            nomask_count = cursor.fetchone()['c']
            
            conn.close()
            return {'mask': mask_count, 'no_mask': nomask_count}
        except Exception as e:
            print(f"DB Error getStatistics: {e}")
            return {'mask': 0, 'no_mask': 0}

class Admin:
    """
    Represents an administrative user and provides methods for authentication.
    """
    def __init__(self, username):
        self.username = username
        self.db = DatabaseManager()

    def login(self, username, password):
        """
        Authenticates an administrator using their username and password.
        
        Args:
            username (str): The admin username.
            password (str): The admin password.
            
        Returns:
            bool: True if credentials are valid, False otherwise.
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            sql = "SELECT * FROM ADMIN WHERE username=? AND password=?"
            cursor.execute(sql, (username, password))
            user = cursor.fetchone()
            conn.close()
            return user is not None
        except Exception as e:
            print(f"DB Error Login: {e}")
            return False

    def logout(self):
        # Session handling will be done in Flask blueprint
        pass
