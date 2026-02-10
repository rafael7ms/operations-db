import pandas as pd
from datetime import datetime, timedelta
from app import db
from app.models import Employee, Schedule, Attendance, ExceptionRecord


def process_employee_upload(file_path):
    """
    Process employee Excel upload and add to database.
    Returns (success_count, error_count, errors_list).
    """
    errors = []
    success_count = 0

    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        return 0, 1, [f'Error reading file: {str(e)}']

    required_columns = ['Odoo ID', 'First Name', 'Last Name', 'Batch', 'Supervisor',
                       'Manager', 'Shift', 'Department', 'Role', 'Hire Date',
                       'Company Email']

    # Check for required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        return 0, 1, [f'Missing required columns: {missing_cols}']

    for idx, row in df.iterrows():
        try:
            # Parse name if in "Last, First" format
            first_name = str(row['First Name']).strip()
            last_name = str(row['Last Name']).strip()

            # Check if employee already exists
            employee_id = int(row['Odoo ID'])
            existing = Employee.query.get(employee_id)
            if existing:
                errors.append(f'Employee {employee_id} already exists, skipping')
                continue

            employee = Employee(
                employee_id=employee_id,
                first_name=first_name,
                last_name=last_name,
                full_name=f"{first_name} {last_name}",
                company_email=str(row['Company Email']).strip(),
                batch=str(row['Batch']).strip(),
                supervisor=str(row['Supervisor']).strip(),
                manager=str(row['Manager']).strip(),
                shift=str(row['Shift']).strip(),
                department=str(row['Department']).strip(),
                role=str(row['Role']).strip(),
                hire_date=row['Hire Date'].to_pydatetime().date() if pd.notna(row['Hire Date']) else None,
                tier=int(row['Tier']) if pd.notna(row['Tier']) else None,
                agent_id=int(row['Agent ID']) if pd.notna(row['Agent ID']) else None,
                bo_user=str(row['BO User']).strip() if pd.notna(row['BO User']) else None,
                axonify=str(row['Axonify']).strip() if pd.notna(row['Axonify']) else None,
                status='Active'
            )

            db.session.add(employee)
            success_count += 1

        except Exception as e:
            errors.append(f'Row {idx + 2}: {str(e)}')

    db.session.commit()
    return success_count, len(errors), errors


def process_schedule_upload(file_path):
    """
    Process schedule Excel upload and add to database.
    """
    errors = []
    success_count = 0

    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        return 0, 1, [f'Error reading file: {str(e)}']

    required_columns = ['Employee - ID', 'Date - Nominal Date', 'Earliest - Start',
                       'Latest - Stop', 'Work - Code']

    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        return 0, 1, [f'Missing required columns: {missing_cols}']

    for idx, row in df.iterrows():
        try:
            employee_id = int(row['Employee - ID'])
            start_date = row['Date - Nominal Date'].to_pydatetime().date()

            # Parse time - some may be empty (OFF day)
            start_time = None
            if pd.notna(row['Earliest - Start']):
                start_time = row['Earliest - Start'].to_pydatetime().time()

            stop_time = None
            if pd.notna(row['Latest - Stop']):
                stop_time = row['Latest - Stop'].to_pydatetime().time()

            # Handle overnight shifts - determine stop date
            stop_date = start_date
            if stop_time and start_time:
                start_dt = datetime.combine(start_date, start_time)
                stop_dt = datetime.combine(start_date, stop_time)
                if stop_dt < start_dt:
                    stop_date = start_date + timedelta(days=1)

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
            success_count += 1

        except Exception as e:
            errors.append(f'Row {idx + 2}: {str(e)}')

    db.session.commit()
    return success_count, len(errors), errors


def process_attendance_upload(file_path):
    """
    Process attendance Excel upload and add to database.
    """
    errors = []
    success_count = 0

    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        return 0, 1, [f'Error reading file: {str(e)}']

    required_columns = ['Employee - ID', 'Date', 'Check In']

    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        return 0, 1, [f'Missing required columns: {missing_cols}']

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
            success_count += 1

        except Exception as e:
            errors.append(f'Row {idx + 2}: {str(e)}')

    db.session.commit()
    return success_count, len(errors), errors


def process_exception_upload(file_path):
    """
    Process exception Excel upload and create exception records.
    """
    errors = []
    success_count = 0

    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        return 0, 1, [f'Error reading file: {str(e)}']

    required_columns = ['Employee - ID', 'Exception Type', 'Start Date', 'End Date']

    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        return 0, 1, [f'Missing required columns: {missing_cols}']

    for idx, row in df.iterrows():
        try:
            employee_id = int(row['Employee - ID'])
            exception_type = str(row['Exception Type']).strip()

            start_date = row['Start Date'].to_pydatetime().date()
            end_date = row['End Date'].to_pydatetime().date()

            work_code = None
            if pd.notna(row.get('Work Code')):
                work_code = str(row['Work Code']).strip()

            supervisor_override = None
            if pd.notna(row.get('Supervisor Override')):
                supervisor_override = str(row['Supervisor Override']).strip()

            exception = ExceptionRecord(
                employee_id=employee_id,
                exception_type=exception_type,
                start_date=start_date,
                end_date=end_date,
                work_code=work_code,
                status='Pending',
                notes=str(row.get('Notes', '') or ''),
                supervisor_override=supervisor_override
            )

            db.session.add(exception)
            success_count += 1

        except Exception as e:
            errors.append(f'Row {idx + 2}: {str(e)}')

    db.session.commit()
    return success_count, len(errors), errors
