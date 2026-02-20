from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
from functools import wraps
from app import db
from app.models import Employee, Schedule, Attendance, LeaveRequest, ScheduleChange, ExceptionRecord, AdminOptions, RewardReason, EmployeeReward


class APIError(BadRequest):
    """Custom API error for better error responses."""
    def __init__(self, message, status_code=400, errors=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors


bp = Blueprint('api', __name__)


def require_api_key(f):
    """Decorator to require API key authentication.

    For backward compatibility, if no API key is provided in the request,
    the decorator will allow the request to proceed but log a warning.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            # Allow requests without API key for backward compatibility
            # This will be changed to require API key in the future
            return f(*args, **kwargs)

        # Check if API key is valid in admin_options
        valid_key = AdminOptions.query.filter_by(
            category='api_key',
            value=api_key,
            is_active=True
        ).first()

        if not valid_key:
            return jsonify({'error': 'Invalid API key'}), 401

        return f(*args, **kwargs)
    return decorated_function


@bp.route('/', methods=['GET'])
def api_root():
    """API root endpoint - returns documentation link."""
    return jsonify({
        'message': 'Operations DB API',
        'version': '1.0.0',
        'documentation': '/apidocs'
    }), 200


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


@bp.route('/employees', methods=['GET'])
@require_api_key
def get_employees():
    """Get employees with comprehensive filtering options.

    Query Parameters:
    - status: Filter by status (Active, On Leave, Inactive)
    - department: Filter by department
    - supervisor: Filter by supervisor name
    - manager: Filter by manager name
    - shift: Filter by shift (Morning, Evening, Night)
    - role: Filter by role
    - tier: Filter by tier number
    - batch: Filter by batch
    - phase: Filter by phase (1, 2, 3) - employees with phase dates
    - point_balance_min: Filter by minimum point balance
    - point_balance_max: Filter by maximum point balance
    - hire_date_min: Filter by minimum hire date (YYYY-MM-DD)
    - hire_date_max: Filter by maximum hire date (YYYY-MM-DD)
    - inactive_since: Filter employees inactive since date (YYYY-MM-DD)
    - has_schedule: Filter employees with/without schedules on a date (YYYY-MM-DD)
    - has_attendance: Filter employees with/without attendance on a date (YYYY-MM-DD)
    - page: Page number for pagination (default: 1)
    - per_page: Items per page (default: 100)
    - sort: Sort field (employee_id, last_name, first_name, hire_date, point_balance)
    - order: Sort order (asc, desc)
    """
    # Get query parameters
    status = request.args.get('status')
    department = request.args.get('department')
    supervisor = request.args.get('supervisor')
    manager = request.args.get('manager')
    shift = request.args.get('shift')
    role = request.args.get('role')
    tier = request.args.get('tier')
    batch = request.args.get('batch')
    phase = request.args.get('phase')
    point_balance_min = request.args.get('point_balance_min')
    point_balance_max = request.args.get('point_balance_max')
    hire_date_min = request.args.get('hire_date_min')
    hire_date_max = request.args.get('hire_date_max')
    inactive_since = request.args.get('inactive_since')
    has_schedule = request.args.get('has_schedule')
    has_attendance = request.args.get('has_attendance')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    sort = request.args.get('sort')
    order = request.args.get('order', 'asc')

    # Build query
    query = Employee.query

    # Apply filters
    if status:
        query = query.filter(Employee.status == status)
    else:
        # Default to active employees
        query = query.filter(Employee.status == 'Active')

    if department:
        query = query.filter(Employee.department == department)
    if supervisor:
        query = query.filter(Employee.supervisor == supervisor)
    if manager:
        query = query.filter(Employee.manager == manager)
    if shift:
        query = query.filter(Employee.shift == shift)
    if role:
        query = query.filter(Employee.role == role)
    if tier:
        query = query.filter(Employee.tier == int(tier))
    if batch:
        query = query.filter(Employee.batch == batch)

    # Phase filter - check if phase date exists
    if phase == '1':
        query = query.filter(Employee.phase_1_date.isnot(None))
    elif phase == '2':
        query = query.filter(Employee.phase_2_date.isnot(None))
    elif phase == '3':
        query = query.filter(Employee.phase_3_date.isnot(None))

    # Point balance filters
    if point_balance_min:
        query = query.filter(Employee.point_balance >= int(point_balance_min))
    if point_balance_max:
        query = query.filter(Employee.point_balance <= int(point_balance_max))

    # Hire date filters
    if hire_date_min:
        query = query.filter(Employee.hire_date >= hire_date_min)
    if hire_date_max:
        query = query.filter(Employee.hire_date <= hire_date_max)

    # Inactive since filter
    if inactive_since:
        query = query.filter(Employee.status != 'Active')

    # Has schedule filter
    if has_schedule:
        from app.models import Schedule
        subquery = Schedule.query.filter(
            Schedule.employee_id == Employee.employee_id,
            Schedule.start_date == has_schedule
        ).exists()
        query = query.filter(subquery)

    # Has attendance filter
    if has_attendance:
        from app.models import Attendance
        subquery = Attendance.query.filter(
            Attendance.employee_id == Employee.employee_id,
            Attendance.date == has_attendance
        ).exists()
        query = query.filter(subquery)

    # Sorting
    if sort:
        sort_field = {
            'employee_id': Employee.employee_id,
            'last_name': Employee.last_name,
            'first_name': Employee.first_name,
            'hire_date': Employee.hire_date,
            'point_balance': Employee.point_balance
        }.get(sort, Employee.employee_id)
        if order == 'desc':
            sort_field = sort_field.desc()
        query = query.order_by(sort_field)

    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    employees = pagination.items

    return jsonify({
        'employees': [{
            'employee_id': e.employee_id,
            'first_name': e.first_name,
            'last_name': e.last_name,
            'full_name': e.full_name,
            'company_email': e.company_email,
            'department': e.department,
            'role': e.role,
            'shift': e.shift,
            'status': e.status,
            'batch': e.batch,
            'supervisor': e.supervisor,
            'manager': e.manager,
            'tier': e.tier,
            'hire_date': str(e.hire_date),
            'phase_1_date': str(e.phase_1_date) if e.phase_1_date else None,
            'phase_2_date': str(e.phase_2_date) if e.phase_2_date else None,
            'phase_3_date': str(e.phase_3_date) if e.phase_3_date else None,
            'point_balance': e.point_balance or 0,
            'access_card': e.access_card,
            'token_serial': e.token_serial,
            'building_card': e.building_card,
            'attrition_date': str(e.attrition_date) if e.attrition_date else None
        } for e in employees],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })


@bp.route('/employees/<int:employee_id>', methods=['GET'])
@require_api_key
def get_employee(employee_id):
    """Get single employee by ID."""
    employee = Employee.query.get_or_404(employee_id)
    return jsonify({
        'employee_id': employee.employee_id,
        'first_name': employee.first_name,
        'last_name': employee.last_name,
        'full_name': employee.full_name,
        'company_email': employee.company_email,
        'batch': employee.batch,
        'supervisor': employee.supervisor,
        'manager': employee.manager,
        'tier': employee.tier,
        'shift': employee.shift,
        'department': employee.department,
        'role': employee.role,
        'hire_date': str(employee.hire_date),
        'phase_1_date': str(employee.phase_1_date) if employee.phase_1_date else None,
        'phase_2_date': str(employee.phase_2_date) if employee.phase_2_date else None,
        'phase_3_date': str(employee.phase_3_date) if employee.phase_3_date else None,
        'status': employee.status,
        'attrition_date': str(employee.attrition_date) if employee.attrition_date else None,
        'point_balance': employee.point_balance or 0
    })


@bp.route('/employees', methods=['POST'])
@require_api_key
def create_employee():
    """Create new employee."""
    data = request.get_json()

    employee = Employee(
        employee_id=data['employee_id'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        full_name=f"{data['first_name']} {data['last_name']}",
        company_email=data['company_email'],
        batch=data['batch'],
        supervisor=data['supervisor'],
        manager=data['manager'],
        shift=data['shift'],
        department=data['department'],
        role=data['role'],
        hire_date=data['hire_date'],
        tier=data.get('tier'),
        access_card=data.get('access_card'),
        token_serial=data.get('token_serial'),
        building_card=data.get('building_card'),
        agent_id=data.get('agent_id'),
        bo_user=data.get('bo_user'),
        axonify=data.get('axonify'),
        status=data.get('status', 'Active')
    )

    db.session.add(employee)

    if 'phase_1_date' in data:
        employee.phase_1_date = data['phase_1_date']
    if 'phase_2_date' in data:
        employee.phase_2_date = data['phase_2_date']
    if 'phase_3_date' in data:
        employee.phase_3_date = data['phase_3_date']

    db.session.commit()
    return jsonify({'message': 'Employee created', 'employee_id': employee.employee_id}), 201


@bp.route('/employees/<int:employee_id>', methods=['PUT'])
@require_api_key
def update_employee(employee_id):
    """Update employee."""
    employee = Employee.query.get_or_404(employee_id)
    data = request.get_json()

    for field in ['first_name', 'last_name', 'company_email', 'batch', 'supervisor',
                  'manager', 'tier', 'shift', 'department', 'role', 'status',
                  'access_card', 'token_serial', 'building_card', 'agent_id',
                  'bo_user', 'axonify', 'attrition_date']:
        if field in data:
            setattr(employee, field, data[field])

    if 'phase_1_date' in data:
        employee.phase_1_date = data['phase_1_date']
    if 'phase_2_date' in data:
        employee.phase_2_date = data['phase_2_date']
    if 'phase_3_date' in data:
        employee.phase_3_date = data['phase_3_date']

    db.session.commit()
    return jsonify({'message': 'Employee updated'})


@bp.route('/employees/<int:employee_id>', methods=['DELETE'])
@require_api_key
def delete_employee(employee_id):
    """Delete employee (move to history)."""
    employee = Employee.query.get_or_404(employee_id)
    db.session.delete(employee)
    db.session.commit()
    return jsonify({'message': 'Employee deleted'})


# ==================== SCHEDULE ENDPOINTS ====================

@bp.route('/schedules', methods=['GET'])
@require_api_key
def get_schedules():
    """Get schedules with comprehensive filtering options.

    Query Parameters:
    - start_date: Filter schedules on or after this date (YYYY-MM-DD)
    - end_date: Filter schedules on or before this date (YYYY-MM-DD)
    - employee_id: Filter by specific employee ID
    - department: Filter by employee department
    - supervisor: Filter by employee supervisor (exact match)
    - supervisor_team: Filter by supervisor's entire team (all team member schedules)
    - batch: Filter by employee batch
    - work_code: Filter by work code (REG, OT, VAC, etc.)
    - start_time_min: Filter schedules with start time >= this time (HH:MM)
    - start_time_max: Filter schedules with start time <= this time (HH:MM)
    - stop_time_min: Filter schedules with stop time >= this time (HH:MM)
    - stop_time_max: Filter schedules with stop time <= this time (HH:MM)
    - has_start_time: Filter schedules with/without start time (true/false)
    - has_stop_time: Filter schedules with/without stop time (true/false)
    - overnight: Filter overnight shifts only (true/false)
    - date_range: Filter schedules within date range (YYYY-MM-DD,YYYY-MM-DD)
    - employee_status: Filter by employee status (Active, On Leave, etc.)
    - time_slot: Filter by common time slots (morning, afternoon, evening, night)
    - shift_type: Filter by shift pattern (regular, swing, night, weekend)
    - has_overlap: Find schedules that overlap with a date range (YYYY-MM-DD,YYYY-MM-DD)
    - page: Page number for pagination (default: 1)
    - per_page: Items per page (default: 100)
    - sort: Sort field (start_date, start_time, employee_id, last_name)
    - order: Sort order (asc, desc)

    Notes:
    - Date filters use start_date for filtering
    - Overnight shifts are detected when stop_time < start_time
    - Can combine multiple filters for precise results
    """
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    employee_id = request.args.get('employee_id')
    department = request.args.get('department')
    supervisor = request.args.get('supervisor')
    supervisor_team = request.args.get('supervisor_team')
    batch = request.args.get('batch')
    work_code = request.args.get('work_code')
    start_time_min = request.args.get('start_time_min')
    start_time_max = request.args.get('start_time_max')
    stop_time_min = request.args.get('stop_time_min')
    stop_time_max = request.args.get('stop_time_max')
    has_start_time = request.args.get('has_start_time')
    has_stop_time = request.args.get('has_stop_time')
    overnight = request.args.get('overnight')
    date_range = request.args.get('date_range')
    employee_status = request.args.get('employee_status')
    time_slot = request.args.get('time_slot')
    shift_type = request.args.get('shift_type')
    has_overlap = request.args.get('has_overlap')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    sort = request.args.get('sort')
    order = request.args.get('order', 'asc')

    # Build query with join to employee for filtering
    query = db.session.query(Schedule, Employee).join(
        Employee, Schedule.employee_id == Employee.employee_id
    )

    # Apply filters
    if start_date:
        query = query.filter(Schedule.start_date >= start_date)
    if end_date:
        query = query.filter(Schedule.start_date <= end_date)

    if employee_id:
        query = query.filter(Schedule.employee_id == int(employee_id))

    if department:
        query = query.filter(Employee.department == department)
    if supervisor:
        query = query.filter(Employee.supervisor == supervisor)
    if batch:
        query = query.filter(Employee.batch == batch)
    if employee_status:
        query = query.filter(Employee.status == employee_status)

    # Supervisor team filter - pulls all team member schedules
    if supervisor_team:
        # Get all employees who report to this supervisor
        from app.models import Employee
        team_members = Employee.query.filter_by(supervisor=supervisor_team).all()
        team_employee_ids = [e.employee_id for e in team_members]
        if team_employee_ids:
            query = query.filter(Schedule.employee_id.in_(team_employee_ids))
        else:
            # No team members found, return empty result
            query = query.filter(Schedule.schedule_id == -1)

    if work_code:
        query = query.filter(Schedule.work_code == work_code)

    # Time filters - exact time range matching
    if start_time_min:
        query = query.filter(Schedule.start_time >= start_time_min)
    if start_time_max:
        query = query.filter(Schedule.start_time <= start_time_max)
    if stop_time_min:
        query = query.filter(Schedule.stop_time >= stop_time_min)
    if stop_time_max:
        query = query.filter(Schedule.stop_time <= stop_time_max)

    # Time slot filters
    if time_slot:
        time_slots = {
            'morning': ('05:00:00', '12:00:00'),
            'afternoon': ('12:00:00', '17:00:00'),
            'evening': ('17:00:00', '21:00:00'),
            'night': ('21:00:00', '05:00:00')
        }
        if time_slot in time_slots:
            slot_start, slot_end = time_slots[time_slot]
            if time_slot == 'night':
                # Overnight night shifts
                query = query.filter(
                    (Schedule.start_time >= slot_start) |
                    (Schedule.start_time < slot_end)
                )
            else:
                query = query.filter(
                    (Schedule.start_time >= slot_start) &
                    (Schedule.start_time < slot_end)
                )

    # Shift type filters
    if shift_type:
        # Weekend detection (Saturday=5, Sunday=6)
        if shift_type == 'weekend':
            query = query.filter(
                (db.func.dayofweek(Schedule.start_date) == 1) |  # Sunday
                (db.func.dayofweek(Schedule.start_date) == 7)   # Saturday
            )
        # Night shift detection (start time >= 22:00 or < 06:00)
        elif shift_type == 'night':
            query = query.filter(
                (Schedule.start_time >= '22:00:00') |
                (Schedule.start_time < '06:00:00')
            )
        # Swing/afternoon shift (14:00 - 22:00)
        elif shift_type == 'swing':
            query = query.filter(
                (Schedule.start_time >= '14:00:00') &
                (Schedule.start_time < '22:00:00')
            )
        # Regular morning shift (06:00 - 14:00)
        elif shift_type == 'regular':
            query = query.filter(
                (Schedule.start_time >= '06:00:00') &
                (Schedule.start_time < '14:00:00')
            )

    # Overlap filter
    if has_overlap:
        dates = has_overlap.split(',')
        if len(dates) == 2:
            overlap_start = dates[0]
            overlap_end = dates[1]
            # Find schedules that overlap with the given date range
            # Overlap exists if: schedule_start <= overlap_end AND schedule_end >= overlap_start
            # For simplicity, we check if schedule start date is within or touching the overlap period
            query = query.filter(
                Schedule.start_date <= overlap_end
            )

    # Date range filter (for scheduling within a period)
    if date_range:
        dates = date_range.split(',')
        if len(dates) == 2:
            query = query.filter(
                Schedule.start_date >= dates[0],
                Schedule.start_date <= dates[1]
            )

    # Sorting
    if sort:
        sort_options = {
            'start_date': Schedule.start_date,
            'start_time': Schedule.start_time,
            'employee_id': Schedule.employee_id,
            'last_name': Employee.last_name
        }
        sort_field = sort_options.get(sort, Schedule.start_date)
        if order == 'desc':
            sort_field = sort_field.desc()
        query = query.order_by(sort_field)
    else:
        # Default sort by date and time
        query = query.order_by(Schedule.start_date.desc(), Schedule.start_time.desc())

    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    results = pagination.items

    return jsonify({
        'schedules': [{
            'schedule_id': s.schedule_id,
            'employee_id': s.employee_id,
            'first_name': e.first_name,
            'last_name': e.last_name,
            'full_name': e.full_name,
            'department': e.department,
            'supervisor': e.supervisor,
            'batch': e.batch,
            'shift': e.shift,
            'start_date': str(s.start_date),
            'start_time': str(s.start_time) if s.start_time else None,
            'stop_date': str(s.stop_date),
            'stop_time': str(s.stop_time) if s.stop_time else None,
            'work_code': s.work_code,
            'is_overnight': s.stop_date > s.start_date if s.start_time and s.stop_time else False
        } for s, e in results],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })


@bp.route('/schedules', methods=['POST'])
@require_api_key
def create_schedule():
    """Create new schedule."""
    data = request.get_json()

    schedule = Schedule(
        employee_id=data['employee_id'],
        start_date=data['start_date'],
        start_time=data.get('start_time'),
        stop_date=data['stop_date'],
        stop_time=data.get('stop_time'),
        work_code=data.get('work_code')
    )

    db.session.add(schedule)
    db.session.commit()
    return jsonify({'message': 'Schedule created', 'schedule_id': schedule.schedule_id}), 201


# ==================== ATTENDANCE ENDPOINTS ====================

@bp.route('/attendances', methods=['GET'])
@require_api_key
def get_attendances():
    """Get attendance records with comprehensive filtering options.

    Query Parameters:
    - start_date: Filter records on or after this date (YYYY-MM-DD)
    - end_date: Filter records on or before this date (YYYY-MM-DD)
    - employee_id: Filter by specific employee ID
    - department: Filter by employee department
    - supervisor: Filter by employee supervisor
    - batch: Filter by employee batch
    - exception_type: Filter by exception type (Absent, Late, Early Leave, Overtime, Cover Up, Leave)
    - has_check_in: Filter records with/without check-in (true/false)
    - has_check_out: Filter records with/without check-out (true/false)
    - late_only: Filter only late records (true/false)
    - absent_only: Filter only absent records (true/false)
    - overtime_only: Filter only overtime records (true/false)
    - cover_up_only: Filter records where employee covered up for someone (true/false)
    - late_minutes_min: Filter by minimum late minutes
    - late_minutes_max: Filter by maximum late minutes
    - overtime_minutes_min: Filter by minimum overtime minutes
    - overtime_minutes_max: Filter by maximum overtime minutes
    - employee_status: Filter by employee status (Active, On Leave, etc.)
    - page: Page number for pagination (default: 1)
    - per_page: Items per page (default: 100)
    - sort: Sort field (date, check_in, check_out, late_minutes, attendance_id)
    - order: Sort order (asc, desc)

    Response includes employee details for each attendance record.
    """
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    employee_id = request.args.get('employee_id')
    department = request.args.get('department')
    supervisor = request.args.get('supervisor')
    batch = request.args.get('batch')
    exception_type = request.args.get('exception_type')
    has_check_in = request.args.get('has_check_in')
    has_check_out = request.args.get('has_check_out')
    late_only = request.args.get('late_only')
    absent_only = request.args.get('absent_only')
    overtime_only = request.args.get('overtime_only')
    cover_up_only = request.args.get('cover_up_only')
    late_minutes_min = request.args.get('late_minutes_min')
    late_minutes_max = request.args.get('late_minutes_max')
    overtime_minutes_min = request.args.get('overtime_minutes_min')
    overtime_minutes_max = request.args.get('overtime_minutes_max')
    employee_status = request.args.get('employee_status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    sort = request.args.get('sort')
    order = request.args.get('order', 'asc')

    # Build query with join to employee
    query = db.session.query(Attendance, Employee).join(
        Employee, Attendance.employee_id == Employee.employee_id
    )

    # Apply filters
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)

    if employee_id:
        query = query.filter(Attendance.employee_id == int(employee_id))

    if department:
        query = query.filter(Employee.department == department)
    if supervisor:
        query = query.filter(Employee.supervisor == supervisor)
    if batch:
        query = query.filter(Employee.batch == batch)
    if employee_status:
        query = query.filter(Employee.status == employee_status)

    if exception_type:
        query = query.filter(Attendance.exception_type == exception_type)

    # Time filters
    if has_check_in and has_check_in.lower() == 'true':
        query = query.filter(Attendance.check_in.isnot(None))
    elif has_check_in and has_check_in.lower() == 'false':
        query = query.filter(Attendance.check_in.is_(None))

    if has_check_out and has_check_out.lower() == 'true':
        query = query.filter(Attendance.check_out.isnot(None))
    elif has_check_out and has_check_out.lower() == 'false':
        query = query.filter(Attendance.check_out.is_(None))

    # Status filters
    if late_only and late_only.lower() == 'true':
        query = query.filter(Attendance.late_minutes > 0)

    if absent_only and absent_only.lower() == 'true':
        query = query.filter(
            (Attendance.exception_type == 'Absent') |
            (Attendance.exception_type == 'Leave')
        )

    if overtime_only and overtime_only.lower() == 'true':
        query = query.filter(Attendance.overtime_minutes > 0)

    if cover_up_only and cover_up_only.lower() == 'true':
        query = query.filter(Attendance.cover_up_for_employee_id.isnot(None))

    # Minutes filters
    if late_minutes_min:
        query = query.filter(Attendance.late_minutes >= int(late_minutes_min))
    if late_minutes_max:
        query = query.filter(Attendance.late_minutes <= int(late_minutes_max))

    if overtime_minutes_min:
        query = query.filter(Attendance.overtime_minutes >= int(overtime_minutes_min))
    if overtime_minutes_max:
        query = query.filter(Attendance.overtime_minutes <= int(overtime_minutes_max))

    # Sorting
    if sort:
        sort_options = {
            'date': Attendance.date,
            'check_in': Attendance.check_in,
            'check_out': Attendance.check_out,
            'late_minutes': Attendance.late_minutes,
            'overtime_minutes': Attendance.overtime_minutes,
            'attendance_id': Attendance.attendance_id
        }
        sort_field = sort_options.get(sort, Attendance.date)
        if order == 'desc':
            sort_field = sort_field.desc()
        query = query.order_by(sort_field)
    else:
        # Default sort by date descending
        query = query.order_by(Attendance.date.desc())

    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    results = pagination.items

    return jsonify({
        'attendances': [{
            'attendance_id': a.attendance_id,
            'employee_id': a.employee_id,
            'first_name': e.first_name,
            'last_name': e.last_name,
            'full_name': e.full_name,
            'department': e.department,
            'supervisor': e.supervisor,
            'batch': e.batch,
            'shift': e.shift,
            'role': e.role,
            'status': e.status,
            'date': str(a.date),
            'check_in': str(a.check_in) if a.check_in else None,
            'check_out': str(a.check_out) if a.check_out else None,
            'exception_type': a.exception_type,
            'late_minutes': a.late_minutes or 0,
            'early_leave': str(a.early_leave) if a.early_leave else None,
            'overtime_minutes': a.overtime_minutes or 0,
            'cover_up_for_employee_id': a.cover_up_for_employee_id,
            'cover_up_for_name': f"{e_cover.first_name} {e_cover.last_name}" if a.cover_up_for_employee_id and (e_cover := Employee.query.get(a.cover_up_for_employee_id)) else None,
            'notes': a.notes
        } for a, e in results],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })


@bp.route('/attendances', methods=['POST'])
@require_api_key
def create_attendance():
    """Create attendance record."""
    data = request.get_json()

    attendance = Attendance(
        employee_id=data['employee_id'],
        date=data['date'],
        check_in=data['check_in'],
        check_out=data.get('check_out'),
        exception_type=data.get('exception_type'),
        notes=data.get('notes')
    )

    db.session.add(attendance)
    db.session.commit()
    return jsonify({'message': 'Attendance recorded', 'attendance_id': attendance.attendance_id}), 201


@bp.route('/attendances/<int:employee_id>/<string:date>', methods=['PUT'])
@require_api_key
def update_attendance(employee_id, date):
    """Update attendance record."""
    attendance = Attendance.query.filter_by(
        employee_id=employee_id, date=date
    ).first_or_404()

    data = request.get_json()
    if 'check_out' in data:
        attendance.check_out = data['check_out']
    if 'exception_type' in data:
        attendance.exception_type = data['exception_type']
    if 'notes' in data:
        attendance.notes = data['notes']

    db.session.commit()
    return jsonify({'message': 'Attendance updated'})


# ==================== LEAVE REQUEST ENDPOINTS ====================

@bp.route('/leave_requests', methods=['GET'])
@require_api_key
def get_leave_requests():
    """Get leave requests with comprehensive filtering options.

    Query Parameters:
    - status: Filter by status (Pending, Approved, Rejected)
    - leave_type: Filter by leave type (Vacation, Sick, Personal, Unpaid, etc.)
    - employee_id: Filter by specific employee ID
    - department: Filter by employee department
    - supervisor: Filter by employee supervisor
    - batch: Filter by employee batch
    - start_date_min: Filter leave starting on or after this date (YYYY-MM-DD)
    - start_date_max: Filter leave starting on or before this date (YYYY-MM-DD)
    - end_date_min: Filter leave ending on or after this date (YYYY-MM-DD)
    - end_date_max: Filter leave ending on or before this date (YYYY-MM-DD)
    - is_approved: Filter by approval status (true/false)
    - employee_status: Filter by employee status (Active, On Leave, etc.)
    - page: Page number for pagination (default: 1)
    - per_page: Items per page (default: 100)
    - sort: Sort field (start_date, end_date, created_at, leave_id)
    - order: Sort order (asc, desc)
    """
    # Get query parameters
    status = request.args.get('status')
    leave_type = request.args.get('leave_type')
    employee_id = request.args.get('employee_id')
    department = request.args.get('department')
    supervisor = request.args.get('supervisor')
    batch = request.args.get('batch')
    start_date_min = request.args.get('start_date_min')
    start_date_max = request.args.get('start_date_max')
    end_date_min = request.args.get('end_date_min')
    end_date_max = request.args.get('end_date_max')
    is_approved = request.args.get('is_approved')
    employee_status = request.args.get('employee_status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    sort = request.args.get('sort')
    order = request.args.get('order', 'asc')

    # Build query with join to employee
    query = db.session.query(LeaveRequest, Employee).join(
        Employee, LeaveRequest.employee_id == Employee.employee_id
    )

    # Apply filters
    if status:
        query = query.filter(LeaveRequest.status == status)

    if leave_type:
        query = query.filter(LeaveRequest.leave_type == leave_type)

    if employee_id:
        query = query.filter(LeaveRequest.employee_id == int(employee_id))

    if department:
        query = query.filter(Employee.department == department)
    if supervisor:
        query = query.filter(Employee.supervisor == supervisor)
    if batch:
        query = query.filter(Employee.batch == batch)
    if employee_status:
        query = query.filter(Employee.status == employee_status)

    # Date filters
    if start_date_min:
        query = query.filter(LeaveRequest.start_date >= start_date_min)
    if start_date_max:
        query = query.filter(LeaveRequest.start_date <= start_date_max)
    if end_date_min:
        query = query.filter(LeaveRequest.end_date >= end_date_min)
    if end_date_max:
        query = query.filter(LeaveRequest.end_date <= end_date_max)

    # Approval status filters
    if is_approved and is_approved.lower() == 'true':
        query = query.filter(LeaveRequest.status == 'Approved')
    elif is_approved and is_approved.lower() == 'false':
        query = query.filter(LeaveRequest.status != 'Approved')

    # Sorting
    if sort:
        sort_options = {
            'start_date': LeaveRequest.start_date,
            'end_date': LeaveRequest.end_date,
            'created_at': LeaveRequest.created_at,
            'leave_id': LeaveRequest.leave_id
        }
        sort_field = sort_options.get(sort, LeaveRequest.created_at)
        if order == 'desc':
            sort_field = sort_field.desc()
        query = query.order_by(sort_field)
    else:
        query = query.order_by(LeaveRequest.created_at.desc())

    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    results = pagination.items

    return jsonify({
        'leave_requests': [{
            'leave_id': l.leave_id,
            'employee_id': l.employee_id,
            'first_name': e.first_name,
            'last_name': e.last_name,
            'full_name': e.full_name,
            'department': e.department,
            'supervisor': e.supervisor,
            'batch': e.batch,
            'leave_type': l.leave_type,
            'start_date': str(l.start_date),
            'end_date': str(l.end_date),
            'status': l.status,
            'approved_by': l.approved_by,
            'approved_at': str(l.approved_at) if l.approved_at else None,
            'created_at': str(l.created_at)
        } for l, e in results],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })


@bp.route('/leave_requests', methods=['POST'])
@require_api_key
def create_leave_request():
    """Create new leave request."""
    data = request.get_json()

    leave = LeaveRequest(
        employee_id=data['employee_id'],
        leave_type=data['leave_type'],
        start_date=data['start_date'],
        end_date=data['end_date'],
        status=data.get('status', 'Pending')
    )

    db.session.add(leave)
    db.session.commit()
    return jsonify({'message': 'Leave request created', 'leave_id': leave.leave_id}), 201


@bp.route('/leave_requests/<int:leave_id>/approve', methods=['POST'])
@require_api_key
def approve_leave_request(leave_id):
    """Approve leave request."""
    leave = LeaveRequest.query.get_or_404(leave_id)
    data = request.get_json()

    leave.status = 'Approved'
    leave.approved_by = data['approved_by']
    from datetime import datetime
    leave.approved_at = datetime.utcnow()

    db.session.commit()
    return jsonify({'message': 'Leave request approved'})


# ==================== EXCEPTION RECORD ENDPOINTS ====================

@bp.route('/exceptions', methods=['GET'])
@require_api_key
def get_exceptions():
    """Get exception records with comprehensive filtering options.

    Query Parameters:
    - status: Filter by status (Pending, Approved, Rejected, Completed)
    - exception_type: Filter by exception type (Training, Nesting, New Hire Training, Vacation, etc.)
    - employee_id: Filter by specific employee ID
    - department: Filter by employee department
    - supervisor: Filter by employee supervisor
    - batch: Filter by employee batch
    - start_date_min: Filter exceptions starting on or after this date (YYYY-MM-DD)
    - start_date_max: Filter exceptions starting on or before this date (YYYY-MM-DD)
    - end_date_min: Filter exceptions ending on or after this date (YYYY-MM-DD)
    - end_date_max: Filter exceptions ending on or before this date (YYYY-MM-DD)
    - processed: Filter by processing status (true/false)
    - work_code: Filter by work code
    - employee_status: Filter by employee status (Active, On Leave, etc.)
    - page: Page number for pagination (default: 1)
    - per_page: Items per page (default: 100)
    - sort: Sort field (start_date, end_date, created_at, exception_id)
    - order: Sort order (asc, desc)

    Response includes employee details for each exception record.
    """
    # Get query parameters
    status = request.args.get('status')
    exception_type = request.args.get('exception_type')
    employee_id = request.args.get('employee_id')
    department = request.args.get('department')
    supervisor = request.args.get('supervisor')
    batch = request.args.get('batch')
    start_date_min = request.args.get('start_date_min')
    start_date_max = request.args.get('start_date_max')
    end_date_min = request.args.get('end_date_min')
    end_date_max = request.args.get('end_date_max')
    processed = request.args.get('processed')
    work_code = request.args.get('work_code')
    employee_status = request.args.get('employee_status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    sort = request.args.get('sort')
    order = request.args.get('order', 'asc')

    # Build query with join to employee
    query = db.session.query(ExceptionRecord, Employee).join(
        Employee, ExceptionRecord.employee_id == Employee.employee_id
    )

    # Apply filters
    if status:
        query = query.filter(ExceptionRecord.status == status)

    if exception_type:
        query = query.filter(ExceptionRecord.exception_type == exception_type)

    if employee_id:
        query = query.filter(ExceptionRecord.employee_id == int(employee_id))

    if department:
        query = query.filter(Employee.department == department)
    if supervisor:
        query = query.filter(Employee.supervisor == supervisor)
    if batch:
        query = query.filter(Employee.batch == batch)
    if employee_status:
        query = query.filter(Employee.status == employee_status)

    if work_code:
        query = query.filter(ExceptionRecord.work_code == work_code)

    # Date filters
    if start_date_min:
        query = query.filter(ExceptionRecord.start_date >= start_date_min)
    if start_date_max:
        query = query.filter(ExceptionRecord.start_date <= start_date_max)
    if end_date_min:
        query = query.filter(ExceptionRecord.end_date >= end_date_min)
    if end_date_max:
        query = query.filter(ExceptionRecord.end_date <= end_date_max)

    # Processing status filters
    if processed and processed.lower() == 'true':
        query = query.filter(ExceptionRecord.processed_by.isnot(None))
    elif processed and processed.lower() == 'false':
        query = query.filter(ExceptionRecord.processed_by.is_(None))

    # Sorting
    if sort:
        sort_options = {
            'start_date': ExceptionRecord.start_date,
            'end_date': ExceptionRecord.end_date,
            'created_at': ExceptionRecord.created_at,
            'exception_id': ExceptionRecord.exception_id
        }
        sort_field = sort_options.get(sort, ExceptionRecord.start_date)
        if order == 'desc':
            sort_field = sort_field.desc()
        query = query.order_by(sort_field)
    else:
        query = query.order_by(ExceptionRecord.start_date.desc())

    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    results = pagination.items

    return jsonify({
        'exceptions': [{
            'exception_id': e.exception_id,
            'employee_id': e.employee_id,
            'first_name': emp.first_name,
            'last_name': emp.last_name,
            'full_name': emp.full_name,
            'department': emp.department,
            'supervisor': emp.supervisor,
            'batch': emp.batch,
            'exception_type': e.exception_type,
            'start_date': str(e.start_date),
            'end_date': str(e.end_date),
            'work_code': e.work_code,
            'status': e.status,
            'notes': e.notes,
            'supervisor_override': e.supervisor_override,
            'processed_by': e.processed_by,
            'processed_at': str(e.processed_at) if e.processed_at else None,
            'created_at': str(e.created_at)
        } for e, emp in results],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })


@bp.route('/exceptions', methods=['POST'])
@require_api_key
def create_exception():
    """Create exception record (batch or single)."""
    data = request.get_json()

    exception = ExceptionRecord(
        employee_id=data['employee_id'],
        exception_type=data['exception_type'],
        start_date=data['start_date'],
        end_date=data['end_date'],
        work_code=data.get('work_code'),
        status=data.get('status', 'Pending'),
        notes=data.get('notes'),
        supervisor_override=data.get('supervisor_override')
    )

    db.session.add(exception)
    db.session.commit()
    return jsonify({'message': 'Exception record created', 'exception_id': exception.exception_id}), 201


@bp.route('/exceptions/<int:exception_id>/process', methods=['POST'])
@require_api_key
def process_exception(exception_id):
    """Process exception record."""
    exception = ExceptionRecord.query.get_or_404(exception_id)
    data = request.get_json()

    exception.status = 'Completed'
    exception.processed_by = data['processed_by']
    from datetime import datetime
    exception.processed_at = datetime.utcnow()

    db.session.commit()
    return jsonify({'message': 'Exception record processed'})


# ==================== ADMIN OPTIONS ENDPOINTS ====================

@bp.route('/admin/options', methods=['GET'])
@require_api_key
def get_admin_options():
    """Get all admin options."""
    category = request.args.get('category')
    query = AdminOptions.query.filter_by(is_active=True)
    if category:
        query = query.filter_by(category=category)

    options = query.all()
    return jsonify([{
        'option_id': o.option_id,
        'category': o.category,
        'value': o.value
    } for o in options])


@bp.route('/admin/options', methods=['POST'])
@require_api_key
def create_admin_option():
    """Create new admin option."""
    data = request.get_json()

    option = AdminOptions(
        category=data['category'],
        value=data['value']
    )

    db.session.add(option)
    db.session.commit()
    return jsonify({'message': 'Admin option created', 'option_id': option.option_id}), 201


# ==================== REWARD ENDPOINTS ====================

@bp.route('/rewards/reasons', methods=['GET'])
@require_api_key
def get_reward_reasons():
    """Get reward reasons with optional filtering.

    Query Parameters:
    - is_active: Filter by active status (true/false)
    - points_min: Filter by minimum points
    - points_max: Filter by maximum points
    - search: Search in reason name
    """
    is_active = request.args.get('is_active')
    points_min = request.args.get('points_min')
    points_max = request.args.get('points_max')
    search = request.args.get('search')

    query = RewardReason.query

    if is_active and is_active.lower() == 'true':
        query = query.filter_by(is_active=True)
    elif is_active and is_active.lower() == 'false':
        query = query.filter_by(is_active=False)

    if points_min:
        query = query.filter(RewardReason.points >= int(points_min))
    if points_max:
        query = query.filter(RewardReason.points <= int(points_max))
    if search:
        query = query.filter(RewardReason.reason.ilike(f'%{search}%'))

    reasons = query.all()
    return jsonify([{
        'reason_id': r.reason_id,
        'reason': r.reason,
        'points': r.points,
        'is_active': r.is_active
    } for r in reasons])


@bp.route('/rewards/employee/<int:employee_id>', methods=['GET'])
@require_api_key
def get_employee_rewards(employee_id):
    """Get employee reward history with filtering.

    Query Parameters:
    - points_min: Filter by minimum points
    - points_max: Filter by maximum points
    - date_min: Filter awards on or after this date (YYYY-MM-DD)
    - date_max: Filter awards on or before this date (YYYY-MM-DD)
    - spent: Filter by spent status (true/false)
    - reason_id: Filter by specific reason ID
    - sort: Sort field (date_awarded, points, reward_id)
    - order: Sort order (asc, desc)
    """
    points_min = request.args.get('points_min')
    points_max = request.args.get('points_max')
    date_min = request.args.get('date_min')
    date_max = request.args.get('date_max')
    spent = request.args.get('spent')
    reason_id = request.args.get('reason_id')
    sort = request.args.get('sort')
    order = request.args.get('order', 'asc')

    query = EmployeeReward.query.filter_by(employee_id=employee_id)

    if points_min:
        query = query.filter(EmployeeReward.points >= int(points_min))
    if points_max:
        query = query.filter(EmployeeReward.points <= int(points_max))
    if date_min:
        query = query.filter(EmployeeReward.date_awarded >= date_min)
    if date_max:
        query = query.filter(EmployeeReward.date_awarded <= date_max)

    if spent and spent.lower() == 'true':
        query = query.filter_by(is_spent=True)
    elif spent and spent.lower() == 'false':
        query = query.filter_by(is_spent=False)

    if reason_id:
        query = query.filter_by(reason_id=int(reason_id))

    if sort:
        sort_options = {
            'date_awarded': EmployeeReward.date_awarded,
            'points': EmployeeReward.points,
            'reward_id': EmployeeReward.reward_id
        }
        sort_field = sort_options.get(sort, EmployeeReward.date_awarded)
        if order == 'desc':
            sort_field = sort_field.desc()
        query = query.order_by(sort_field)
    else:
        query = query.order_by(EmployeeReward.date_awarded.desc())

    rewards = query.all()
    return jsonify([{
        'reward_id': r.reward_id,
        'reason_id': r.reason_id,
        'reason': r.reward_reason.reason if r.reward_reason else None,
        'points': r.points,
        'date_awarded': str(r.date_awarded),
        'notes': r.notes,
        'awarded_by': r.awarded_by,
        'is_spent': r.is_spent,
        'spent_at': str(r.spent_at) if r.spent_at else None,
        'redemption_id': r.redemption_id if r.redemption else None
    } for r in rewards])


@bp.route('/rewards/award', methods=['POST'])
@require_api_key
def award_points():
    """Award points to employee."""
    from app.models import Employee, EmployeeReward

    data = request.get_json()

    # Validate employee exists
    employee = Employee.query.get(data['employee_id'])
    if not employee:
        raise APIError('Employee not found', 404)

    reward = EmployeeReward(
        employee_id=data['employee_id'],
        reason_id=data['reason_id'],
        points=data['points'],
        date_awarded=data['date_awarded'],
        notes=data.get('notes'),
        awarded_by=data.get('awarded_by')
    )

    # Update employee's point balance
    employee.point_balance = (employee.point_balance or 0) + data['points']

    db.session.add(reward)
    db.session.commit()
    return jsonify({
        'message': 'Points awarded',
        'reward_id': reward.reward_id,
        'new_balance': employee.point_balance
    }), 201


# ==================== BATCH ENDPOINTS ====================

@bp.route('/employees/batch', methods=['POST'])
@require_api_key
def create_employees_batch():
    """Bulk import employees from Excel file."""
    from app.utils.upload_processor import process_employee_upload
    import tempfile
    import os

    if 'file' not in request.files:
        raise APIError('No file uploaded', 400)

    file = request.files['file']
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise APIError('Invalid file type. Must be .xlsx or .xls', 400)

    try:
        file_path = os.path.join(tempfile.gettempdir(), file.filename)
        file.save(file_path)

        success_count, error_count, errors = process_employee_upload(file_path)

        os.remove(file_path)

        return jsonify({
            'message': f'Bulk employee import completed',
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:10]
        }), 201

    except Exception as e:
        db.session.rollback()
        raise APIError(f'Error processing file: {str(e)}', 500)


@bp.route('/schedules/batch', methods=['POST'])
@require_api_key
def create_schedules_batch():
    """Bulk import schedules from Excel file.

    Required columns:
    - Employee - ID (RUEX ID: first letter + last name, or Odoo ID)
    - Date - Nominal Date
    - Earliest - Start
    - Latest - Stop
    - Work - Code

    Query params:
    - employee_file: Optional path to employee Excel file for RUEX ID matching

    Returns count of imported records and any errors.
    """
    from app.utils.upload_processor import process_schedule_upload
    import os

    if 'file' not in request.files:
        raise APIError('No file uploaded', 400)

    file = request.files['file']
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise APIError('Invalid file type. Must be .xlsx or .xls', 400)

    # Optional employee file for RUEX ID matching
    employee_file = request.files.get('employee_file')

    import tempfile
    import os

    # Use temp directory (works on both Windows and Unix)
    temp_dir = tempfile.gettempdir()

    try:
        file_path = os.path.join(temp_dir, file.filename)
        file.save(file_path)

        employee_file_path = None
        if employee_file:
            employee_file_path = os.path.join(temp_dir, employee_file.filename)
            employee_file.save(employee_file_path)

        success_count, error_count, errors, duplicates = process_schedule_upload(
            file_path, employee_file_path=employee_file_path
        )

        os.remove(file_path)
        if employee_file_path and os.path.exists(employee_file_path):
            os.remove(employee_file_path)

        return jsonify({
            'message': f'Bulk schedule import completed',
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:10],
            'duplicates': duplicates[:10]
        }), 201

    except Exception as e:
        db.session.rollback()
        raise APIError(f'Error processing file: {str(e)}', 500)


@bp.route('/attendances/batch', methods=['POST'])
@require_api_key
def create_attendance_batch():
    """Bulk import attendance from Excel file.

    Required columns:
    - Employee - ID
    - Date
    - Check In
    - Check Out (optional)
    - Exception (optional)
    - Notes (optional)

    Returns count of imported records and any errors.
    """
    from app.utils.upload_processor import process_attendance_upload
    import tempfile
    import os

    if 'file' not in request.files:
        raise APIError('No file uploaded', 400)

    file = request.files['file']
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise APIError('Invalid file type. Must be .xlsx or .xls', 400)

    try:
        file_path = os.path.join(tempfile.gettempdir(), file.filename)
        file.save(file_path)

        success_count, error_count, errors = process_attendance_upload(file_path)

        os.remove(file_path)

        return jsonify({
            'message': f'Bulk attendance import completed',
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:10]
        }), 201

    except Exception as e:
        db.session.rollback()
        raise APIError(f'Error processing file: {str(e)}', 500)


@bp.route('/exceptions/batch', methods=['POST'])
@require_api_key
def create_exceptions_batch():
    """Bulk import exception records from Excel file.

    Required columns:
    - Employee - ID
    - Exception Type
    - Start Date
    - End Date
    - Work Code (optional)
    - Supervisor Override (optional)
    - Notes (optional)

    Returns count of imported records and any errors.
    """
    from app.utils.upload_processor import process_exception_upload
    import tempfile
    import os

    if 'file' not in request.files:
        raise APIError('No file uploaded', 400)

    file = request.files['file']
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise APIError('Invalid file type. Must be .xlsx or .xls', 400)

    try:
        file_path = os.path.join(tempfile.gettempdir(), file.filename)
        file.save(file_path)

        success_count, error_count, errors = process_exception_upload(file_path)

        os.remove(file_path)

        return jsonify({
            'message': f'Bulk exception import completed',
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:10]
        }), 201

    except Exception as e:
        db.session.rollback()
        raise APIError(f'Error processing file: {str(e)}', 500)


@bp.route('/rewards/award/batch', methods=['POST'])
@require_api_key
def award_points_batch():
    """Bulk award points to employees.

    Expects:
    - file: Excel file with columns:
      - Employee - ID
      - Reason ID
      - Points
      - Date Awarded
      - Notes (optional)

    Returns count of awards and any errors.
    """
    import os
    import tempfile
    from datetime import datetime
    import pandas as pd

    if 'file' not in request.files:
        raise APIError('No file uploaded', 400)

    file = request.files['file']
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise APIError('Invalid file type. Must be .xlsx or .xls', 400)

    errors = []
    success_count = 0

    try:
        file_path = os.path.join(tempfile.gettempdir(), file.filename)
        file.save(file_path)

        df = pd.read_excel(file_path)

        required = ['Employee - ID', 'Reason ID', 'Points', 'Date Awarded']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise APIError('Missing required columns', 400, missing)

        for idx, row in df.iterrows():
            try:
                employee_id = int(row['Employee - ID'])
                reason_id = int(row['Reason ID'])
                points = int(row['Points'])

                # Validate employee exists
                if not Employee.query.get(employee_id):
                    errors.append(f'Row {idx + 2}: Employee {employee_id} not found')
                    continue

                # Validate reason exists and is active
                reason = RewardReason.query.get(reason_id)
                if not reason or not reason.is_active:
                    errors.append(f'Row {idx + 2}: Reason {reason_id} not found or inactive')
                    continue

                # Parse date
                award_date = row['Date Awarded']
                if pd.isna(award_date):
                    award_date = datetime.utcnow().date()
                else:
                    award_date = award_date.to_pydatetime().date()

                # Update employee's point balance
                employee = Employee.query.get(employee_id)
                if employee:
                    employee.point_balance = (employee.point_balance or 0) + points

                # Create reward
                reward = EmployeeReward(
                    employee_id=employee_id,
                    reason_id=reason_id,
                    points=points,
                    date_awarded=award_date,
                    notes=str(row.get('Notes', '') or '').strip() or None,
                    awarded_by=1  # Default to admin
                )
                db.session.add(reward)
                success_count += 1

            except Exception as e:
                errors.append(f'Row {idx + 2}: {str(e)}')

        db.session.commit()

        os.remove(file_path)

        return jsonify({
            'message': f'Bulk reward award completed',
            'success_count': success_count,
            'error_count': len(errors),
            'errors': errors[:10]
        }), 201

    except Exception as e:
        db.session.rollback()
        raise APIError(f'Error processing file: {str(e)}', 500)


# ==================== REWARD BALANCE ENDPOINTS ====================

@bp.route('/rewards/employee/<int:employee_id>/balance', methods=['GET'])
@require_api_key
def get_employee_balance(employee_id):
    """Get employee's current point balance."""
    from app.models import Employee

    employee = Employee.query.get_or_404(employee_id)
    return jsonify({
        'employee_id': employee.employee_id,
        'employee_name': employee.full_name,
        'point_balance': employee.point_balance or 0
    })


@bp.route('/rewards/redemptions', methods=['POST'])
@require_api_key
def create_redemption():
    """Redeem points for an employee."""
    from app.models import Employee, EmployeeRewardRedemption

    data = request.get_json()

    employee = Employee.query.get_or_404(data['employee_id'])

    # Check sufficient balance
    current_balance = employee.point_balance or 0
    if data['points_redeemed'] > current_balance:
        raise APIError(f'Insufficient points. Current balance: {current_balance}', 400)

    redemption = EmployeeRewardRedemption(
        employee_id=data['employee_id'],
        points_redeemed=data['points_redeemed'],
        redemption_type=data['redemption_type'],
        redemption_details=data.get('redemption_details'),
        notes=data.get('notes'),
        approved_by=data.get('approved_by')
    )

    # Update employee's point balance
    employee.point_balance = current_balance - data['points_redeemed']

    db.session.add(redemption)
    db.session.commit()

    return jsonify({
        'message': 'Points redeemed successfully',
        'redemption_id': redemption.redemption_id,
        'points_redeemed': data['points_redeemed'],
        'remaining_balance': employee.point_balance
    }), 201

