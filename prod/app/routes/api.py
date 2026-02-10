from flask import Blueprint, request, jsonify
from app import db
from app.models import Employee, Schedule, Attendance, LeaveRequest, ScheduleChange, ExceptionRecord, AdminOptions, RewardReason, EmployeeReward

bp = Blueprint('api', __name__)


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


# ==================== EMPLOYEE ENDPOINTS ====================

@bp.route('/api/employees', methods=['GET'])
def get_employees():
    """Get all active employees or filter by status."""
    status = request.args.get('status', 'Active')
    employees = Employee.query.filter_by(status=status).all()
    return jsonify([{
        'employee_id': e.employee_id,
        'first_name': e.first_name,
        'last_name': e.last_name,
        'full_name': e.full_name,
        'company_email': e.company_email,
        'department': e.department,
        'role': e.role,
        'shift': e.shift,
        'status': e.status
    } for e in employees])


@bp.route('/api/employees/<int:employee_id>', methods=['GET'])
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
        'attrition_date': str(employee.attrition_date) if employee.attrition_date else None
    })


@bp.route('/api/employees', methods=['POST'])
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


@bp.route('/api/employees/<int:employee_id>', methods=['PUT'])
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


@bp.route('/api/employees/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """Delete employee (move to history)."""
    employee = Employee.query.get_or_404(employee_id)
    db.session.delete(employee)
    db.session.commit()
    return jsonify({'message': 'Employee deleted'})


# ==================== SCHEDULE ENDPOINTS ====================

@bp.route('/api/schedules', methods=['GET'])
def get_schedules():
    """Get schedules for date range."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    employee_id = request.args.get('employee_id')

    query = Schedule.query
    if start_date:
        query = query.filter(Schedule.start_date >= start_date)
    if end_date:
        query = query.filter(Schedule.start_date <= end_date)
    if employee_id:
        query = query.filter(Schedule.employee_id == employee_id)

    schedules = query.all()
    return jsonify([{
        'schedule_id': s.schedule_id,
        'employee_id': s.employee_id,
        'start_date': str(s.start_date),
        'start_time': str(s.start_time) if s.start_time else None,
        'stop_date': str(s.stop_date),
        'stop_time': str(s.stop_time) if s.stop_time else None,
        'work_code': s.work_code
    } for s in schedules])


@bp.route('/api/schedules', methods=['POST'])
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

@bp.route('/api/attendances', methods=['GET'])
def get_attendances():
    """Get attendance records for date range."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    employee_id = request.args.get('employee_id')

    query = Attendance.query
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)
    if employee_id:
        query = query.filter(Attendance.employee_id == employee_id)

    attendances = query.all()
    return jsonify([{
        'attendance_id': a.attendance_id,
        'employee_id': a.employee_id,
        'date': str(a.date),
        'check_in': str(a.check_in),
        'check_out': str(a.check_out) if a.check_out else None,
        'exception_type': a.exception_type,
        'notes': a.notes
    } for a in attendances])


@bp.route('/api/attendances', methods=['POST'])
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


@bp.route('/api/attendances/<int:employee_id>/<string:date>', methods=['PUT'])
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

@bp.route('/api/leave_requests', methods=['GET'])
def get_leave_requests():
    """Get leave requests."""
    status = request.args.get('status')
    employee_id = request.args.get('employee_id')

    query = LeaveRequest.query
    if status:
        query = query.filter(LeaveRequest.status == status)
    if employee_id:
        query = query.filter(LeaveRequest.employee_id == employee_id)

    leave_requests = query.all()
    return jsonify([{
        'leave_id': l.leave_id,
        'employee_id': l.employee_id,
        'leave_type': l.leave_type,
        'start_date': str(l.start_date),
        'end_date': str(l.end_date),
        'status': l.status
    } for l in leave_requests])


@bp.route('/api/leave_requests', methods=['POST'])
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


@bp.route('/api/leave_requests/<int:leave_id>/approve', methods=['POST'])
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

@bp.route('/api/exceptions', methods=['GET'])
def get_exceptions():
    """Get exception records."""
    status = request.args.get('status')
    employee_id = request.args.get('employee_id')

    query = ExceptionRecord.query
    if status:
        query = query.filter(ExceptionRecord.status == status)
    if employee_id:
        query = query.filter(ExceptionRecord.employee_id == employee_id)

    exceptions = query.all()
    return jsonify([{
        'exception_id': e.exception_id,
        'employee_id': e.employee_id,
        'exception_type': e.exception_type,
        'start_date': str(e.start_date),
        'end_date': str(e.end_date),
        'work_code': e.work_code,
        'status': e.status,
        'notes': e.notes
    } for e in exceptions])


@bp.route('/api/exceptions', methods=['POST'])
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


@bp.route('/api/exceptions/<int:exception_id>/process', methods=['POST'])
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

@bp.route('/api/admin/options', methods=['GET'])
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


@bp.route('/api/admin/options', methods=['POST'])
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

@bp.route('/api/rewards/reasons', methods=['GET'])
def get_reward_reasons():
    """Get reward reasons."""
    reasons = RewardReason.query.filter_by(is_active=True).all()
    return jsonify([{
        'reason_id': r.reason_id,
        'reason': r.reason,
        'points': r.points
    } for r in reasons])


@bp.route('/api/rewards/employee/<int:employee_id>', methods=['GET'])
def get_employee_rewards(employee_id):
    """Get employee reward history."""
    rewards = EmployeeReward.query.filter_by(employee_id=employee_id).all()
    return jsonify([{
        'reward_id': r.reward_id,
        'reason': r.reward_reason.reason if r.reward_reason else None,
        'points': r.points,
        'date_awarded': str(r.date_awarded)
    } for r in rewards])


@bp.route('/api/rewards/award', methods=['POST'])
def award_points():
    """Award points to employee."""
    data = request.get_json()

    reward = EmployeeReward(
        employee_id=data['employee_id'],
        reason_id=data['reason_id'],
        points=data['points'],
        date_awarded=data['date_awarded'],
        notes=data.get('notes'),
        awarded_by=data.get('awarded_by')
    )

    db.session.add(reward)
    db.session.commit()
    return jsonify({'message': 'Points awarded', 'reward_id': reward.reward_id}), 201
