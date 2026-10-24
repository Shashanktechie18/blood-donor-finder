-- ============================================================
--   BLOOD DONOR FINDER — MYSQL WORKBENCH QUERY REFERENCE
--   Database: blood_donor_db
-- ============================================================

USE blood_donor_db;

-- ============================================================
-- SECTION 1 : DATABASE & TABLE SETUP (run once)
-- ============================================================

CREATE DATABASE IF NOT EXISTS blood_donor_db;
USE blood_donor_db;

CREATE TABLE IF NOT EXISTS BLOOD_GROUP (
    blood_group_id   INT AUTO_INCREMENT PRIMARY KEY,
    blood_group_name VARCHAR(5) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS DONOR (
    donor_id            INT AUTO_INCREMENT PRIMARY KEY,
    donor_name          VARCHAR(100) NOT NULL,
    age                 INT NOT NULL,
    gender              ENUM('M','F','Other') NOT NULL,
    phone               VARCHAR(15) UNIQUE NOT NULL,
    address             TEXT,
    availability_status ENUM('Available','Unavailable') DEFAULT 'Available',
    blood_group_id      INT,
    password            VARCHAR(255) NOT NULL,
    FOREIGN KEY (blood_group_id) REFERENCES BLOOD_GROUP(blood_group_id)
);

CREATE TABLE IF NOT EXISTS HOSPITAL (
    hospital_id     INT AUTO_INCREMENT PRIMARY KEY,
    hospital_name   VARCHAR(150) NOT NULL,
    address         TEXT,
    contact_number  VARCHAR(15) NOT NULL,
    password        VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS ADMIN (
    admin_id    INT AUTO_INCREMENT PRIMARY KEY,
    admin_name  VARCHAR(100) NOT NULL,
    username    VARCHAR(50) UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS EMERGENCY_REQUEST (
    request_id     INT AUTO_INCREMENT PRIMARY KEY,
    units_required INT NOT NULL,
    priority_level ENUM('Critical','High','Medium','Low') NOT NULL,
    request_date   DATETIME DEFAULT CURRENT_TIMESTAMP,
    status         ENUM('Pending','In Progress','Fulfilled','Cancelled') DEFAULT 'Pending',
    blood_group_id INT,
    hospital_id    INT,
    FOREIGN KEY (blood_group_id) REFERENCES BLOOD_GROUP(blood_group_id),
    FOREIGN KEY (hospital_id)    REFERENCES HOSPITAL(hospital_id)
);

CREATE TABLE IF NOT EXISTS DONATION_RESPONSE (
    response_id     INT AUTO_INCREMENT PRIMARY KEY,
    response_status ENUM('Accepted','Rejected','Pending') DEFAULT 'Pending',
    response_date   DATETIME DEFAULT CURRENT_TIMESTAMP,
    donor_id        INT,
    request_id      INT,
    admin_id        INT NULL,
    FOREIGN KEY (donor_id)    REFERENCES DONOR(donor_id),
    FOREIGN KEY (request_id)  REFERENCES EMERGENCY_REQUEST(request_id),
    FOREIGN KEY (admin_id)    REFERENCES ADMIN(admin_id)
);

CREATE TABLE IF NOT EXISTS RESPONDS_TO (
    donor_id    INT,
    response_id INT,
    PRIMARY KEY (donor_id, response_id),
    FOREIGN KEY (donor_id)    REFERENCES DONOR(donor_id),
    FOREIGN KEY (response_id) REFERENCES DONATION_RESPONSE(response_id)
);

CREATE TABLE IF NOT EXISTS MANAGES (
    admin_id    INT,
    response_id INT,
    PRIMARY KEY (admin_id, response_id),
    FOREIGN KEY (admin_id)    REFERENCES ADMIN(admin_id),
    FOREIGN KEY (response_id) REFERENCES DONATION_RESPONSE(response_id)
);

CREATE TABLE IF NOT EXISTS HOSPITAL_ADMIN (
    hospital_id INT,
    admin_id    INT,
    PRIMARY KEY (hospital_id, admin_id),
    FOREIGN KEY (hospital_id) REFERENCES HOSPITAL(hospital_id),
    FOREIGN KEY (admin_id)    REFERENCES ADMIN(admin_id)
);

-- ============================================================
-- SECTION 2 : SEED DATA (run once)
-- ============================================================

-- Blood groups
INSERT IGNORE INTO BLOOD_GROUP (blood_group_name)
VALUES ('A+'), ('A-'), ('B+'), ('B-'), ('AB+'), ('AB-'), ('O+'), ('O-');

-- Default admin  (password: admin123)
INSERT IGNORE INTO ADMIN (admin_name, username, password)
VALUES ('System Admin', 'admin', 'admin123');

-- Mock hospitals  (password: hospital123)
INSERT IGNORE INTO HOSPITAL (hospital_name, address, contact_number, password) VALUES
    ('Manipal Hospital',  '98 HAL Airport Road, Bengaluru',     '9980001111', 'hospital123'),
    ('Fortis Hospital',   '154/9 Bannerghatta Road, Bengaluru', '9980002222', 'hospital123'),
    ('Apollo Hospital',   '21/1A Bannerghatta Road, Bengaluru', '9980003333', 'hospital123');

-- Mock donors  (password: donor123)
--   blood_group_id: 1=A+, 2=A-, 3=B+, 4=B-, 5=AB+, 6=AB-, 7=O+, 8=O-
INSERT IGNORE INTO DONOR (donor_name, age, gender, phone, address, availability_status, blood_group_id, password) VALUES
    ('Anmol Miskin',   25, 'M', '7020107467', 'Bengaluru', 'Available', 1, 'donor123'),
    ('Priya Sharma',   28, 'F', '9845123456', 'Mysuru',    'Available', 2, 'donor123'),
    ('Abhijeet S',     24, 'M', '7676748471', 'Bengaluru', 'Available', 3, 'donor123'),
    ('Sidhant Jadhav', 22, 'M', '8660524190', 'Bengaluru', 'Available', 7, 'donor123');

-- ============================================================
-- SECTION 3 : TRIGGERS
-- ============================================================

DROP TRIGGER IF EXISTS trg_update_donor_status;
DELIMITER $$
CREATE TRIGGER trg_update_donor_status
AFTER UPDATE ON DONATION_RESPONSE
FOR EACH ROW
BEGIN
    IF NEW.response_status = 'Accepted' THEN
        UPDATE DONOR
        SET availability_status = 'Unavailable'
        WHERE donor_id = NEW.donor_id;
    END IF;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trg_emergency_alert;
DELIMITER $$
CREATE TRIGGER trg_emergency_alert
AFTER INSERT ON EMERGENCY_REQUEST
FOR EACH ROW
BEGIN
    INSERT INTO DONATION_RESPONSE (response_status, response_date, donor_id, request_id)
    SELECT 'Pending', NOW(), d.donor_id, NEW.request_id
    FROM DONOR d
    WHERE d.blood_group_id = NEW.blood_group_id
      AND d.availability_status = 'Available';
END$$
DELIMITER ;

-- ============================================================
-- SECTION 4 : STORED PROCEDURES
-- ============================================================

DROP PROCEDURE IF EXISTS SearchAvailableDonors;
DELIMITER $$
CREATE PROCEDURE SearchAvailableDonors(IN bg_name VARCHAR(5))
BEGIN
    SELECT d.donor_id, d.donor_name, d.phone, d.address, d.age, d.gender,
           bg.blood_group_name
    FROM DONOR d
    JOIN BLOOD_GROUP bg ON d.blood_group_id = bg.blood_group_id
    WHERE bg.blood_group_name = bg_name
      AND d.availability_status = 'Available';
END$$
DELIMITER ;

DROP PROCEDURE IF EXISTS GetEmergencyRequests;
DELIMITER $$
CREATE PROCEDURE GetEmergencyRequests()
BEGIN
    SELECT er.request_id, h.hospital_name, bg.blood_group_name,
           er.units_required, er.priority_level, er.request_date, er.status
    FROM EMERGENCY_REQUEST er
    JOIN HOSPITAL  h  ON er.hospital_id    = h.hospital_id
    JOIN BLOOD_GROUP bg ON er.blood_group_id = bg.blood_group_id
    WHERE er.status IN ('Pending', 'In Progress')
    ORDER BY FIELD(er.priority_level, 'Critical','High','Medium','Low'), er.request_date ASC;
END$$
DELIMITER ;

-- ============================================================
-- SECTION 5 : SELECT QUERIES (READ)
-- ============================================================

-- 5.1  All donors with blood group name
SELECT d.donor_id, d.donor_name, d.age, d.gender, d.phone,
       d.address, d.availability_status, bg.blood_group_name
FROM DONOR d
JOIN BLOOD_GROUP bg ON d.blood_group_id = bg.blood_group_id
ORDER BY d.donor_name;

-- 5.2  All available donors
SELECT d.donor_id, d.donor_name, d.phone, d.age, d.gender,
       bg.blood_group_name
FROM DONOR d
JOIN BLOOD_GROUP bg ON d.blood_group_id = bg.blood_group_id
WHERE d.availability_status = 'Available'
ORDER BY bg.blood_group_name, d.donor_name;

-- 5.3  All hospitals
SELECT * FROM HOSPITAL ORDER BY hospital_name;

-- 5.4  All emergency requests (with hospital & blood group info)
SELECT er.request_id, h.hospital_name, bg.blood_group_name,
       er.units_required, er.priority_level, er.request_date, er.status
FROM EMERGENCY_REQUEST er
JOIN HOSPITAL    h  ON er.hospital_id    = h.hospital_id
JOIN BLOOD_GROUP bg ON er.blood_group_id = bg.blood_group_id
ORDER BY FIELD(er.priority_level, 'Critical','High','Medium','Low'),
         er.request_date DESC;

-- 5.5  Active (Pending / In Progress) emergency requests
SELECT er.request_id, h.hospital_name, bg.blood_group_name,
       er.units_required, er.priority_level, er.request_date, er.status
FROM EMERGENCY_REQUEST er
JOIN HOSPITAL    h  ON er.hospital_id    = h.hospital_id
JOIN BLOOD_GROUP bg ON er.blood_group_id = bg.blood_group_id
WHERE er.status IN ('Pending', 'In Progress')
ORDER BY FIELD(er.priority_level, 'Critical','High','Medium','Low'),
         er.request_date ASC;

-- 5.6  All donation responses (admin view)
SELECT dr.response_id, d.donor_name, d.phone, bg.blood_group_name,
       h.hospital_name, er.priority_level, er.units_required,
       dr.response_status, dr.response_date
FROM DONATION_RESPONSE dr
JOIN DONOR           d  ON dr.donor_id    = d.donor_id
JOIN EMERGENCY_REQUEST er ON dr.request_id = er.request_id
JOIN HOSPITAL        h  ON er.hospital_id  = h.hospital_id
JOIN BLOOD_GROUP     bg ON er.blood_group_id = bg.blood_group_id
ORDER BY dr.response_date DESC;

-- 5.7  Responses for a specific donor  (replace 1 with actual donor_id)
SELECT dr.response_id, dr.response_status, dr.response_date,
       er.request_id, er.units_required, er.priority_level,
       er.request_date, er.status AS request_status,
       h.hospital_name, h.address AS hospital_address, h.contact_number,
       bg.blood_group_name
FROM DONATION_RESPONSE dr
JOIN EMERGENCY_REQUEST er ON dr.request_id   = er.request_id
JOIN HOSPITAL          h  ON er.hospital_id  = h.hospital_id
JOIN BLOOD_GROUP       bg ON er.blood_group_id = bg.blood_group_id
WHERE dr.donor_id = 1   -- << change donor_id here
ORDER BY FIELD(er.priority_level, 'Critical','High','Medium','Low'),
         dr.response_date DESC;

-- 5.8  Requests placed by a specific hospital  (replace 1 with hospital_id)
SELECT er.*, bg.blood_group_name
FROM EMERGENCY_REQUEST er
JOIN BLOOD_GROUP bg ON er.blood_group_id = bg.blood_group_id
WHERE er.hospital_id = 1   -- << change hospital_id here
ORDER BY er.request_date DESC;

-- 5.9  Blood group distribution (donor count per group)
SELECT bg.blood_group_name, COUNT(d.donor_id) AS donor_count
FROM BLOOD_GROUP bg
LEFT JOIN DONOR d ON bg.blood_group_id = d.blood_group_id
GROUP BY bg.blood_group_id, bg.blood_group_name
ORDER BY bg.blood_group_name;

-- 5.10  Responses handled today
SELECT COUNT(*) AS responses_today
FROM DONATION_RESPONSE
WHERE DATE(response_date) = CURDATE();

-- 5.11  Admin dashboard counters
SELECT
    (SELECT COUNT(*) FROM DONOR)                                              AS total_donors,
    (SELECT COUNT(*) FROM DONOR WHERE availability_status = 'Available')      AS available_donors,
    (SELECT COUNT(*) FROM HOSPITAL)                                           AS total_hospitals,
    (SELECT COUNT(*) FROM EMERGENCY_REQUEST WHERE status IN ('Pending','In Progress')) AS active_requests,
    (SELECT COUNT(*) FROM EMERGENCY_REQUEST)                                  AS total_requests,
    (SELECT COUNT(*) FROM DONATION_RESPONSE WHERE DATE(response_date) = CURDATE()) AS responses_today;

-- 5.12  5 most recent emergency requests (admin dashboard widget)
SELECT er.*, h.hospital_name, bg.blood_group_name
FROM EMERGENCY_REQUEST er
JOIN HOSPITAL    h  ON er.hospital_id    = h.hospital_id
JOIN BLOOD_GROUP bg ON er.blood_group_id = bg.blood_group_id
ORDER BY er.request_date DESC
LIMIT 5;

-- 5.13  Hospital dashboard counters  (replace 1 with hospital_id)
SELECT
    (SELECT COUNT(*) FROM EMERGENCY_REQUEST WHERE hospital_id = 1)                                        AS total_requests,
    (SELECT COUNT(*) FROM EMERGENCY_REQUEST WHERE hospital_id = 1 AND status IN ('Pending','In Progress')) AS active_requests,
    (SELECT COUNT(*) FROM EMERGENCY_REQUEST WHERE hospital_id = 1 AND status = 'Fulfilled')               AS fulfilled_requests;

-- 5.14  Call stored procedure – search available donors by blood group
CALL SearchAvailableDonors('O+');   -- << change blood group

-- 5.15  Call stored procedure – get all active emergency requests
CALL GetEmergencyRequests();

-- ============================================================
-- SECTION 6 : INSERT QUERIES
-- ============================================================

-- 6.1  Register a new donor
INSERT INTO DONOR (donor_name, age, gender, phone, address, blood_group_id, password)
VALUES ('New Donor Name', 30, 'M', '9999999999', 'City, State', 1, 'donor123');

-- 6.2  Register a new hospital
INSERT INTO HOSPITAL (hospital_name, address, contact_number, password)
VALUES ('New Hospital', '123 Main Street, City', '9876543210', 'hospital123');

-- 6.3  Create an emergency request  (hospital_id=1, blood_group_id=3 = B+)
INSERT INTO EMERGENCY_REQUEST (units_required, priority_level, blood_group_id, hospital_id)
VALUES (2, 'Critical', 3, 1);

-- 6.4  Admin accepts / rejects a donation response
INSERT IGNORE INTO MANAGES (admin_id, response_id)
VALUES (1, 1);   -- admin_id=1 manages response_id=1

-- 6.5  Donor acknowledges a request (RESPONDS_TO junction)
INSERT IGNORE INTO RESPONDS_TO (donor_id, response_id)
VALUES (1, 1);   -- donor_id=1, response_id=1

-- ============================================================
-- SECTION 7 : UPDATE QUERIES
-- ============================================================

-- 7.1  Update donor profile (admin edit)
UPDATE DONOR
SET donor_name          = 'Updated Name',
    age                 = 26,
    gender              = 'M',
    phone               = '9000000001',
    address             = 'New Address, City',
    blood_group_id      = 2,
    availability_status = 'Available'
WHERE donor_id = 1;   -- << change donor_id

-- 7.2  Toggle donor availability (donor self-update)
UPDATE DONOR
SET availability_status = 'Unavailable'  -- or 'Available'
WHERE donor_id = 1;   -- << change donor_id

-- 7.3  Update hospital details (admin edit)
UPDATE HOSPITAL
SET hospital_name  = 'Updated Hospital Name',
    address        = 'New Address',
    contact_number = '9000000002'
WHERE hospital_id = 1;   -- << change hospital_id

-- 7.4  Update emergency request status (admin action)
UPDATE EMERGENCY_REQUEST
SET status = 'Fulfilled'   -- Pending | In Progress | Fulfilled | Cancelled
WHERE request_id = 1;      -- << change request_id

-- 7.5  Update request to 'In Progress' when a donor accepts
UPDATE EMERGENCY_REQUEST
SET status = 'In Progress'
WHERE request_id = 1 AND status = 'Pending';

-- 7.6  Update donation response status (admin approves/rejects)
UPDATE DONATION_RESPONSE
SET response_status = 'Accepted',  -- Accepted | Rejected | Pending
    admin_id        = 1            -- admin who acted
WHERE response_id = 1;             -- << change response_id

-- 7.7  Donor responds to a donation request (self-action)
UPDATE DONATION_RESPONSE
SET response_status = 'Accepted',  -- or 'Rejected'
    response_date   = NOW()
WHERE response_id = 1 AND donor_id = 1;

-- 7.8  Trigger effect — mark donor unavailable after accepting (done by trigger,
--      but can also be run manually)
UPDATE DONOR
SET availability_status = 'Unavailable'
WHERE donor_id = 1;

-- 7.9  Reset a donor back to Available (e.g., after donation period ends)
UPDATE DONOR
SET availability_status = 'Available'
WHERE donor_id = 1;

-- 7.10  Change admin password
UPDATE ADMIN
SET password = 'newpassword123'
WHERE username = 'admin';

-- ============================================================
-- SECTION 8 : DELETE QUERIES
-- ============================================================

-- 8.1  Delete a donor (cascade-safe: remove related rows first)
DELETE FROM MANAGES
WHERE response_id IN (SELECT response_id FROM DONATION_RESPONSE WHERE donor_id = 1);

DELETE FROM RESPONDS_TO WHERE donor_id = 1;

DELETE FROM DONATION_RESPONSE WHERE donor_id = 1;

DELETE FROM DONOR WHERE donor_id = 1;

-- 8.2  Delete a hospital (cascade-safe)
DELETE FROM HOSPITAL_ADMIN WHERE hospital_id = 1;

DELETE FROM RESPONDS_TO
WHERE response_id IN (
    SELECT response_id FROM DONATION_RESPONSE
    WHERE request_id IN (SELECT request_id FROM EMERGENCY_REQUEST WHERE hospital_id = 1)
);

DELETE FROM MANAGES
WHERE response_id IN (
    SELECT response_id FROM DONATION_RESPONSE
    WHERE request_id IN (SELECT request_id FROM EMERGENCY_REQUEST WHERE hospital_id = 1)
);

DELETE FROM DONATION_RESPONSE
WHERE request_id IN (SELECT request_id FROM EMERGENCY_REQUEST WHERE hospital_id = 1);

DELETE FROM EMERGENCY_REQUEST WHERE hospital_id = 1;

DELETE FROM HOSPITAL WHERE hospital_id = 1;

-- ============================================================
-- SECTION 9 : UTILITY / DIAGNOSTIC QUERIES
-- ============================================================

-- 9.1  Show all tables
SHOW TABLES;

-- 9.2  Show all triggers
SHOW TRIGGERS;

-- 9.3  Show all stored procedures
SHOW PROCEDURE STATUS WHERE Db = 'blood_donor_db';

-- 9.4  Check all blood groups
SELECT * FROM BLOOD_GROUP;

-- 9.5  Check all admins
SELECT admin_id, admin_name, username FROM ADMIN;

-- 9.6  Full donor list with blood group
SELECT d.donor_id, d.donor_name, d.age, d.gender, d.phone,
       d.address, d.availability_status, bg.blood_group_name
FROM DONOR d
JOIN BLOOD_GROUP bg ON d.blood_group_id = bg.blood_group_id;

-- 9.7  Full responses view
SELECT dr.response_id, d.donor_name, er.request_id,
       h.hospital_name, bg.blood_group_name, er.priority_level,
       dr.response_status, dr.response_date
FROM DONATION_RESPONSE dr
JOIN DONOR           d  ON dr.donor_id     = d.donor_id
JOIN EMERGENCY_REQUEST er ON dr.request_id = er.request_id
JOIN HOSPITAL        h  ON er.hospital_id  = h.hospital_id
JOIN BLOOD_GROUP     bg ON er.blood_group_id = bg.blood_group_id;

-- 9.8  Check login credentials (donor by phone)
SELECT donor_id, donor_name, phone, password FROM DONOR WHERE phone = '7020107467';

-- 9.9  Check login credentials (hospital by contact)
SELECT hospital_id, hospital_name, contact_number, password FROM HOSPITAL WHERE contact_number = '9980001111';

-- 9.10  Check login credentials (admin by username)
SELECT admin_id, admin_name, username, password FROM ADMIN WHERE username = 'admin';

-- ============================================================
-- END OF QUERY FILE
-- ============================================================
