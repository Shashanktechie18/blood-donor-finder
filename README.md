<h1 align="center">🩸 Blood Donor Finder</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Flask-3.1.1-black?logo=flask&logoColor=white" alt="Flask"/>
  <img src="https://img.shields.io/badge/MySQL-8.0%2B-4479A1?logo=mysql&logoColor=white" alt="MySQL"/>
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License"/>
</p>

<p align="center">
  A full-stack web application for managing blood donors, hospitals, and emergency blood requests — built as a DBMS course project using Flask and MySQL.
</p>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Database Schema](#database-schema)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Screenshots](#screenshots)

---

## 🔍 Overview

**Blood Donor Finder** is a role-based web platform that connects blood donors with hospitals in emergency situations. It features three distinct user roles — **Admin**, **Donor**, and **Hospital** — each with a dedicated dashboard and set of capabilities.

---

## ✨ Features

### 👤 Donor
- Register with blood group, age, gender, contact info
- Update profile and availability status
- View and respond to emergency blood requests
- Change password securely

### 🏥 Hospital
- Register and manage hospital profile
- Post emergency blood requests with blood group and units needed
- Search for available donors by blood group
- Track the status of all requests

### 🛡️ Admin
- View all registered donors and hospitals
- Approve or manage emergency requests
- View system-wide reports and response logs
- Full CRUD access over the platform

---

## 🛠️ Tech Stack

| Layer       | Technology                        |
|-------------|-----------------------------------|
| Backend     | Python 3.10+, Flask 3.1.1         |
| Database    | MySQL 8.0+ (via mysql-connector)  |
| Frontend    | HTML5, CSS3, JavaScript (Vanilla) |
| Auth        | Session-based (Werkzeug hashing)  |
| ORM/DB      | Raw SQL with stored procedures    |

---

## 🗄️ Database Schema

The application uses the following core tables:

```
BLOOD_GROUP      — Blood group reference data
DONOR            — Donor registration & credentials
HOSPITAL         — Hospital registration & credentials
ADMIN            — Admin accounts
EMERGENCY_REQUEST — Blood requests raised by hospitals
REQUEST_RESPONSE  — Donor responses to requests
```

> Full schema with all DDL, DML, stored procedures, triggers, and sample queries is in [`blood_donor_queries.sql`](./blood_donor_queries.sql).

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- MySQL Server 8.0+
- pip

### 1. Clone the Repository

```bash
git clone https://github.com/Sidhant-Jadhav/blood-donor-finder.git
cd blood-donor-finder
```

### 2. Create & Activate a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Database

1. Open **MySQL Workbench** (or any MySQL client)
2. Run the full schema script:
   ```sql
   source blood_donor_queries.sql;
   ```
3. Set up your environment variables (or update `config.py`):

```bash
# Create a .env file (never commit this!)
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=blood_donor_db
SECRET_KEY=your-secret-key
```

### 5. Run the Application

```bash
python app.py
```

Visit **http://127.0.0.1:5000** in your browser.

---

## 📁 Project Structure

```
blood-donor-finder/
├── app.py                    # Main Flask application & all routes
├── config.py                 # App & DB configuration (env-driven)
├── db.py                     # DB connection helpers & query utilities
├── blood_donor_queries.sql   # Full MySQL schema, procedures & queries
├── mysql_reset.sql           # Quick DB reset script
├── requirements.txt          # Python dependencies
├── static/
│   ├── css/                  # Stylesheets
│   └── js/                   # JavaScript files
└── templates/
    ├── base.html             # Base layout template
    ├── index.html            # Landing / Login page
    ├── admin/                # Admin dashboard templates
    ├── donor/                # Donor portal templates
    └── hospital/             # Hospital portal templates
```

---

## 🖥️ Usage

| Role     | Login Credential       | Default Access         |
|----------|------------------------|------------------------|
| Admin    | Username + Password    | `/admin/dashboard`     |
| Donor    | Phone Number + Password| `/donor/profile`       |
| Hospital | Contact + Password     | `/hospital/dashboard`  |

---

## 📸 Screenshots

> _Add screenshots of the dashboard, donor registration, and hospital request pages here._

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">Made with ❤️ by <a href="https://github.com/Sidhant-Jadhav">Sidhant Jadhav</a></p>
