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
    schedules = Schedule.query.join(
        Employee
    ).filter(
        Schedule.start_date == today
    ).order_by(Employee.last_name).all()
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

@attendance_bp.route('/daily')
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


@attendance_bp.route('/daily/mark', methods=['POST'])
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
        # Set check_in and check_out based on shift time if available
        check_in = None
        check_out = None
        if schedule:
            check_in = schedule.start_time
            check_out = schedule.stop_time

        attendance = Attendance(
            employee_id=employee_id,
            date=date,
            check_in=check_in,
            check_out=check_out,
            exception_type='Absent' if status == 'absent' else
                        'Late' if status == 'late' else
                        'Early Leave' if status == 'early_leave' else
                        'Overtime' if status == 'overtime' else
                        'Cover Up' if status == 'cover_up' else
                        'Leave' if status == 'on_leave' else None,
            late_minutes=late_minutes if status in ['late', 'present'] else None,
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


@attendance_bp.route('/mark', methods=['POST'])
def mark_attendance_legacy():
    """Legacy endpoint for marking attendance (used by daily_attendance.html)."""
    return mark_attendance()


@attendance_bp.route('/report/daily')
def daily_report():
    """Daily attendance report for today - all schedules with attendance marking."""
    report_date = datetime.utcnow().date()

    # Get all schedules for the day (not just attendance records)
    # Only include schedules with valid start_time and stop_time (employees with no schedule time are OFF)
    schedules = Schedule.query.join(
        Employee
    ).filter(
        Schedule.start_date == report_date,
        Schedule.start_time.isnot(None),
        Schedule.stop_time.isnot(None)
    ).order_by(Employee.last_name).all()

    # Get attendance records for the day (indexed by employee_id)
    attendance_records = Attendance.query.filter_by(date=report_date).all()
    attendance_by_employee = {a.employee_id: a for a in attendance_records}

    # Get exceptions for the day that indicate the person is off
    # (Vacation, Training, Nesting, Leave - any completed exception)
    exceptions = ExceptionRecord.query.filter(
        ExceptionRecord.start_date <= report_date,
        ExceptionRecord.end_date >= report_date,
        ExceptionRecord.exception_type.in_(['Vacation', 'Training', 'Nesting', 'Leave'])
    ).all()
    off_employee_ids = {e.employee_id for e in exceptions}

    # Also include people marked Absent or On Leave in attendance
    for att in attendance_records:
        if att.exception_type in ['Absent', 'Leave', 'Early Leave']:
            off_employee_ids.add(att.employee_id)

    # Filter out people who are off
    filtered_schedules = [s for s in schedules if s.employee_id not in off_employee_ids]
    # Re-index attendance for filtered list
    filtered_attendance = {emp_id: att for emp_id, att in attendance_by_employee.items() if emp_id not in off_employee_ids}

    # Calculate summary (only for people who are working)
    total_scheduled = len(filtered_schedules)
    present = len([s for s in filtered_schedules if filtered_attendance.get(s.employee_id) and
                   filtered_attendance[s.employee_id].exception_type not in ['Absent', 'Leave']])
    late = len([s for s in filtered_schedules if filtered_attendance.get(s.employee_id) and
                filtered_attendance[s.employee_id].late_minutes > 0])
    absent = len([s for s in filtered_schedules if filtered_attendance.get(s.employee_id) and
                  filtered_attendance[s.employee_id].exception_type in ['Absent', 'Leave']])

    return render_template(
        'attendance_tracker/daily_report.html',
        report_date=report_date,
        schedules=filtered_schedules,
        attendance_by_employee=filtered_attendance,
        total_scheduled=total_scheduled,
        present=present,
        late=late,
        absent=absent
    )


@attendance_bp.route('/report/weekly')
def weekly_report():
    """Weekly attendance report (week to date from Monday)."""
    end_date = datetime.utcnow().date()

    # Get filter parameters
    department = request.args.get('department')
    supervisor = request.args.get('supervisor')
    batch = request.args.get('batch')
    exception_type = request.args.get('exception_type')

    # Calculate start of week (Monday)
    days_since_monday = end_date.weekday()  # Monday = 0, Sunday = 6
    start_date = end_date - timedelta(days=days_since_monday)

    # Build query with filters
    query = db.session.query(Attendance, Employee).join(
        Employee, Attendance.employee_id == Employee.employee_id
    ).filter(
        Attendance.date >= start_date,
        Attendance.date <= end_date
    )

    if department:
        query = query.filter(Employee.department == department)
    if supervisor:
        query = query.filter(Employee.supervisor == supervisor)
    if batch:
        query = query.filter(Employee.batch == batch)
    if exception_type:
        query = query.filter(Attendance.exception_type == exception_type)

    weekly_attendances = query.all()

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

    # Calculate summary cards
    total_scheduled = Schedule.query.filter(
        Schedule.start_date >= start_date,
        Schedule.start_date <= end_date
    ).count()

    present_count = len(weekly_attendances)
    late_count = len([a for a in weekly_attendances if a.late_minutes and a.late_minutes > 0])
    absent_count = len([a for a in weekly_attendances if a.exception_type in ['Absent', 'Leave']])

    return render_template(
        'attendance_tracker/weekly_report.html',
        datetime=datetime,  # Pass datetime for template use
        start_date=start_date,
        end_date=end_date,
        daily_stats=daily_stats,
        weekly_attendances=weekly_attendances,
        attendances=weekly_attendances,
        present=present_count,
        late=late_count,
        absent=absent_count,
        total_scheduled=total_scheduled
    )


@attendance_bp.route('/report/monthly')
def monthly_report():
    """Monthly attendance report (month to date from 1st)."""
    # Get filter parameters
    department = request.args.get('department')
    supervisor = request.args.get('supervisor')
    batch = request.args.get('batch')
    exception_type = request.args.get('exception_type')

    # Get current year and month
    now = datetime.utcnow()
    year = now.year
    month = now.month

    # Get first and last day of month
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()

    # Build query with filters
    query = db.session.query(Attendance, Employee).join(
        Employee, Attendance.employee_id == Employee.employee_id
    ).filter(
        Attendance.date >= start_date,
        Attendance.date < end_date
    )

    if department:
        query = query.filter(Employee.department == department)
    if supervisor:
        query = query.filter(Employee.supervisor == supervisor)
    if batch:
        query = query.filter(Employee.batch == batch)
    if exception_type:
        query = query.filter(Attendance.exception_type == exception_type)

    monthly_attendances = query.all()

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


@attendance_bp.route('/api/today')
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


@attendance_bp.route('/exceptions')
def exception_list():
    """List of pending and processed exceptions."""
    exceptions = ExceptionRecord.query.order_by(ExceptionRecord.created_at.desc()).all()
    return render_template('attendance_tracker/exception_list.html', exceptions=exceptions)


@attendance_bp.route('/exceptions/create', methods=['POST'])
def create_exception():
    """Create a new exception (Cover Up, Overtime, Vacation, Training, Nesting, Leave)."""
    data = request.get_json()

    employee_id = data.get('employee_id')
    exception_type = data.get('exception_type')  # Cover Up, Overtime, Vacation, Training, Nesting, Leave
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')  # Optional, same as start_date for single day
    overtime_minutes = data.get('overtime_minutes', 0)
    overtime_end_time = data.get('overtime_end_time')  # HH:MM format
    cover_up_for_id = data.get('cover_up_for_employee_id')  # For Cover Up type
    notes = data.get('notes', '')

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid start date format'}), 400

    end_date = start_date
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid end date format'}), 400

    # Validate exception type
    valid_types = ['Cover Up', 'Overtime', 'Vacation', 'Training', 'Nesting', 'Leave']
    if exception_type not in valid_types:
        return jsonify({'error': f'Invalid exception type. Must be one of: {valid_types}'}), 400

    # Create the exception record
    exception = ExceptionRecord(
        employee_id=employee_id,
        exception_type=exception_type,
        start_date=start_date,
        end_date=end_date,
        notes=notes
    )

    db.session.add(exception)
    db.session.commit()

    # If Overtime, also create an attendance record for the extra time
    if exception_type == 'Overtime':
        attendance = Attendance(
            employee_id=employee_id,
            date=start_date,
            exception_type='Overtime',
            overtime_minutes=overtime_minutes,
            notes=f"Overtime: {overtime_end_time if overtime_end_time else f'{overtime_minutes} minutes'}"
        )
        db.session.add(attendance)

    # If Cover Up, also create an attendance record
    elif exception_type == 'Cover Up':
        attendance = Attendance(
            employee_id=employee_id,
            date=start_date,
            exception_type='Cover Up',
            cover_up_for_employee_id=cover_up_for_id,
            notes=notes
        )
        db.session.add(attendance)

    db.session.commit()

    return jsonify({
        'message': f'Exception created successfully',
        'exception_id': exception.exception_id
    })


@attendance_bp.route('/exceptions/process/<int:exception_id>', methods=['POST'])
def process_exception(exception_id):
    """Process an exception (mark as Completed)."""
    exception = ExceptionRecord.query.get(exception_id)
    if not exception:
        return jsonify({'error': 'Exception not found'}), 404

    exception.status = 'Completed'
    db.session.commit()

    return jsonify({'message': 'Exception processed successfully'})
