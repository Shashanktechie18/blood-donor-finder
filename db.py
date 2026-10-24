import mysql.connector
from mysql.connector import Error
from config import Config

def get_db_connection():
    """Create and return a MySQL database connection."""
    try:
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            port=Config.MYSQL_PORT
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def execute_query(query, params=None, fetch=False, fetchone=False, commit=False):
    """Execute a database query with optional fetch/commit."""
    conn = get_db_connection()
    if not conn:
        return None
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if commit:
            conn.commit()
            return cursor.lastrowid
        
        if fetchone:
            result = cursor.fetchone()
            return result
        
        if fetch:
            result = cursor.fetchall()
            return result
        
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def call_procedure(proc_name, args=None):
    """Call a stored procedure and return results."""
    conn = get_db_connection()
    if not conn:
        return None
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.callproc(proc_name, args or [])
        
        results = []
        for result in cursor.stored_results():
            results.extend(result.fetchall())
        
        return results
    except Error as e:
        print(f"Procedure error: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def init_db():
    """Initialize the database schema, triggers, procedures, and seed data."""
    try:
        # First connect without database to create it
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            port=Config.MYSQL_PORT
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DATABASE}")
        cursor.execute(f"USE {Config.MYSQL_DATABASE}")
        
        # Create tables
        tables = [
            """
            CREATE TABLE IF NOT EXISTS BLOOD_GROUP (
                blood_group_id INT AUTO_INCREMENT PRIMARY KEY,
                blood_group_name VARCHAR(5) NOT NULL UNIQUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS DONOR (
                donor_id INT AUTO_INCREMENT PRIMARY KEY,
                donor_name VARCHAR(100) NOT NULL,
                age INT NOT NULL,
                gender ENUM('M','F','Other') NOT NULL,
                phone VARCHAR(15) UNIQUE NOT NULL,
                address TEXT,
                availability_status ENUM('Available','Unavailable') DEFAULT 'Available',
                blood_group_id INT,
                password VARCHAR(255) NOT NULL,
                FOREIGN KEY (blood_group_id) REFERENCES BLOOD_GROUP(blood_group_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS HOSPITAL (
                hospital_id INT AUTO_INCREMENT PRIMARY KEY,
                hospital_name VARCHAR(150) NOT NULL,
                address TEXT,
                contact_number VARCHAR(15) NOT NULL,
                password VARCHAR(255) NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS ADMIN (
                admin_id INT AUTO_INCREMENT PRIMARY KEY,
                admin_name VARCHAR(100) NOT NULL,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS EMERGENCY_REQUEST (
                request_id INT AUTO_INCREMENT PRIMARY KEY,
                units_required INT NOT NULL,
                priority_level ENUM('Critical','High','Medium','Low') NOT NULL,
                request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                status ENUM('Pending','In Progress','Fulfilled','Cancelled') DEFAULT 'Pending',
                blood_group_id INT,
                hospital_id INT,
                FOREIGN KEY (blood_group_id) REFERENCES BLOOD_GROUP(blood_group_id),
                FOREIGN KEY (hospital_id) REFERENCES HOSPITAL(hospital_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS DONATION_RESPONSE (
                response_id INT AUTO_INCREMENT PRIMARY KEY,
                response_status ENUM('Accepted','Rejected','Pending') DEFAULT 'Pending',
                response_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                donor_id INT,
                request_id INT,
                admin_id INT NULL,
                FOREIGN KEY (donor_id) REFERENCES DONOR(donor_id),
                FOREIGN KEY (request_id) REFERENCES EMERGENCY_REQUEST(request_id),
                FOREIGN KEY (admin_id) REFERENCES ADMIN(admin_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS RESPONDS_TO (
                donor_id INT,
                response_id INT,
                PRIMARY KEY (donor_id, response_id),
                FOREIGN KEY (donor_id) REFERENCES DONOR(donor_id),
                FOREIGN KEY (response_id) REFERENCES DONATION_RESPONSE(response_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS MANAGES (
                admin_id INT,
                response_id INT,
                PRIMARY KEY (admin_id, response_id),
                FOREIGN KEY (admin_id) REFERENCES ADMIN(admin_id),
                FOREIGN KEY (response_id) REFERENCES DONATION_RESPONSE(response_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS HOSPITAL_ADMIN (
                hospital_id INT,
                admin_id INT,
                PRIMARY KEY (hospital_id, admin_id),
                FOREIGN KEY (hospital_id) REFERENCES HOSPITAL(hospital_id),
                FOREIGN KEY (admin_id) REFERENCES ADMIN(admin_id)
            )
            """
        ]
        
        for table_sql in tables:
            cursor.execute(table_sql)
        
        # Create triggers (drop first if exist)
        cursor.execute("DROP TRIGGER IF EXISTS trg_update_donor_status")
        cursor.execute("""
            CREATE TRIGGER trg_update_donor_status
            AFTER UPDATE ON DONATION_RESPONSE
            FOR EACH ROW
            BEGIN
                IF NEW.response_status = 'Accepted' THEN
                    UPDATE DONOR
                    SET availability_status = 'Unavailable'
                    WHERE donor_id = NEW.donor_id;
                END IF;
            END
        """)
        
        cursor.execute("DROP TRIGGER IF EXISTS trg_emergency_alert")
        cursor.execute("""
            CREATE TRIGGER trg_emergency_alert
            AFTER INSERT ON EMERGENCY_REQUEST
            FOR EACH ROW
            BEGIN
                INSERT INTO DONATION_RESPONSE (response_status, response_date, donor_id, request_id)
                SELECT 'Pending', NOW(), d.donor_id, NEW.request_id
                FROM DONOR d
                WHERE d.blood_group_id = NEW.blood_group_id
                  AND d.availability_status = 'Available';
            END
        """)
        
        # Create stored procedures
        cursor.execute("DROP PROCEDURE IF EXISTS SearchAvailableDonors")
        cursor.execute("""
            CREATE PROCEDURE SearchAvailableDonors(IN bg_name VARCHAR(5))
            BEGIN
                SELECT d.donor_id, d.donor_name, d.phone, d.address, d.age, d.gender,
                       bg.blood_group_name
                FROM DONOR d
                JOIN BLOOD_GROUP bg ON d.blood_group_id = bg.blood_group_id
                WHERE bg.blood_group_name = bg_name
                  AND d.availability_status = 'Available';
            END
        """)
        
        cursor.execute("DROP PROCEDURE IF EXISTS GetEmergencyRequests")
        cursor.execute("""
            CREATE PROCEDURE GetEmergencyRequests()
            BEGIN
                SELECT er.request_id, h.hospital_name, bg.blood_group_name,
                       er.units_required, er.priority_level, er.request_date, er.status
                FROM EMERGENCY_REQUEST er
                JOIN HOSPITAL h ON er.hospital_id = h.hospital_id
                JOIN BLOOD_GROUP bg ON er.blood_group_id = bg.blood_group_id
                WHERE er.status IN ('Pending', 'In Progress')
                ORDER BY FIELD(er.priority_level, 'Critical','High','Medium','Low'), er.request_date ASC;
            END
        """)
        
        # Seed blood groups
        blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        for bg in blood_groups:
            cursor.execute(
                "INSERT IGNORE INTO BLOOD_GROUP (blood_group_name) VALUES (%s)", (bg,)
            )
        
        # Seed default admin (password: admin123)
        cursor.execute(
            "SELECT admin_id FROM ADMIN WHERE username = 'admin'", 
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO ADMIN (admin_name, username, password) VALUES (%s, %s, %s)",
                ('System Admin', 'admin', 'admin123')
            )
        
        # Seed mock hospitals (password: hospital123)
        cursor.execute("SELECT COUNT(*) FROM HOSPITAL")
        if cursor.fetchone()[0] == 0:
            hospitals_data = [
                ('Manipal Hospital', '98 HAL Airport Road, Bengaluru', '9980001111', 'hospital123'),
                ('Fortis Hospital', '154/9 Bannerghatta Road, Bengaluru', '9980002222', 'hospital123'),
                ('Apollo Hospital', '21/1A Bannerghatta Road, Bengaluru', '9980003333', 'hospital123')
            ]
            cursor.executemany(
                "INSERT INTO HOSPITAL (hospital_name, address, contact_number, password) VALUES (%s, %s, %s, %s)",
                hospitals_data
            )
            
        # Seed mock donors (password: donor123)
        cursor.execute("SELECT COUNT(*) FROM DONOR")
        if cursor.fetchone()[0] == 0:
            donors_data = [
                ('Anmol Miskin', 25, 'M', '7020107467', 'Bengaluru', 'Available', 1, 'donor123'),
                ('Priya Sharma', 28, 'F', '9845123456', 'Mysuru', 'Available', 2, 'donor123'),
                ('Abhijeet S', 24, 'M', '7676748471', 'Bengaluru', 'Available', 3, 'donor123'),
                ('Sidhant Jadhav', 22, 'M', '8660524190', 'Bengaluru', 'Available', 7, 'donor123')
            ]
            cursor.executemany(
                """INSERT INTO DONOR (donor_name, age, gender, phone, address, availability_status, blood_group_id, password) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                donors_data
            )
        
        conn.commit()
        print("Database initialized successfully!")
        return True
        
    except Error as e:
        print(f"Error initializing database: {e}")
        return False
    finally:
        try:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
        except:
            pass
