from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from app.models.db import Admin, DatabaseManager
import functools

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get('admin_logged_in') is None:
            return redirect(url_for('admin.login'))
        return view(**kwargs)
    return wrapped_view

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
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
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('main.index'))

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    db = DatabaseManager()
    stats = db.getStatistics()
    records = db.getAllRecords()
    return render_template('dashboard.html', stats=stats, records=records)