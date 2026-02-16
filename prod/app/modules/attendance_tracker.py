"""
Attendance Tracking Module

A standalone module for daily attendance tracking and reporting.

Features:
- Daily attendance marking (present/late with minutes late)
- Daily, weekly, monthly attendance reports
- Integration with existing schedule system

Usage in another project:
1. Copy this file to your project's app/modules/ directory
2. Register the blueprint in your app's __init__.py:
   from app.modules.attendance_tracker import attendance_bp
   app.register_blueprint(attendance_bp, url_prefix='/attendance')
"""

from datetime import datetime, timedelta, time
from flask import Blueprint, render_template, request, jsonify
from app import db
from app.models import Employee, Schedule, Attendance, LeaveRequest, ExceptionRecord

attendance_bp = Blueprint('attendance_tracker', __name__, template_folder='templates')


# ==================== MODEL EXTENSIONS ====================

def add_attendance_fields():
    """Add late_minutes field to attendance records (called once during setup)."""
    try:
        # This should be run once to add the column
        with db.engine.connect() as conn:
            result = conn.execute(db.text(
                "SELECT COUNT(*) FROM pragma_table_info('attendances') WHERE name='late_minutes'"
            )).fetchone()
            if result[0] == 0:
                conn.execute(db.text("ALTER TABLE attendances ADD COLUMN late_minutes INTEGER DEFAULT 0"))
                conn.commit()
        return True
    except Exception:
        return False


# ==================== HELPER FUNCTIONS ====================

def get_todays_schedules():
    """Get all schedules for today."""
    today = datetime.utcnow().date()
    schedules = Schedule.query.filter(
        Schedule.start_date == today,
        Schedule.employee_id == Employee.employee_id
    ).join(Employee).order_by(Employee.last_name).all()
    return schedules


def get_employee_attendance_status(employee_id, date):
    """Get attendance status for an employee on a specific date."""
    attendance = Attendance.query.filter_by(
        employee_id=employee_id,
        date=date
    ).first()
    return attendance


def get_today_exceptions():
    """Get today's exceptions (vacations, coverups, etc.)."""
    today = datetime.utcnow().date()
    exceptions = ExceptionRecord.query.filter(
        ExceptionRecord.start_date <= today,
        ExceptionRecord.end_date >= today,
        ExceptionRecord.status != 'Completed'
    ).all()
    return exceptions


# ==================== ROUTES ====================

@attendance_bp.route('/attendance')
def attendance_page():
    """Daily attendance tracking page."""
    today = datetime.utcnow().date()

    # Get all employees scheduled for today
    schedules = get_todays_schedules()

    # Get today's exceptions
    exceptions = get_today_exceptions()

    # Build exception mapping by employee ID
    exception_map = {}
    for exc in exceptions:
        exception_map[exc.employee_id] = exc

    # Get attendance for each scheduled employee
    attendance_records = {}
    for schedule in schedules:
        att = get_employee_attendance_status(schedule.employee_id, today)
        attendance_records[schedule.employee_id] = att

    return render_template(
        'attendance_tracker/daily_attendance.html',
        schedules=schedules,
        attendance_records=attendance_records,
        exceptions=exceptions,
        exception_map=exception_map,
        today=today
    )


