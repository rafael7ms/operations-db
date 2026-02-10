from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, TimeField, TextAreaField, SubmitField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Email, Optional
from datetime import date


class EmployeeForm(FlaskForm):
    """Form for adding/editing employees."""
    employee_id = IntegerField('Employee ID (Odoo ID)', validators=[DataRequired()])
    name = StringField('Name (First Last or Last, First)', validators=[DataRequired()])
    email = StringField('Company Email', validators=[DataRequired(), Email()])
    batch = StringField('Batch', validators=[DataRequired()])
    agent_id = IntegerField('Agent ID', validators=[Optional()])
    bo_user = StringField('Back Office User', validators=[Optional()])
    axonify = StringField('Axonify', validators=[Optional()])
    supervisor = StringField('Supervisor', validators=[DataRequired()])
    manager = StringField('Manager', validators=[DataRequired()])
    tier = IntegerField('Tier', validators=[Optional()])
    shift = SelectField('Shift', choices=[], validators=[DataRequired()])
    department = SelectField('Department', choices=[], validators=[DataRequired()])
    role = SelectField('Role', choices=[], validators=[DataRequired()])
    hire_date = DateField('Hire Date', validators=[DataRequired()], default=date.today)
    phase_1_date = DateField('Phase 1 Date', validators=[Optional()])
    phase_2_date = DateField('Phase 2 Date', validators=[Optional()])
    phase_3_date = DateField('Phase 3 Date', validators=[Optional()])
    status = SelectField('Status', choices=[], validators=[DataRequired()])
    attrition_date = DateField('Attrition Date', validators=[Optional()])
    access_card = StringField('Access Card', validators=[Optional()])
    token_serial = StringField('Token Serial', validators=[Optional()])
    building_card = StringField('Building Card', validators=[Optional()])
    submit = SubmitField('Save')


class ScheduleForm(FlaskForm):
    """Form for adding schedules."""
    employee_id = IntegerField('Employee ID', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    start_time = TimeField('Start Time', validators=[Optional()])
    stop_date = DateField('Stop Date', validators=[DataRequired()])
    stop_time = TimeField('Stop Time', validators=[Optional()])
    work_code = SelectField('Work Code', choices=[], validators=[Optional()])
    submit = SubmitField('Save Schedule')


class UploadForm(FlaskForm):
    """Form for batch uploads."""
    file = StringField('File Path', validators=[DataRequired()])
    upload_type = SelectField('Upload Type', choices=[
        ('schedules', 'Schedules'),
        ('exceptions', 'Exceptions'),
        ('attendances', 'Attendances')
    ], validators=[DataRequired()])
    submit = SubmitField('Upload')


class LeaveRequestForm(FlaskForm):
    """Form for leave requests."""
    employee_id = IntegerField('Employee ID', validators=[DataRequired()])
    leave_type = SelectField('Leave Type', choices=[], validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    submit = SubmitField('Submit Request')


class ExceptionForm(FlaskForm):
    """Form for exception records."""
    employee_id = IntegerField('Employee ID', validators=[DataRequired()])
    exception_type = SelectField('Exception Type', choices=[], validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    work_code = SelectField('Work Code', choices=[], validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    supervisor_override = StringField('Supervisor Override (for new hires)', validators=[Optional()])
    submit = SubmitField('Create Exception')


class AdminOptionForm(FlaskForm):
    """Form for admin dropdown options."""
    category = SelectField('Category', choices=[
        ('leave_type', 'Leave Type'),
        ('work_code', 'Work Code'),
        ('exception_type', 'Exception Type'),
        ('status', 'Status'),
        ('shift', 'Shift'),
        ('department', 'Department'),
        ('role', 'Role')
    ], validators=[DataRequired()])
    value = StringField('Value', validators=[DataRequired()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Option')


class RewardReasonForm(FlaskForm):
    """Form for reward reasons."""
    reason = StringField('Reward Reason', validators=[DataRequired()])
    points = IntegerField('Points', validators=[DataRequired()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Reason')
