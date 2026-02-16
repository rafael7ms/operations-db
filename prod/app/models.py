from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class AdminOptions(db.Model):
    """Predefined dropdown options - manageable by admin."""
    __tablename__ = 'admin_options'

    option_id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False, index=True)
    value = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('category', 'value', name='uq_category_value'),
    )

    def __repr__(self):
        return f'<AdminOptions {self.category}: {self.value}>'


class Employee(db.Model):
    """Active employees table."""
    __tablename__ = 'employees'

    employee_id = db.Column(db.BigInteger, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    company_email = db.Column(db.String(150), nullable=False, unique=True)
    access_card = db.Column(db.String(50))
    token_serial = db.Column(db.String(100))
    building_card = db.Column(db.String(50))
    batch = db.Column(db.String(20), nullable=False)
    agent_id = db.Column(db.BigInteger)
    ruex_id = db.Column(db.String(50))
    axonify_id = db.Column(db.String(50))
    supervisor = db.Column(db.String(100), nullable=False)
    manager = db.Column(db.String(100), nullable=False)
    tier = db.Column(db.Integer)
    shift = db.Column(db.String(20), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    hire_date = db.Column(db.Date, nullable=False)
    phase_1_date = db.Column(db.Date)
    phase_2_date = db.Column(db.Date)
    phase_3_date = db.Column(db.Date)
    status = db.Column(db.String(20), nullable=False, default='Active')
    attrition_date = db.Column(db.Date)
    point_balance = db.Column(db.Integer, default=0)  # Current available points balance
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    attendances = db.relationship('Attendance', backref='employee', lazy='dynamic')
    leave_requests = db.relationship('LeaveRequest', foreign_keys='LeaveRequest.employee_id', backref='employee', lazy='dynamic')
    schedule_changes_as_employee = db.relationship('ScheduleChange', foreign_keys='ScheduleChange.employee_id', backref='employee', lazy='dynamic')
    schedule_changes_as_replacement = db.relationship('ScheduleChange', foreign_keys='ScheduleChange.replacement_id', backref='replacement_employee', lazy='dynamic')
    rewards_earned = db.relationship('EmployeeReward', foreign_keys='EmployeeReward.employee_id', backref='employee', lazy='dynamic')
    exceptions = db.relationship('ExceptionRecord', foreign_keys='ExceptionRecord.employee_id', backref='employee', lazy='dynamic')

    def __repr__(self):
        return f'<Employee {self.employee_id}: {self.full_name}>'


class EmployeeHistory(db.Model):
    """Historical records of inactive employees."""
    __tablename__ = 'employees_history'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.BigInteger, nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    company_email = db.Column(db.String(150))
    access_card = db.Column(db.String(50))
    token_serial = db.Column(db.String(100))
    building_card = db.Column(db.String(50))
    batch = db.Column(db.String(20), nullable=False)
    agent_id = db.Column(db.BigInteger)
    ruex_id = db.Column(db.String(50))
    axonify_id = db.Column(db.String(50))
    supervisor = db.Column(db.String(100), nullable=False)
    manager = db.Column(db.String(100), nullable=False)
    tier = db.Column(db.Integer)
    shift = db.Column(db.String(20), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    hire_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    attrition_date = db.Column(db.Date)
    archived_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<EmployeeHistory {self.employee_id}: {self.full_name}>'


class Schedule(db.Model):
    """Current schedules (within retention period)."""
    __tablename__ = 'schedules'

    schedule_id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.BigInteger, db.ForeignKey('employees.employee_id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time)
    stop_date = db.Column(db.Date, nullable=False)
    stop_time = db.Column(db.Time)
    work_code = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to Employee
    employee = db.relationship('Employee', backref='schedules')

    def __repr__(self):
        return f'<Schedule {self.schedule_id}: {self.employee_id} - {self.start_date}>'


class ScheduleHistory(db.Model):
    """Historical schedules (archived)."""
    __tablename__ = 'schedules_history'

    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, nullable=False, index=True)
    employee_id = db.Column(db.BigInteger, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time)
    stop_date = db.Column(db.Date, nullable=False)
    stop_time = db.Column(db.Time)
    work_code = db.Column(db.String(50))
    archived_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ScheduleHistory {self.schedule_id}>'


class Attendance(db.Model):
    """Current attendance records (check-ins + exceptions only)."""
    __tablename__ = 'attendances'

    attendance_id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.BigInteger, db.ForeignKey('employees.employee_id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    check_in = db.Column(db.Time, nullable=False)
    check_out = db.Column(db.Time)
    exception_type = db.Column(db.String(50))
    late_minutes = db.Column(db.Integer, default=0)  # Minutes late if arrival is late
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('employee_id', 'date', name='uq_employee_date'),
    )

    def __repr__(self):
        return f'<Attendance {self.attendance_id}: {self.employee_id} - {self.date}>'


class AttendanceHistory(db.Model):
    """Archived attendance records."""
    __tablename__ = 'attendances_history'

    id = db.Column(db.Integer, primary_key=True)
    attendance_id = db.Column(db.Integer, nullable=False, index=True)
    employee_id = db.Column(db.BigInteger, nullable=False)
    date = db.Column(db.Date, nullable=False)
    check_in = db.Column(db.Time, nullable=False)
    check_out = db.Column(db.Time)
    exception_type = db.Column(db.String(50))
    notes = db.Column(db.Text)
    archived_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AttendanceHistory {self.attendance_id}>'


class LeaveRequest(db.Model):
    """Leave requests (vacation, sick, etc.)."""
    __tablename__ = 'leave_requests'

    leave_id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.BigInteger, db.ForeignKey('employees.employee_id'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')
    approved_by = db.Column(db.BigInteger, db.ForeignKey('employees.employee_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)

    # Relationship with explicit foreign_keys to avoid ambiguity
    approved_by_user = db.relationship('Employee', foreign_keys=[approved_by])

    def __repr__(self):
        return f'<LeaveRequest {self.leave_id}: {self.employee_id} - {self.status}>'


class ScheduleChange(db.Model):
    """Schedule swap/cover requests."""
    __tablename__ = 'schedule_changes'

    change_id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.BigInteger, db.ForeignKey('employees.employee_id'), nullable=False)
    replacement_id = db.Column(db.BigInteger, db.ForeignKey('employees.employee_id'), nullable=False)
    schedule_date = db.Column(db.Date, nullable=False)
    change_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ScheduleChange {self.change_id}: {self.employee_id} -> {self.replacement_id}>'


class RewardReason(db.Model):
    """Definitions of reward points."""
    __tablename__ = 'reward_reasons'

    reason_id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.String(150), nullable=False, unique=True)
    points = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<RewardReason {self.reason}: {self.points} pts>'


class EmployeeReward(db.Model):
    """Employee reward points tracking - awards only."""
    __tablename__ = 'employee_rewards'

    reward_id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.BigInteger, db.ForeignKey('employees.employee_id'), nullable=False)
    reason_id = db.Column(db.Integer, db.ForeignKey('reward_reasons.reason_id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    date_awarded = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    awarded_by = db.Column(db.BigInteger, db.ForeignKey('employees.employee_id'))
    is_spent = db.Column(db.Boolean, default=False)
    spent_at = db.Column(db.DateTime)
    spent_by = db.Column(db.BigInteger, db.ForeignKey('employees.employee_id'))
    spend_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    reward_reason = db.relationship('RewardReason', backref='rewards')
    awarded_by_user = db.relationship('Employee', foreign_keys=[awarded_by])
    spent_by_user = db.relationship('Employee', foreign_keys=[spent_by])

    def __repr__(self):
        return f'<EmployeeReward {self.reward_id}: {self.employee_id} - {self.points} pts>'


class ExceptionRecord(db.Model):
    """Batch exception records (training, nesting, new hire, etc.)."""
    __tablename__ = 'exceptions'

    exception_id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.BigInteger, db.ForeignKey('employees.employee_id'), nullable=False)
    exception_type = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    work_code = db.Column(db.String(50))
    status = db.Column(db.String(20), nullable=False, default='Pending')
    notes = db.Column(db.Text)
    supervisor_override = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_by = db.Column(db.BigInteger, db.ForeignKey('employees.employee_id'))
    processed_at = db.Column(db.DateTime)

    # Relationships
    processed_by_user = db.relationship('Employee', foreign_keys=[processed_by])

    def __repr__(self):
        return f'<ExceptionRecord {self.exception_id}: {self.employee_id} - {self.exception_type}>'


class EmployeeRewardRedemption(db.Model):
    """Track when employees spend/redeem their reward points."""
    __tablename__ = 'employee_reward_redemptions'

    redemption_id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.BigInteger, db.ForeignKey('employees.employee_id'), nullable=False)
    points_redeemed = db.Column(db.Integer, nullable=False)
    redemption_date = db.Column(db.DateTime, default=datetime.utcnow)
    redemption_type = db.Column(db.String(50), nullable=False)  # Gift card, merchandise, donation, etc.
    redemption_details = db.Column(db.Text)  # Specific item, gift card number, etc.
    notes = db.Column(db.Text)
    approved_by = db.Column(db.BigInteger, db.ForeignKey('employees.employee_id'))
    approved_at = db.Column(db.DateTime)
    is_approved = db.Column(db.Boolean, default=True)  # Auto-approved by default

    # Relationships
    employee = db.relationship('Employee', foreign_keys=[employee_id], backref='reward_redemptions')
    approved_by_user = db.relationship('Employee', foreign_keys=[approved_by])

    def __repr__(self):
        return f'<EmployeeRewardRedemption {self.redemption_id}: {self.employee_id} - {self.points_redeemed} pts>'


class NewEmployeeReview(db.Model):
    """Queue for new employees added from roster uploads - requires admin verification."""
    __tablename__ = 'new_employee_reviews'

    review_id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.BigInteger, nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    batch = db.Column(db.String(20), nullable=False)
    supervisor = db.Column(db.String(100), nullable=False)
    manager = db.Column(db.String(100), nullable=False)
    tier = db.Column(db.Integer)
    shift = db.Column(db.String(20), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    hire_date = db.Column(db.Date)
    phase_1_date = db.Column(db.Date)
    phase_2_date = db.Column(db.Date)
    phase_3_date = db.Column(db.Date)
    ruex_id = db.Column(db.String(50))
    axonify_id = db.Column(db.String(50))
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default='Pending')  # Pending, Verified, Rejected
    reviewed_by = db.Column(db.BigInteger, db.ForeignKey('employees.employee_id'))
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    reviewed_by_user = db.relationship('Employee', foreign_keys=[reviewed_by])

    def __repr__(self):
        return f'<NewEmployeeReview {self.review_id}: {self.full_name} - {self.status}>'

    def approve(self, reviewed_by_id):
        """Approve the review and create the actual employee record."""
        employee = Employee(
            employee_id=self.employee_id,
            first_name=self.first_name,
            last_name=self.last_name,
            full_name=self.full_name,
            company_email=f"{self.first_name.lower()}.{self.last_name.lower()}@7managedservices.com",
            batch=self.batch,
            supervisor=self.supervisor,
            manager=self.manager,
            tier=self.tier,
            shift=self.shift,
            department=self.department,
            role=self.role,
            hire_date=self.hire_date,
            phase_1_date=self.phase_1_date,
            phase_2_date=self.phase_2_date,
            phase_3_date=self.phase_3_date,
            ruex_id=self.ruex_id,
            axonify_id=self.axonify_id,
            status='Active'
        )
        self.status = 'Verified'
        self.reviewed_by = reviewed_by_id
        self.reviewed_at = datetime.utcnow()
        return employee

    def reject(self, notes, reviewed_by_id):
        """Reject the review."""
        self.status = 'Rejected'
        self.notes = f"Rejected: {notes}\nOriginal: {self.notes}"
        self.reviewed_by = reviewed_by_id
        self.reviewed_at = datetime.utcnow()


class User(UserMixin, db.Model):
    """System users for admin access."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class DBUser(db.Model):
    """Database management users - separate from system users."""
    __tablename__ = 'db_users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_superuser = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    notes = db.Column(db.Text)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<DBUser {self.username}>'


# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    """Load user from either User or DBUser table."""
    from app.models import User, DBUser
    user = User.query.get(int(user_id))
    if user:
        return user
    return DBUser.query.get(int(user_id))
