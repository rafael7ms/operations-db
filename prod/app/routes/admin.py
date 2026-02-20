from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models import Employee, Schedule, AdminOptions, ExceptionRecord, User, RewardReason, EmployeeReward, Attendance, DBUser, NewEmployeeReview
from flask_login import login_user, logout_user, login_required, current_user
from app.utils.parsers import parse_name
import pandas as pd
import os

bp = Blueprint('main', __name__)


# ==================== AUTH ROUTES ====================

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')


@bp.route('/logout')
@login_required
def logout():
    """Logout user."""
    logout_user()
    return redirect(url_for('main.login'))


# ==================== MAIN ROUTES ====================

@bp.route('/')
def index():
    """Home page - redirects to login or dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))


@bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard with overview statistics."""
    total_employees = Employee.query.count()
    active_employees = Employee.query.filter_by(status='Active').count()
    on_leave = Employee.query.filter_by(status='On Leave').count()
    in_training = ExceptionRecord.query.filter_by(exception_type='Training', status='Pending').count()

    return render_template('dashboard.html',
                         total_employees=total_employees,
                         active_employees=active_employees,
                         on_leave=on_leave,
                         in_training=in_training)


@bp.route('/employees', methods=['GET', 'POST'])
@login_required
def employees():
    """Employee management - list and add."""
    if request.method == 'POST':
        # Handle batch file upload
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename.endswith(('.xlsx', '.xls')):
                filepath = os.path.join('uploads', file.filename)
                file.save(filepath)

                try:
                    df = pd.read_excel(filepath)
                    imported = 0
                    for idx, row in df.iterrows():
                        try:
                            first_name = str(row['First Name']).strip()
                            last_name = str(row['Last Name']).strip()
                            company_email = f"{first_name.lower()}.{last_name.lower()}@7managedservices.com"

                            employee_id = int(row['Odoo ID'])
                            agent_id = int(row['Agent ID']) if pd.notna(row['Agent ID']) else None

                            emp = Employee(
                                employee_id=employee_id,
                                first_name=first_name,
                                last_name=last_name,
                                full_name=f"{first_name} {last_name}",
                                company_email=company_email,
                                batch=str(row['Batch']).strip(),
                                agent_id=agent_id,
                                ruex_id=str(row['BO User']).strip() if pd.notna(row['BO User']) else None,
                                axonify_id=str(row['Axonify']).strip() if pd.notna(row['Axonify']) else None,
                                supervisor=str(row['Supervisor']).strip(),
                                manager=str(row['Manager']).strip(),
                                tier=int(row['Tier']) if pd.notna(row['Tier']) else None,
                                shift=str(row['Shift']).strip(),
                                department=str(row['Department']).strip(),
                                role=str(row['Role']).strip(),
                                hire_date=row['Hire Date'].to_pydatetime().date() if pd.notna(row['Hire Date']) else None,
                                phase_1_date=row['Phase 1 Date'].to_pydatetime().date() if pd.notna(row['Phase 1 Date']) else None,
                                phase_2_date=row['Phase 2 Date'].to_pydatetime().date() if pd.notna(row['Phase 2 Date']) else None,
                                phase_3_date=row['Phase 3 Date'].to_pydatetime().date() if pd.notna(row['Phase 3 Date']) else None,
                                status='Active'
                            )
                            db.session.add(emp)
                            imported += 1
                        except Exception as e:
                            continue

                    db.session.commit()
                    flash(f'Imported {imported} employees!', 'success')
                except Exception as e:
                    flash(f'Error importing file: {str(e)}', 'danger')

        return redirect(url_for('main.employees'))

    # Get dropdown options
    departments = AdminOptions.query.filter_by(category='department', is_active=True).all()
    roles = AdminOptions.query.filter_by(category='role', is_active=True).all()
    shifts = AdminOptions.query.filter_by(category='shift', is_active=True).all()
    statuses = AdminOptions.query.filter_by(category='status', is_active=True).all()

    employees_list = Employee.query.all()
    return render_template('employees.html',
                         employees=employees_list,
                         departments=departments,
                         roles=roles,
                         shifts=shifts,
                         statuses=statuses)


