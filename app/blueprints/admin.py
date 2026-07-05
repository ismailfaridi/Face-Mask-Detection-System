from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.db import Admin, DatabaseManager

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles administrator login.
    
    In POST: Validates credentials and starts an admin session.
    In GET: Renders the admin login page.
    
    Returns:
        str: Rendered HTML for the login page or a redirect to the dashboard.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin_model = Admin(username)
        if admin_model.login(username, password):
            session['admin_logged_in'] = True
            session['username'] = username
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials.', 'error')
            
    return render_template('login.html')

@admin_bp.route('/logout')
def logout():
    """
    Clears the administrator session and logs out the user.
    
    Returns:
        Response: Redirects to the main index page.
    """
    session.clear() # clears all data stored in the session
    flash('Logged out successfully.', 'success')
    return redirect(url_for('main.index'))

@admin_bp.route('/dashboard')
def dashboard():
    """
    Displays the admin dashboard with system statistics and detection records.
    Requires the administrator to be logged in.
    
    Returns:
        str: Rendered HTML for the admin dashboard or a redirect to login page.
    """
    if session.get('admin_logged_in') is None:
        return redirect(url_for('admin.login'))
    
    db = DatabaseManager()
    stats = db.getStatistics()
    all_records = db.getAllRecords()
    recent_records = db.getRecentRecords(50)

    return render_template('dashboard.html',
                           stats=stats,
                           all_records=all_records,
                           recent_records=recent_records)

@admin_bp.route('/clear_records', methods=['POST'])
def clear_records():
    """
    Clears all detection records from the database and removes all uploaded images.
    Requires the administrator to be logged in.
    """
    if session.get('admin_logged_in') is None:
        return redirect(url_for('admin.login'))
        
    try:
        db = DatabaseManager()
        db.clearAllRecords()
        flash('All historical records and uploaded images have been successfully cleared.', 'success')
    except Exception as e:
        flash(f'An error occurred while clearing records: {str(e)}', 'error')
        
    return redirect(url_for('admin.dashboard'))