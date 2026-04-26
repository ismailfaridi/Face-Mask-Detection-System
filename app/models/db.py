import pymysql
import os

class DatabaseManager:
    def __init__(self):
        self.host = os.getenv('DB_HOST', '127.0.0.1')
        self.user = os.getenv('DB_USER', 'admin')
        self.password = os.getenv('DB_PASSWORD', 'admin')
        self.db = os.getenv('DB_NAME', 'mask_detection')
        self.port = int(os.getenv('DB_PORT', 3306))

    def get_connection(self):
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.db,
            cursorclass=pymysql.cursors.DictCursor
        )

    def storeRecord(self, mask_status, confidence_score, image_path, media_source):
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                sql = "INSERT INTO DETECTION (mask_status, confidence_score, image_path, media_source) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (mask_status, confidence_score, image_path, media_source))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"DB Error storeRecord: {e}")
            return False

    def getAllRecords(self, limit=100):
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                sql = "SELECT * FROM DETECTION ORDER BY timestamp DESC LIMIT %s"
                cursor.execute(sql, (limit,))
                result = cursor.fetchall()
            conn.close()
            return result
        except Exception as e:
            print(f"DB Error getAllRecords: {e}")
            return []

    def getStatistics(self):
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
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
            with conn.cursor() as cursor:
                sql = "SELECT * FROM ADMIN WHERE username=%s AND password=%s"
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