@bp.route('/employees/add', methods=['POST'])
@login_required
def add_employee():
    """Add single employee."""
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    batch = request.form.get('batch')
    supervisor = request.form.get('supervisor')
    manager = request.form.get('manager')
    shift = request.form.get('shift')
    department = request.form.get('department')
    role = request.form.get('role')
    tier = request.form.get('tier')
    company_email = request.form.get('company_email')
    ruex_id = request.form.get('ruex_id')
    axonify_id = request.form.get('axonify_id')
    agent_id = request.form.get('agent_id')
    access_card = request.form.get('access_card')
    token_serial = request.form.get('token_serial')
    building_card = request.form.get('building_card')

    # Parse dates
    hire_date_str = request.form.get('hire_date')
    hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date() if hire_date_str else None

    # Auto-generate employee_id from email domain
    import hashlib
    employee_id = int(hashlib.md5(company_email.encode()).hexdigest()[:8], 16)

    emp = Employee(
        employee_id=employee_id,
        first_name=first_name,
        last_name=last_name,
        full_name=f"{first_name} {last_name}",
        company_email=company_email,
        batch=batch,
        supervisor=supervisor,
        manager=manager,
        shift=shift,
        department=department,
        role=role,
        hire_date=hire_date,
        tier=int(tier) if tier else None,
        ruex_id=ruex_id or None,
        axonify_id=axonify_id or None,
        agent_id=int(agent_id) if agent_id else None,
        access_card=access_card or None,
        token_serial=token_serial or None,
        building_card=building_card or None,
        status='Active'
    )
    db.session.add(emp)
    db.session.commit()
    flash('Employee added successfully!', 'success')
    return redirect(url_for('main.employees'))