@attendance_bp.route('/attendance/mark', methods=['POST'])
def mark_attendance():
    """Mark attendance for an employee."""
    data = request.get_json()

    employee_id = data.get('employee_id')
    date_str = data.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
    status = data.get('status')  # 'present', 'late', 'absent', 'early_leave', 'overtime', 'cover_up', 'on_leave'
    late_minutes = data.get('late_minutes', 0)
    early_leave_time = data.get('early_leave_time')  # Format: "HH:MM"
    overtime_minutes = data.get('overtime_minutes', 0)
    cover_up_for_id = data.get('cover_up_for_employee_id')
    notes = data.get('notes', '')

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # Parse early leave time if provided
    early_leave = None
    if early_leave_time:
        try:
            parts = early_leave_time.split(':')
            early_leave = time(int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            return jsonify({'error': 'Invalid early leave time format'}), 400

    # Check if employee is scheduled for this date
    schedule = Schedule.query.filter_by(
        employee_id=employee_id,
        start_date=date
    ).first()

    if not schedule and status not in ['on_leave', 'cover_up']:
        # Check if on leave/exception
        exception = ExceptionRecord.query.filter(
            ExceptionRecord.employee_id == employee_id,
            ExceptionRecord.start_date <= date,
            ExceptionRecord.end_date >= date,
            ExceptionRecord.status != 'Completed'
        ).first()

        if not exception:
            return jsonify({'error': 'Employee not scheduled for this date'}), 400

    # Check if attendance record exists
    attendance = Attendance.query.filter_by(
        employee_id=employee_id,
        date=date
    ).first()

    if attendance:
        # Update existing record
        if status == 'present':
            attendance.exception_type = None
            attendance.late_minutes = 0
            attendance.early_leave = None
            attendance.overtime_minutes = 0
            attendance.cover_up_for_employee_id = None
            attendance.notes = notes
        elif status == 'late':
            attendance.exception_type = 'Late'
            attendance.late_minutes = late_minutes
            attendance.notes = notes
        elif status == 'absent':
            attendance.exception_type = 'Absent'
            attendance.late_minutes = None
            attendance.notes = notes
        elif status == 'early_leave':
            attendance.exception_type = 'Early Leave'
            attendance.early_leave = early_leave
            attendance.notes = notes
        elif status == 'overtime':
            attendance.exception_type = 'Overtime'
            attendance.overtime_minutes = overtime_minutes
            attendance.notes = notes
        elif status == 'cover_up':
            attendance.exception_type = 'Cover Up'
            attendance.cover_up_for_employee_id = cover_up_for_id
            attendance.notes = notes
        elif status == 'on_leave':
            attendance.exception_type = 'Leave'
            attendance.late_minutes = None
            attendance.notes = notes
    else:
        # Create new record
        attendance = Attendance(
            employee_id=employee_id,
            date=date,
            exception_type='Absent' if status == 'absent' else
                        'Late' if status == 'late' else
                        'Early Leave' if status == 'early_leave' else
                        'Overtime' if status == 'overtime' else
                        'Cover Up' if status == 'cover_up' else
                        'Leave' if status == 'on_leave' else None,
            late_minutes=late_minutes if status == 'late' else None,
            early_leave=early_leave if status == 'early_leave' else None,
            overtime_minutes=overtime_minutes if status == 'overtime' else None,
            cover_up_for_employee_id=cover_up_for_id if status == 'cover_up' else None,
            notes=notes
        )
        db.session.add(attendance)

    db.session.commit()

    return jsonify({
        'message': 'Attendance marked successfully',
        'attendance_id': attendance.attendance_id
    })


@attendance_bp.route('/attendance/report/daily')
def daily_report():
    """Daily attendance report."""
    date_str = request.args.get('date', datetime.utcnow().strftime('%Y-%m-%d'))

    try:
        report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # Get all attendance for the date
    attendances = Attendance.query.filter_by(date=report_date).all()

    # Calculate summary
    total_scheduled = Schedule.query.filter_by(start_date=report_date).count()
    present = Attendance.query.filter_by(date=report_date).count()
    late = Attendance.query.filter(
        Attendance.date == report_date,
        Attendance.late_minutes > 0
    ).count()
    absent = Attendance.query.filter(
        Attendance.date == report_date,
        Attendance.exception_type.in_(['Absent', 'Leave'])
    ).count()

    # Get late employees with details
    late_employees = db.session.query(Attendance, Employee).join(
        Employee
    ).filter(
        Attendance.date == report_date,
        Attendance.late_minutes > 0
    ).all()

    return render_template(
        'attendance_tracker/daily_report.html',
        report_date=report_date,
        attendances=attendances,
        total_scheduled=total_scheduled,
        present=present,
        late=late,
        absent=absent,
        late_employees=late_employees
    )


@attendance_bp.route('/attendance/report/weekly')
def weekly_report():
    """Weekly attendance report (last 7 days)."""
    end_date = request.args.get('end_date', datetime.utcnow().strftime('%Y-%m-%d'))

    try:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    start_date = end_date_obj - timedelta(days=6)

    # Get attendance for the week
    weekly_attendances = Attendance.query.filter(
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).all()

    # Calculate daily summaries
    daily_stats = {}
    for day in range(7):
        current_date = start_date + timedelta(days=day)
        date_str = current_date.strftime('%Y-%m-%d')
        day_attendances = [a for a in weekly_attendances if a.date == current_date]

        daily_stats[date_str] = {
            'date': date_str,
            'present': len(day_attendances),
            'late': len([a for a in day_attendances if a.late_minutes and a.late_minutes > 0]),
            'absent': len([a for a in day_attendances if a.exception_type in ['Absent', 'Leave']]),
            'early_leave': len([a for a in day_attendances if a.exception_type == 'Early Leave']),
            'overtime': len([a for a in day_attendances if a.exception_type == 'Overtime']),
            'cover_up': len([a for a in day_attendances if a.exception_type == 'Cover Up']),
            'total_scheduled': Schedule.query.filter_by(start_date=current_date).count()
        }

    return render_template(
        'attendance_tracker/weekly_report.html',
        start_date=start_date,
        end_date=end_date,
        daily_stats=daily_stats,
        weekly_attendances=weekly_attendances
    )


@attendance_bp.route('/attendance/report/monthly')
def monthly_report():
    """Monthly attendance report."""
    year_str = request.args.get('year', datetime.utcnow().strftime('%Y'))
    month_str = request.args.get('month', datetime.utcnow().strftime('%m'))

    try:
        year = int(year_str)
        month = int(month_str)
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # Get first and last day of month
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()

    # Get attendance for the month
    monthly_attendances = Attendance.query.filter(
        Attendance.date >= start_date,
        Attendance.date < end_date
    ).all()

    # Calculate summary by employee
    employee_stats = {}
    for att in monthly_attendances:
        emp_id = att.employee_id
        if emp_id not in employee_stats:
            employee_stats[emp_id] = {
                'name': f'{att.employee.first_name} {att.employee.last_name}' if att.employee else 'Unknown',
                'present': 0,
                'late': 0,
                'absent': 0,
                'total_late_minutes': 0
            }

        if att.exception_type in ['Absent', 'Leave']:
            employee_stats[emp_id]['absent'] += 1
        elif att.late_minutes and att.late_minutes > 0:
            employee_stats[emp_id]['present'] += 1
            employee_stats[emp_id]['late'] += 1
            employee_stats[emp_id]['total_late_minutes'] += att.late_minutes
        else:
            employee_stats[emp_id]['present'] += 1

    # Sort by name
    sorted_stats = sorted(employee_stats.items(), key=lambda x: x[1]['name'])

    return render_template(
        'attendance_tracker/monthly_report.html',
        year=year,
        month=month,
        employee_stats=dict(sorted_stats),
        monthly_attendances=monthly_attendances
    )


@attendance_bp.route('/api/attendance/today')
def api_today_attendance():
    """API endpoint for today's attendance data."""
    today = datetime.utcnow().date()

    schedules = Schedule.query.filter_by(start_date=today).all()
    attendance = {a.employee_id: a for a in Attendance.query.filter_by(date=today).all()}

    data = []
    for schedule in schedules:
        emp = schedule.employee
        att = attendance.get(schedule.employee_id)

        status = 'not_marked'
        late_minutes = None

        if att:
            if att.exception_type in ['Absent', 'Leave']:
                status = 'absent'
            elif att.late_minutes and att.late_minutes > 0:
                status = 'late'
                late_minutes = att.late_minutes
            else:
                status = 'present'

        data.append({
            'employee_id': emp.employee_id,
            'name': f'{emp.first_name} {emp.last_name}',
            'scheduled_start': str(schedule.start_time) if schedule.start_time else None,
            'status': status,
            'late_minutes': late_minutes,
            'attendance_id': att.attendance_id if att else None
        })

    return jsonify({
        'date': today.strftime('%Y-%m-%d'),
        'data': data
    })
