import sqlite3
import os

class DatabaseManager:
    def __init__(self):
        # Default to instance/detection.db to keep database outside app/templates/static folders
        self.db_path = os.getenv('DB_NAME', os.path.join('instance', 'detection.db'))
        self._init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
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

    def getStatistics(self):
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
    def __init__(self, username):
        self.username = username
        self.db = DatabaseManager()

    def login(self, username, password):
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