@bp.route('/employees/<int:employee_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
    """Edit employee."""
    emp = Employee.query.get_or_404(employee_id)

    if request.method == 'POST':
        emp.first_name = request.form.get('first_name')
        emp.last_name = request.form.get('last_name')
        emp.full_name = f"{emp.first_name} {emp.last_name}"
        emp.company_email = request.form.get('company_email')
        emp.batch = request.form.get('batch')
        emp.supervisor = request.form.get('supervisor')
        emp.manager = request.form.get('manager')
        emp.shift = request.form.get('shift')
        emp.department = request.form.get('department')
        emp.role = request.form.get('role')
        emp.tier = request.form.get('tier')
        emp.status = request.form.get('status')

        # Parse attrition_date - convert string to date object
        attrition_date_str = request.form.get('attrition_date')
        if attrition_date_str:
            emp.attrition_date = datetime.strptime(attrition_date_str, '%Y-%m-%d').date()
        else:
            emp.attrition_date = None

        emp.ruex_id = request.form.get('ruex_id') or None
        emp.axonify_id = request.form.get('axonify_id') or None
        emp.agent_id = request.form.get('agent_id') or None
        emp.access_card = request.form.get('access_card') or None
        emp.token_serial = request.form.get('token_serial') or None
        emp.building_card = request.form.get('building_card') or None

        db.session.commit()
        flash('Employee updated successfully!', 'success')
        return redirect(url_for('main.employees'))

    # GET request - show edit form
    return render_template('edit_employee.html', employee=emp)


@bp.route('/employees/<int:employee_id>/delete', methods=['POST'])
@login_required
def delete_employee(employee_id):
    """Delete employee."""
    emp = Employee.query.get_or_404(employee_id)
    db.session.delete(emp)
    db.session.commit()
    flash('Employee deleted successfully!', 'success')
    return redirect(url_for('main.employees'))


@bp.route('/schedules', methods=['GET', 'POST'])
@login_required
def schedules():
    """Schedule management - list and add."""
    if request.method == 'POST':
        # Handle schedule import
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename.endswith(('.xlsx', '.xls')):
                filepath = os.path.join('uploads', file.filename)
                file.save(filepath)

                try:
                    df = pd.read_excel(filepath)
                    imported = 0
                    errors = []
                    for idx, row in df.iterrows():
                        try:
                            employee_id = int(row['Employee - ID'])
                            start_date = row['Date - Nominal Date'].to_pydatetime().date()

                            start_time = None
                            if pd.notna(row['Earliest - Start']):
                                start_time = row['Earliest - Start'].to_pydatetime().time()

                            stop_time = None
                            if pd.notna(row['Latest - Stop']):
                                stop_time = row['Latest - Stop'].to_pydatetime().time()

                            # Handle overnight shifts
                            stop_date = start_date

                            work_code = str(row['Work - Code']).strip() if pd.notna(row['Work - Code']) else None

                            schedule = Schedule(
                                employee_id=employee_id,
                                start_date=start_date,
                                start_time=start_time,
                                stop_date=stop_date,
                                stop_time=stop_time,
                                work_code=work_code
                            )
                            db.session.add(schedule)
                            imported += 1
                        except Exception as e:
                            errors.append(f'Row {idx + 2}: {str(e)}')

                    db.session.commit()
                    flash(f'Imported {imported} schedules!', 'success')

                    # Return JSON for AJAX requests
                    if request.is_json:
                        return jsonify({'success': True, 'imported': imported, 'errors': errors})

                except Exception as e:
                    flash(f'Error importing schedules: {str(e)}', 'danger')
                    if request.is_json:
                        return jsonify({'success': False, 'error': str(e)})

                return redirect(url_for('main.schedules'))

        return redirect(url_for('main.schedules'))

    # Get query parameters for filtering
    view = request.args.get('view', 'table')  # 'table' or 'calendar'
    employee_id = request.args.get('employee_id', type=int)
    supervisor = request.args.get('supervisor')
    manager = request.args.get('manager')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Get all employees for filters
    employees = Employee.query.all()

    # Get unique supervisors and managers
    supervisors = db.session.query(Employee.supervisor).distinct().filter(Employee.supervisor != '').all()
    managers = db.session.query(Employee.manager).distinct().filter(Employee.manager != '').all()

    schedules_query = Schedule.query

    # Apply filters
    if employee_id:
        schedules_query = schedules_query.filter(Schedule.employee_id == employee_id)
    if supervisor:
        schedules_query = schedules_query.join(Employee).filter(Employee.supervisor == supervisor)
    if manager:
        schedules_query = schedules_query.join(Employee).filter(Employee.manager == manager)

    # Date range filter
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            schedules_query = schedules_query.filter(Schedule.start_date >= start_dt)
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            schedules_query = schedules_query.filter(Schedule.start_date <= end_dt)
        except ValueError:
            pass

    schedules_list = schedules_query.order_by(Schedule.start_date, Schedule.employee_id).all()

    # If no date range, get schedules for the next 3 weeks by default
    today = datetime.utcnow().date()
    if not start_date and not end_date:
        three_weeks = today + timedelta(days=21)
        schedules_list = Schedule.query.filter(
            Schedule.start_date >= today,
            Schedule.start_date <= three_weeks
        ).order_by(Schedule.start_date, Schedule.employee_id).all()

    # Generate date range for table view
    if schedules_list:
        min_date = min(s.start_date for s in schedules_list)
        max_date = max(s.start_date for s in schedules_list)
        date_range_days = (max_date - min_date).days + 1
        date_range = [min_date + timedelta(days=i) for i in range(date_range_days)]
    else:
        # Default: next 21 days
        date_range = [today + timedelta(days=i) for i in range(21)]

    work_codes = AdminOptions.query.filter_by(category='work_code', is_active=True).all()

    return render_template('schedules.html',
                         schedules=schedules_list,
                         work_codes=work_codes,
                         view=view,
                         employees=employees,
                         supervisors=supervisors,
                         managers=managers,
                         selected_employee_id=employee_id,
                         selected_supervisor=supervisor,
                         selected_manager=manager,
                         start_date=start_date,
                         end_date=end_date,
                         today=today,
                         date_range=date_range)


@bp.route('/attendance', methods=['GET'])
@login_required
def attendance():
    """Attendance list view."""
    attendances = Attendance.query.all()
    return render_template('attendance.html', attendances=attendances)


@bp.route('/attendance/import', methods=['GET', 'POST'])
@login_required
def attendance_import():
    """Attendance import from Excel file."""
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename.endswith(('.xlsx', '.xls')):
                filepath = os.path.join('uploads', file.filename)
                file.save(filepath)

                try:
                    df = pd.read_excel(filepath)
                    imported = 0
                    errors = []
                    for idx, row in df.iterrows():
                        try:
                            employee_id = int(row['Employee - ID'])
                            date = row['Date'].to_pydatetime().date()
                            check_in = row['Check In'].to_pydatetime().time()

                            check_out = None
                            if pd.notna(row.get('Check Out')):
                                check_out = row['Check Out'].to_pydatetime().time()

                            exception_type = None
                            if pd.notna(row.get('Exception')):
                                exception_type = str(row['Exception']).strip()

                            attendance = Attendance(
                                employee_id=employee_id,
                                date=date,
                                check_in=check_in,
                                check_out=check_out,
                                exception_type=exception_type,
                                notes=str(row.get('Notes', '') or '')
                            )
                            db.session.add(attendance)
                            imported += 1
                        except Exception as e:
                            errors.append(f'Row {idx + 2}: {str(e)}')

                    db.session.commit()
                    flash(f'Imported {imported} attendance records!', 'success')

                    # Return JSON for AJAX requests
                    if request.is_json:
                        return jsonify({'success': True, 'imported': imported, 'errors': errors})

                except Exception as e:
                    flash(f'Error importing attendance: {str(e)}', 'danger')
                    if request.is_json:
                        return jsonify({'success': False, 'error': str(e)})

                return redirect(url_for('main.attendance_import'))

        return redirect(url_for('main.attendance_import'))

    # Redirect to list view on GET
    return redirect(url_for('main.attendance'))


@bp.route('/exceptions', methods=['GET', 'POST'])
@login_required
def exceptions():
    """Exception management."""
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename.endswith(('.xlsx', '.xls')):
                filepath = os.path.join('uploads', file.filename)
                file.save(filepath)

                try:
                    df = pd.read_excel(filepath)
                    imported = 0
                    errors = []
                    for idx, row in df.iterrows():
                        try:
                            employee_id = int(row['Employee - ID'])
                            exception_type = str(row['Exception Type']).strip()
                            start_date = row['Start Date'].to_pydatetime().date()
                            end_date = row['End Date'].to_pydatetime().date()

                            work_code = None
                            if pd.notna(row.get('Work Code')):
                                work_code = str(row['Work Code']).strip()

                            exception = ExceptionRecord(
                                employee_id=employee_id,
                                exception_type=exception_type,
                                start_date=start_date,
                                end_date=end_date,
                                work_code=work_code,
                                status='Pending',
                                supervisor_override=str(row.get('Supervisor Override', '') or '')
                            )
                            db.session.add(exception)
                            imported += 1
                        except Exception as e:
                            errors.append(f'Row {idx + 2}: {str(e)}')

                    db.session.commit()
                    flash(f'Imported {imported} exception records!', 'success')

                    # Return JSON for AJAX requests
                    if request.is_json:
                        return jsonify({'success': True, 'imported': imported, 'errors': errors})

                except Exception as e:
                    flash(f'Error importing exceptions: {str(e)}', 'danger')
                    if request.is_json:
                        return jsonify({'success': False, 'error': str(e)})

                return redirect(url_for('main.exceptions'))

        return redirect(url_for('main.exceptions'))

    pending = ExceptionRecord.query.filter_by(status='Pending').all()
    completed = ExceptionRecord.query.filter_by(status='Completed').all()
    return render_template('exceptions.html', pending_exceptions=pending, completed_exceptions=completed)


@bp.route('/admin/options', methods=['GET', 'POST'])
@login_required
def admin_options():
    """Admin options management."""
    categories = ['leave_type', 'work_code', 'exception_type', 'status', 'shift', 'department', 'role']
    options_by_category = {}
    for cat in categories:
        options_by_category[cat] = AdminOptions.query.filter_by(category=cat, is_active=True).all()

    if request.method == 'POST':
        category = request.form.get('category')
        value = request.form.get('value')
        is_active = request.form.get('is_active') == 'on'

        existing = AdminOptions.query.filter_by(category=category, value=value).first()
        if not existing:
            option = AdminOptions(category=category, value=value, is_active=is_active)
            db.session.add(option)
            db.session.commit()
            flash('Option added successfully!', 'success')

        return redirect(url_for('main.admin_options'))

    return render_template('admin_options.html', categories=categories, options_by_category=options_by_category)


@bp.route('/rewards', methods=['GET', 'POST'])
@login_required
def rewards():
    """Reward program management."""
    reward_reasons = RewardReason.query.filter_by(is_active=True).all()
    recent_rewards = EmployeeReward.query.order_by(EmployeeReward.created_at.desc()).limit(10).all()

    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        reason_id = request.form.get('reason_id')
        points = request.form.get('points')
        date_awarded = request.form.get('date_awarded')

        reward = EmployeeReward(
            employee_id=employee_id,
            reason_id=reason_id,
            points=int(points),
            date_awarded=date_awarded
        )
        db.session.add(reward)
        db.session.commit()
        flash('Points awarded successfully!', 'success')

        return redirect(url_for('main.rewards'))

    return render_template('rewards.html', reward_reasons=reward_reasons, recent_rewards=recent_rewards)


# ==================== DB USERS ROUTES ====================

@bp.route('/db_users')
@login_required
def db_users():
    """Database users management."""
    db_users_list = DBUser.query.all()
    return render_template('db_users.html', db_users=db_users_list)


@bp.route('/db_users/add', methods=['POST'])
@login_required
def add_db_user():
    """Add database user."""
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    is_superuser = request.form.get('is_superuser') == 'on'
    is_active = request.form.get('is_active') == 'on'

    user = DBUser(
        username=username,
        email=email,
        is_superuser=is_superuser,
        is_active=is_active
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash('Database user added successfully!', 'success')
    return redirect(url_for('main.db_users'))


@bp.route('/db_users/<int:user_id>/edit', methods=['POST'])
@login_required
def edit_db_user(user_id):
    """Edit database user."""
    user = DBUser.query.get_or_404(user_id)

    user.username = request.form.get('username')
    user.email = request.form.get('email')
    user.is_superuser = request.form.get('is_superuser') == 'on'
    user.is_active = request.form.get('is_active') == 'on'

    if request.form.get('password'):
        user.set_password(request.form.get('password'))

    db.session.commit()
    flash('Database user updated successfully!', 'success')
    return redirect(url_for('main.db_users'))


@bp.route('/db_users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_db_user(user_id):
    """Delete database user."""
    user = DBUser.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Database user deleted successfully!', 'success')
    return redirect(url_for('main.db_users'))


# ==================== API DOCUMENTATION ====================

@bp.route('/apidocs')
def apidocs():
    """API documentation page - publicly accessible."""
    return render_template('apidocs.html')


# ==================== NEW EMPLOYEE REVIEWS ====================

@bp.route('/employees/reviews')
@login_required
def employee_reviews():
    """New employee reviews queue - admin verification."""
    pending = NewEmployeeReview.query.filter_by(status='Pending').all()
    verified = NewEmployeeReview.query.filter_by(status='Verified').all()
    rejected = NewEmployeeReview.query.filter_by(status='Rejected').all()
    return render_template('employee_reviews.html',
                         pending_reviews=pending,
                         verified_reviews=verified,
                         rejected_reviews=rejected)


@bp.route('/employees/reviews/<int:review_id>/approve', methods=['POST'])
@login_required
def approve_employee_review(review_id):
    """Approve a new employee review and create the employee record."""
    review = NewEmployeeReview.query.get_or_404(review_id)
    try:
        employee = review.approve(current_user.id if hasattr(current_user, 'id') else 1)
        db.session.add(employee)
        db.session.commit()
        flash('Employee approved and record created!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating employee record: {str(e)}', 'danger')
    return redirect(url_for('main.employee_reviews'))


@bp.route('/employees/reviews/<int:review_id>/reject', methods=['POST'])
@login_required
def reject_employee_review(review_id):
    """Reject a new employee review."""
    review = NewEmployeeReview.query.get_or_404(review_id)
    notes = request.form.get('notes', 'No notes provided')
    try:
        review.reject(notes, current_user.id if hasattr(current_user, 'id') else 1)
        db.session.commit()
        flash('Employee review rejected.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting review: {str(e)}', 'danger')
    return redirect(url_for('main.employee_reviews'))
