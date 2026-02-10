from datetime import datetime, date, timedelta
from app import db
from app.models import Employee, Schedule, Attendance, EmployeeHistory, ScheduleHistory, AttendanceHistory


def archive_old_schedules():
    """
    Move schedules older than SCHEDULE_RETENTION_DAYS to history table.
    Returns the count of archived records.
    """
    from app.config import config
    config_obj = config['default']
    retention_days = config_obj.SCHEDULE_RETENTION_DAYS

    cutoff_date = date.today() - timedelta(days=retention_days)

    # Find schedules to archive
    old_schedules = Schedule.query.filter(Schedule.start_date < cutoff_date).all()

    archived_count = 0
    for schedule in old_schedules:
        history = ScheduleHistory(
            schedule_id=schedule.schedule_id,
            employee_id=schedule.employee_id,
            start_date=schedule.start_date,
            start_time=schedule.start_time,
            stop_date=schedule.stop_date,
            stop_time=schedule.stop_time,
            work_code=schedule.work_code
        )
        db.session.add(history)
        db.session.delete(schedule)
        archived_count += 1

    db.session.commit()
    return archived_count


def archive_old_attendances():
    """
    Move attendances older than ATTENDANCE_RETENTION_DAYS to history table.
    Returns the count of archived records.
    """
    from app.config import config
    config_obj = config['default']
    retention_days = config_obj.ATTENDANCE_RETENTION_DAYS

    cutoff_date = date.today() - timedelta(days=retention_days)

    # Find attendances to archive
    old_attendances = Attendance.query.filter(Attendance.date < cutoff_date).all()

    archived_count = 0
    for attendance in old_attendances:
        history = AttendanceHistory(
            attendance_id=attendance.attendance_id,
            employee_id=attendance.employee_id,
            date=attendance.date,
            check_in=attendance.check_in,
            check_out=attendance.check_out,
            exception_type=attendance.exception_type,
            notes=attendance.notes
        )
        db.session.add(history)
        db.session.delete(attendance)
        archived_count += 1

    db.session.commit()
    return archived_count


def move_employee_to_history(employee_id):
    """
    Move an employee to history table and delete from active table.
    """
    employee = Employee.query.get_or_404(employee_id)

    history = EmployeeHistory(
        employee_id=employee.employee_id,
        first_name=employee.first_name,
        last_name=employee.last_name,
        full_name=employee.full_name,
        company_email=employee.company_email,
        access_card=employee.access_card,
        token_serial=employee.token_serial,
        building_card=employee.building_card,
        batch=employee.batch,
        agent_id=employee.agent_id,
        bo_user=employee.bo_user,
        axonify=employee.axonify,
        supervisor=employee.supervisor,
        manager=employee.manager,
        tier=employee.tier,
        shift=employee.shift,
        department=employee.department,
        role=employee.role,
        hire_date=employee.hire_date,
        status=employee.status,
        attrition_date=employee.attrition_date
    )

    db.session.add(history)
    db.session.delete(employee)
    db.session.commit()


def cleanup_inactive_employees():
    """
    Move all inactive employees to history and delete from active table.
    Returns count of cleaned up employees.
    """
    inactive_employees = Employee.query.filter_by(status='Inactive').all()

    cleaned_count = 0
    for employee in inactive_employees:
        move_employee_to_history(employee.employee_id)
        cleaned_count += 1

    return cleaned_count


def process_exception_record(exception_id):
    """
    Process an exception record and create corresponding schedule.
    Handles Training, Nesting, New Hire Training, Vacation, Swap, Cover.
    """
    from app.models import ExceptionRecord

    exception = ExceptionRecord.query.get_or_404(exception_id)

    # Create schedule based on exception type
    schedule = Schedule(
        employee_id=exception.employee_id,
        start_date=exception.start_date,
        stop_date=exception.end_date,
        work_code=exception.work_code
    )

    # Handle time based on exception type
    if exception.exception_type in ['Vacation', 'Sick']:
        # Full day off - set times to indicate OFF
        schedule.start_time = None
        schedule.stop_time = None
    else:
        # Training/Nesting - use default work hours
        schedule.start_time = datetime.strptime('06:00', '%H:%M').time()
        schedule.stop_time = datetime.strptime('15:00', '%H:%M').time()

    db.session.add(schedule)
    exception.status = 'Completed'
    exception.processed_at = datetime.utcnow()
    db.session.commit()

    return schedule
