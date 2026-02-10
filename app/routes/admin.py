from flask import Blueprint, render_template

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Home page."""
    return render_template('index.html')


@bp.route('/dashboard')
def dashboard():
    """Dashboard with overview statistics."""
    return render_template('dashboard.html')


@bp.route('/employees')
def employees():
    """Employee management."""
    return render_template('employees.html')


@bp.route('/schedules')
def schedules():
    """Schedule management."""
    return render_template('schedules.html')


@bp.route('/attendance')
def attendance():
    """Attendance management."""
    return render_template('attendance.html')


@bp.route('/exceptions')
def exceptions():
    """Exception records."""
    return render_template('exceptions.html')


@bp.route('/admin/options')
def admin_options():
    """Admin options management."""
    return render_template('admin_options.html')


@bp.route('/rewards')
def rewards():
    """Reward program."""
    return render_template('rewards.html')
