from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from config import Config
from db import get_db_connection, execute_query, call_procedure, init_db
import datetime

app = Flask(__name__)
app.config.from_object(Config)

# ─── Auth Decorators ─────────────────────────────────────────────

def login_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or session.get('role') != role:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ─── Landing & Auth ──────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'donor':
            return redirect(url_for('donor_profile'))
        elif role == 'hospital':
            return redirect(url_for('hospital_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    role = request.form.get('role')
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    if role == 'admin':
        user = execute_query(
            "SELECT * FROM ADMIN WHERE username = %s",
            (username,), fetchone=True
        )
        if user and user['password'] == password:
            session['user_id'] = user['admin_id']
            session['user_name'] = user['admin_name']
            session['role'] = 'admin'
            session.permanent = True
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
    
    elif role == 'donor':
        user = execute_query(
            "SELECT * FROM DONOR WHERE phone = %s",
            (username,), fetchone=True
        )
        if user and user['password'] == password:
            session['user_id'] = user['donor_id']
            session['user_name'] = user['donor_name']
            session['role'] = 'donor'
            session['blood_group_id'] = user['blood_group_id']
            session.permanent = True
            flash(f'Welcome, {user["donor_name"]}!', 'success')
            return redirect(url_for('donor_profile'))
    
    elif role == 'hospital':
        user = execute_query(
            "SELECT * FROM HOSPITAL WHERE contact_number = %s",
            (username,), fetchone=True
        )
        if user and user['password'] == password:
            session['user_id'] = user['hospital_id']
            session['user_name'] = user['hospital_name']
            session['role'] = 'hospital'
            session.permanent = True
            flash(f'Welcome, {user["hospital_name"]}!', 'success')
            return redirect(url_for('hospital_dashboard'))
    
    flash('Invalid credentials. Please try again.', 'error')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session or 'role' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('index'))
    
    role = session['role']
    user_id = session['user_id']
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_password or not new_password or not confirm_password:
            flash('All fields are required.', 'error')
            return redirect(url_for('change_password'))
            
        if new_password != confirm_password:
            flash('New password and confirm password do not match.', 'error')
            return redirect(url_for('change_password'))
            
        # Verify current password
        if role == 'admin':
            user = execute_query("SELECT password FROM ADMIN WHERE admin_id = %s", (user_id,), fetchone=True)
            table_name = "ADMIN"
            id_col = "admin_id"
        elif role == 'donor':
            user = execute_query("SELECT password FROM DONOR WHERE donor_id = %s", (user_id,), fetchone=True)
            table_name = "DONOR"
            id_col = "donor_id"
        elif role == 'hospital':
            user = execute_query("SELECT password FROM HOSPITAL WHERE hospital_id = %s", (user_id,), fetchone=True)
            table_name = "HOSPITAL"
            id_col = "hospital_id"
        else:
            flash('Invalid user role.', 'error')
            return redirect(url_for('index'))
            
        if not user or user['password'] != current_password:
            flash('Incorrect current password.', 'error')
            return redirect(url_for('change_password'))
            
        # Update password
        execute_query(
            f"UPDATE {table_name} SET password = %s WHERE {id_col} = %s",
            (new_password, user_id),
            commit=True
        )
        flash('Password updated successfully!', 'success')
        
        # Redirect based on role
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'donor':
            return redirect(url_for('donor_profile'))
        elif role == 'hospital':
            return redirect(url_for('hospital_dashboard'))
            
    return render_template('change_password.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        step = request.form.get('step')

        if step == '1':
            role = request.form.get('role')
            identifier = request.form.get('identifier', '').strip()

            user = None
            display_name = ''
            user_id = None

            if role == 'admin':
                user = execute_query(
                    "SELECT admin_id, admin_name FROM ADMIN WHERE username = %s",
                    (identifier,), fetchone=True
                )
                if user:
                    display_name = user['admin_name']
                    user_id = user['admin_id']

            elif role == 'donor':
                user = execute_query(
                    "SELECT donor_id, donor_name FROM DONOR WHERE phone = %s",
                    (identifier,), fetchone=True
                )
                if user:
                    display_name = user['donor_name']
                    user_id = user['donor_id']

            elif role == 'hospital':
                user = execute_query(
                    "SELECT hospital_id, hospital_name FROM HOSPITAL WHERE contact_number = %s",
                    (identifier,), fetchone=True
                )
                if user:
                    display_name = user['hospital_name']
                    user_id = user['hospital_id']

            if not user:
                flash('No account found with that identifier. Please try again.', 'error')
                return render_template('forgot_password.html', step2=False)

            return render_template('forgot_password.html',
                step2=True,
                display_name=display_name,
                reset_role=role,
                reset_user_id=user_id
            )

        elif step == '2':
            role = request.form.get('role')
            user_id = request.form.get('user_id')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if not new_password or not confirm_password:
                flash('All fields are required.', 'error')
                return redirect(url_for('forgot_password'))

            if new_password != confirm_password:
                flash('Passwords do not match. Please try again.', 'error')
                return redirect(url_for('forgot_password'))

            if role == 'admin':
                table_name, id_col = 'ADMIN', 'admin_id'
            elif role == 'donor':
                table_name, id_col = 'DONOR', 'donor_id'
            elif role == 'hospital':
                table_name, id_col = 'HOSPITAL', 'hospital_id'
            else:
                flash('Invalid role.', 'error')
                return redirect(url_for('forgot_password'))

            execute_query(
                f"UPDATE {table_name} SET password = %s WHERE {id_col} = %s",
                (new_password, user_id), commit=True
            )
            flash('Password reset successfully! You can now log in with your new password.', 'success')
            return redirect(url_for('index'))

    return render_template('forgot_password.html', step2=False)

# ─── Donor Registration ─────────────────────────────────────────

@app.route('/donor/register', methods=['GET', 'POST'])
def donor_register():
    if request.method == 'POST':
        name = request.form.get('donor_name', '').strip()
        age = request.form.get('age')
        gender = request.form.get('gender')
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        blood_group_id = request.form.get('blood_group_id')
        password = request.form.get('password')
        
        # Check if phone already exists
        existing = execute_query(
            "SELECT donor_id FROM DONOR WHERE phone = %s", (phone,), fetchone=True
        )
        if existing:
            flash('Phone number already registered.', 'error')
            blood_groups = execute_query("SELECT * FROM BLOOD_GROUP ORDER BY blood_group_name", fetch=True)
            return render_template('donor/register.html', blood_groups=blood_groups or [])
        
        execute_query(
            """INSERT INTO DONOR (donor_name, age, gender, phone, address, blood_group_id, password)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (name, age, gender, phone, address, blood_group_id, password),
            commit=True
        )
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('index'))
    
    blood_groups = execute_query("SELECT * FROM BLOOD_GROUP ORDER BY blood_group_name", fetch=True)
    return render_template('donor/register.html', blood_groups=blood_groups or [])

# ─── Hospital Registration ───────────────────────────────────────

@app.route('/hospital/register', methods=['GET', 'POST'])
def hospital_register():
    if request.method == 'POST':
        name = request.form.get('hospital_name', '').strip()
        address = request.form.get('address', '').strip()
        contact = request.form.get('contact_number', '').strip()
        password = request.form.get('password')
        
        existing = execute_query(
            "SELECT hospital_id FROM HOSPITAL WHERE contact_number = %s", (contact,), fetchone=True
        )
        if existing:
            flash('Contact number already registered.', 'error')
            return render_template('hospital/register.html')
        
        execute_query(
            """INSERT INTO HOSPITAL (hospital_name, address, contact_number, password)
               VALUES (%s, %s, %s, %s)""",
            (name, address, contact, password),
            commit=True
        )
        flash('Hospital registered successfully! You can now log in.', 'success')
        return redirect(url_for('index'))
    
    return render_template('hospital/register.html')

# ═══════════════════════════════════════════════════════════════════
#  ADMIN ROUTES
# ═══════════════════════════════════════════════════════════════════

@app.route('/admin/dashboard')
@login_required('admin')
def admin_dashboard():
    total_donors = execute_query("SELECT COUNT(*) as count FROM DONOR", fetchone=True)['count']
    available_donors = execute_query(
        "SELECT COUNT(*) as count FROM DONOR WHERE availability_status='Available'", fetchone=True
    )['count']
    total_hospitals = execute_query("SELECT COUNT(*) as count FROM HOSPITAL", fetchone=True)['count']
    active_requests = execute_query(
        "SELECT COUNT(*) as count FROM EMERGENCY_REQUEST WHERE status IN ('Pending','In Progress')",
        fetchone=True
    )['count']
    total_requests = execute_query("SELECT COUNT(*) as count FROM EMERGENCY_REQUEST", fetchone=True)['count']
    responses_today = execute_query(
        "SELECT COUNT(*) as count FROM DONATION_RESPONSE WHERE DATE(response_date) = CURDATE()",
        fetchone=True
    )['count']
    
    # Recent requests
    recent_requests = execute_query("""
        SELECT er.*, h.hospital_name, bg.blood_group_name
        FROM EMERGENCY_REQUEST er
        JOIN HOSPITAL h ON er.hospital_id = h.hospital_id
        JOIN BLOOD_GROUP bg ON er.blood_group_id = bg.blood_group_id
        ORDER BY er.request_date DESC LIMIT 5
    """, fetch=True)
    
    return render_template('admin/dashboard.html',
        total_donors=total_donors,
        available_donors=available_donors,
        total_hospitals=total_hospitals,
        active_requests=active_requests,
        total_requests=total_requests,
        responses_today=responses_today,
        recent_requests=recent_requests or []
    )

@app.route('/admin/donors', methods=['GET', 'POST'])
@login_required('admin')
def admin_donors():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            name = request.form.get('donor_name', '').strip()
            age = request.form.get('age')
            gender = request.form.get('gender')
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            blood_group_id = request.form.get('blood_group_id')
            password = 'donor123'  # default password
            
            existing = execute_query("SELECT donor_id FROM DONOR WHERE phone = %s", (phone,), fetchone=True)
            if existing:
                flash('Phone number already registered.', 'error')
            else:
                execute_query(
                    """INSERT INTO DONOR (donor_name, age, gender, phone, address, blood_group_id, password)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (name, age, gender, phone, address, blood_group_id, password),
                    commit=True
                )
                flash('Donor added successfully! Default password: donor123', 'success')
        
        elif action == 'edit':
            donor_id = request.form.get('donor_id')
            name = request.form.get('donor_name', '').strip()
            age = request.form.get('age')
            gender = request.form.get('gender')
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            blood_group_id = request.form.get('blood_group_id')
            availability = request.form.get('availability_status')
            
            existing = execute_query("SELECT donor_id FROM DONOR WHERE phone = %s AND donor_id != %s", (phone, donor_id), fetchone=True)
            if existing:
                flash('Phone number already registered to another donor.', 'error')
            else:
                execute_query(
                    """UPDATE DONOR SET donor_name=%s, age=%s, gender=%s, phone=%s,
                       address=%s, blood_group_id=%s, availability_status=%s WHERE donor_id=%s""",
                    (name, age, gender, phone, address, blood_group_id, availability, donor_id),
                    commit=True
                )
                flash('Donor updated successfully!', 'success')
        
        elif action == 'delete':
            donor_id = request.form.get('donor_id')
            # Delete related records first
            execute_query("DELETE FROM MANAGES WHERE response_id IN (SELECT response_id FROM DONATION_RESPONSE WHERE donor_id = %s)", (donor_id,), commit=True)
            execute_query("DELETE FROM RESPONDS_TO WHERE donor_id = %s", (donor_id,), commit=True)
            execute_query("DELETE FROM DONATION_RESPONSE WHERE donor_id = %s", (donor_id,), commit=True)
            execute_query("DELETE FROM DONOR WHERE donor_id = %s", (donor_id,), commit=True)
            flash('Donor deleted successfully!', 'success')
        
        return redirect(url_for('admin_donors'))
    
    donors = execute_query("""
        SELECT d.*, bg.blood_group_name 
        FROM DONOR d 
        JOIN BLOOD_GROUP bg ON d.blood_group_id = bg.blood_group_id
        ORDER BY d.donor_name
    """, fetch=True)
    blood_groups = execute_query("SELECT * FROM BLOOD_GROUP ORDER BY blood_group_name", fetch=True)
    
    return render_template('admin/donors.html', donors=donors or [], blood_groups=blood_groups or [])

@app.route('/admin/hospitals', methods=['GET', 'POST'])
@login_required('admin')
def admin_hospitals():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            name = request.form.get('hospital_name', '').strip()
            address = request.form.get('address', '').strip()
            contact = request.form.get('contact_number', '').strip()
            password = 'hospital123'
            
            existing = execute_query("SELECT hospital_id FROM HOSPITAL WHERE contact_number = %s", (contact,), fetchone=True)
            if existing:
                flash('Contact number already registered.', 'error')
            else:
                execute_query(
                    """INSERT INTO HOSPITAL (hospital_name, address, contact_number, password)
                       VALUES (%s, %s, %s, %s)""",
                    (name, address, contact, password),
                    commit=True
                )
                flash('Hospital added! Default password: hospital123', 'success')
        
        elif action == 'edit':
            hospital_id = request.form.get('hospital_id')
            name = request.form.get('hospital_name', '').strip()
            address = request.form.get('address', '').strip()
            contact = request.form.get('contact_number', '').strip()
            
            existing = execute_query("SELECT hospital_id FROM HOSPITAL WHERE contact_number = %s AND hospital_id != %s", (contact, hospital_id), fetchone=True)
            if existing:
                flash('Contact number already registered to another hospital.', 'error')
            else:
                execute_query(
                    """UPDATE HOSPITAL SET hospital_name=%s, address=%s, contact_number=%s
                       WHERE hospital_id=%s""",
                    (name, address, contact, hospital_id),
                    commit=True
                )
                flash('Hospital updated successfully!', 'success')
        
        elif action == 'delete':
            hospital_id = request.form.get('hospital_id')
            execute_query("DELETE FROM HOSPITAL_ADMIN WHERE hospital_id = %s", (hospital_id,), commit=True)
            # Delete related emergency requests and responses
            requests = execute_query(
                "SELECT request_id FROM EMERGENCY_REQUEST WHERE hospital_id = %s",
                (hospital_id,), fetch=True
            )
            if requests:
                for req in requests:
                    execute_query("DELETE FROM RESPONDS_TO WHERE response_id IN (SELECT response_id FROM DONATION_RESPONSE WHERE request_id = %s)", (req['request_id'],), commit=True)
                    execute_query("DELETE FROM MANAGES WHERE response_id IN (SELECT response_id FROM DONATION_RESPONSE WHERE request_id = %s)", (req['request_id'],), commit=True)
                    execute_query("DELETE FROM DONATION_RESPONSE WHERE request_id = %s", (req['request_id'],), commit=True)
                execute_query("DELETE FROM EMERGENCY_REQUEST WHERE hospital_id = %s", (hospital_id,), commit=True)
            execute_query("DELETE FROM HOSPITAL WHERE hospital_id = %s", (hospital_id,), commit=True)
            flash('Hospital deleted successfully!', 'success')
        
        return redirect(url_for('admin_hospitals'))
    
    hospitals = execute_query("SELECT * FROM HOSPITAL ORDER BY hospital_name", fetch=True)
    return render_template('admin/hospitals.html', hospitals=hospitals or [])

@app.route('/admin/requests')
@login_required('admin')
def admin_requests():
    requests_list = execute_query("""
        SELECT er.*, h.hospital_name, bg.blood_group_name
        FROM EMERGENCY_REQUEST er
        JOIN HOSPITAL h ON er.hospital_id = h.hospital_id
        JOIN BLOOD_GROUP bg ON er.blood_group_id = bg.blood_group_id
        ORDER BY FIELD(er.priority_level, 'Critical','High','Medium','Low'), er.request_date DESC
    """, fetch=True)
    return render_template('admin/requests.html', requests=requests_list or [])

@app.route('/admin/requests/update_status', methods=['POST'])
@login_required('admin')
def admin_update_request_status():
    request_id = request.form.get('request_id')
    new_status = request.form.get('status')
    execute_query(
        "UPDATE EMERGENCY_REQUEST SET status = %s WHERE request_id = %s",
        (new_status, request_id), commit=True
    )
    flash('Request status updated.', 'success')
    return redirect(url_for('admin_requests'))

@app.route('/admin/responses')
@login_required('admin')
def admin_responses():
    responses = execute_query("""
        SELECT dr.*, d.donor_name, d.phone, bg.blood_group_name,
               h.hospital_name, er.priority_level, er.units_required
        FROM DONATION_RESPONSE dr
        JOIN DONOR d ON dr.donor_id = d.donor_id
        JOIN EMERGENCY_REQUEST er ON dr.request_id = er.request_id
        JOIN HOSPITAL h ON er.hospital_id = h.hospital_id
        JOIN BLOOD_GROUP bg ON er.blood_group_id = bg.blood_group_id
        ORDER BY dr.response_date DESC
    """, fetch=True)
    return render_template('admin/responses.html', responses=responses or [])

@app.route('/admin/responses/update', methods=['POST'])
@login_required('admin')
def admin_update_response():
    response_id = request.form.get('response_id')
    new_status = request.form.get('response_status')
    admin_id = session['user_id']
    
    execute_query(
        "UPDATE DONATION_RESPONSE SET response_status = %s, admin_id = %s WHERE response_id = %s",
        (new_status, admin_id, response_id), commit=True
    )
    
    # Insert into MANAGES junction table
    execute_query(
        "INSERT IGNORE INTO MANAGES (admin_id, response_id) VALUES (%s, %s)",
        (admin_id, response_id), commit=True
    )
    
    flash('Response status updated.', 'success')
    return redirect(url_for('admin_responses'))

@app.route('/admin/reports')
@login_required('admin')
def admin_reports():
    # Available donors with blood groups
    available_donors = execute_query("""
        SELECT d.donor_name, d.phone, d.age, d.gender, d.address, d.availability_status,
               bg.blood_group_name
        FROM DONOR d
        JOIN BLOOD_GROUP bg ON d.blood_group_id = bg.blood_group_id
        WHERE d.availability_status = 'Available'
        ORDER BY bg.blood_group_name, d.donor_name
    """, fetch=True)
    
    # Blood group distribution
    bg_stats = execute_query("""
        SELECT bg.blood_group_name, COUNT(d.donor_id) as donor_count
        FROM BLOOD_GROUP bg
        LEFT JOIN DONOR d ON bg.blood_group_id = d.blood_group_id
        GROUP BY bg.blood_group_id, bg.blood_group_name
        ORDER BY bg.blood_group_name
    """, fetch=True)
    
    # Request history
    request_history = execute_query("""
        SELECT er.request_id, h.hospital_name, bg.blood_group_name,
               er.units_required, er.priority_level, er.request_date, er.status
        FROM EMERGENCY_REQUEST er
        JOIN HOSPITAL h ON er.hospital_id = h.hospital_id
        JOIN BLOOD_GROUP bg ON er.blood_group_id = bg.blood_group_id
        ORDER BY er.request_date DESC
    """, fetch=True)
    
    # Pending/In-progress requests
    active_requests = execute_query("""
        SELECT er.request_id, h.hospital_name, bg.blood_group_name,
               er.units_required, er.priority_level, er.request_date, er.status
        FROM EMERGENCY_REQUEST er
        JOIN HOSPITAL h ON er.hospital_id = h.hospital_id
        JOIN BLOOD_GROUP bg ON er.blood_group_id = bg.blood_group_id
        WHERE er.status IN ('Pending', 'In Progress')
        ORDER BY FIELD(er.priority_level, 'Critical','High','Medium','Low'), er.request_date ASC
    """, fetch=True)
    
    return render_template('admin/reports.html',
        available_donors=available_donors or [],
        bg_stats=bg_stats or [],
        request_history=request_history or [],
        active_requests=active_requests or []
    )

# ═══════════════════════════════════════════════════════════════════
#  DONOR ROUTES
# ═══════════════════════════════════════════════════════════════════

@app.route('/donor/profile', methods=['GET', 'POST'])
@login_required('donor')
def donor_profile():
    if request.method == 'POST':
        availability = request.form.get('availability_status')
        execute_query(
            "UPDATE DONOR SET availability_status = %s WHERE donor_id = %s",
            (availability, session['user_id']), commit=True
        )
        flash('Availability updated!', 'success')
        return redirect(url_for('donor_profile'))
    
    donor = execute_query("""
        SELECT d.*, bg.blood_group_name
        FROM DONOR d
        JOIN BLOOD_GROUP bg ON d.blood_group_id = bg.blood_group_id
        WHERE d.donor_id = %s
    """, (session['user_id'],), fetchone=True)
    
    return render_template('donor/profile.html', donor=donor)

@app.route('/donor/requests')
@login_required('donor')
def donor_requests():
    requests_list = execute_query("""
        SELECT dr.response_id, dr.response_status, dr.response_date,
               er.request_id, er.units_required, er.priority_level, er.request_date, er.status as request_status,
               h.hospital_name, h.address as hospital_address, h.contact_number,
               bg.blood_group_name
        FROM DONATION_RESPONSE dr
        JOIN EMERGENCY_REQUEST er ON dr.request_id = er.request_id
        JOIN HOSPITAL h ON er.hospital_id = h.hospital_id
        JOIN BLOOD_GROUP bg ON er.blood_group_id = bg.blood_group_id
        WHERE dr.donor_id = %s
        ORDER BY FIELD(er.priority_level, 'Critical','High','Medium','Low'), dr.response_date DESC
    """, (session['user_id'],), fetch=True)
    
    return render_template('donor/requests.html', requests=requests_list or [])

@app.route('/donor/respond/<int:response_id>', methods=['POST'])
@login_required('donor')
def donor_respond(response_id):
    action = request.form.get('action')
    
    if action in ('Accepted', 'Rejected'):
        execute_query(
            "UPDATE DONATION_RESPONSE SET response_status = %s, response_date = NOW() WHERE response_id = %s AND donor_id = %s",
            (action, response_id, session['user_id']), commit=True
        )
        
        # Insert into RESPONDS_TO
        execute_query(
            "INSERT IGNORE INTO RESPONDS_TO (donor_id, response_id) VALUES (%s, %s)",
            (session['user_id'], response_id), commit=True
        )
        
        # If accepted, check if request should be marked as In Progress
        if action == 'Accepted':
            resp = execute_query(
                "SELECT request_id FROM DONATION_RESPONSE WHERE response_id = %s",
                (response_id,), fetchone=True
            )
            if resp:
                execute_query(
                    "UPDATE EMERGENCY_REQUEST SET status = 'In Progress' WHERE request_id = %s AND status = 'Pending'",
                    (resp['request_id'],), commit=True
                )
        
        flash(f'Response {action.lower()} successfully!', 'success')
    
    return redirect(url_for('donor_requests'))

# ═══════════════════════════════════════════════════════════════════
#  HOSPITAL ROUTES
# ═══════════════════════════════════════════════════════════════════

@app.route('/hospital/dashboard')
@login_required('hospital')
def hospital_dashboard():
    total_requests = execute_query(
        "SELECT COUNT(*) as count FROM EMERGENCY_REQUEST WHERE hospital_id = %s",
        (session['user_id'],), fetchone=True
    )['count']
    
    active_requests = execute_query(
        "SELECT COUNT(*) as count FROM EMERGENCY_REQUEST WHERE hospital_id = %s AND status IN ('Pending','In Progress')",
        (session['user_id'],), fetchone=True
    )['count']
    
    fulfilled_requests = execute_query(
        "SELECT COUNT(*) as count FROM EMERGENCY_REQUEST WHERE hospital_id = %s AND status = 'Fulfilled'",
        (session['user_id'],), fetchone=True
    )['count']
    
    recent_requests = execute_query("""
        SELECT er.*, bg.blood_group_name
        FROM EMERGENCY_REQUEST er
        JOIN BLOOD_GROUP bg ON er.blood_group_id = bg.blood_group_id
        WHERE er.hospital_id = %s
        ORDER BY er.request_date DESC LIMIT 10
    """, (session['user_id'],), fetch=True)
    
    return render_template('hospital/dashboard.html',
        total_requests=total_requests,
        active_requests=active_requests,
        fulfilled_requests=fulfilled_requests,
        recent_requests=recent_requests or []
    )

@app.route('/hospital/new_request', methods=['GET', 'POST'])
@login_required('hospital')
def hospital_new_request():
    if request.method == 'POST':
        blood_group_id = request.form.get('blood_group_id')
        units_required = request.form.get('units_required')
        priority_level = request.form.get('priority_level')
        
        execute_query(
            """INSERT INTO EMERGENCY_REQUEST (units_required, priority_level, blood_group_id, hospital_id)
               VALUES (%s, %s, %s, %s)""",
            (units_required, priority_level, blood_group_id, session['user_id']),
            commit=True
        )
        flash('Emergency request created! Matching donors have been notified.', 'success')
        return redirect(url_for('hospital_dashboard'))
    
    blood_groups = execute_query("SELECT * FROM BLOOD_GROUP ORDER BY blood_group_name", fetch=True)
    return render_template('hospital/new_request.html', blood_groups=blood_groups or [])

@app.route('/hospital/track_requests')
@login_required('hospital')
def hospital_track_requests():
    requests_list = execute_query("""
        SELECT er.*, bg.blood_group_name
        FROM EMERGENCY_REQUEST er
        JOIN BLOOD_GROUP bg ON er.blood_group_id = bg.blood_group_id
        WHERE er.hospital_id = %s
        ORDER BY FIELD(er.priority_level, 'Critical','High','Medium','Low'), er.request_date DESC
    """, (session['user_id'],), fetch=True)
    
    return render_template('hospital/track_requests.html', requests=requests_list or [])

@app.route('/hospital/track/<int:request_id>')
@login_required('hospital')
def hospital_track_request(request_id):
    req = execute_query("""
        SELECT er.*, bg.blood_group_name
        FROM EMERGENCY_REQUEST er
        JOIN BLOOD_GROUP bg ON er.blood_group_id = bg.blood_group_id
        WHERE er.request_id = %s AND er.hospital_id = %s
    """, (request_id, session['user_id']), fetchone=True)
    
    if not req:
        flash('Request not found.', 'error')
        return redirect(url_for('hospital_track_requests'))
    
    responses = execute_query("""
        SELECT dr.*, d.donor_name, d.phone, d.age, d.gender
        FROM DONATION_RESPONSE dr
        JOIN DONOR d ON dr.donor_id = d.donor_id
        WHERE dr.request_id = %s
        ORDER BY dr.response_date DESC
    """, (request_id,), fetch=True)
    
    return render_template('hospital/track_request_detail.html', req=req, responses=responses or [])

@app.route('/hospital/search_donors')
@login_required('hospital')
def hospital_search_donors():
    blood_groups = execute_query("SELECT * FROM BLOOD_GROUP ORDER BY blood_group_name", fetch=True)
    donors = []
    selected_bg = request.args.get('blood_group', '')
    
    if selected_bg:
        donors = call_procedure('SearchAvailableDonors', [selected_bg]) or []
    
    return render_template('hospital/search_donors.html',
        blood_groups=blood_groups or [],
        donors=donors,
        selected_bg=selected_bg
    )

# ─── Error Handlers ──────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template('index.html'), 404

# ─── Main ────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)
