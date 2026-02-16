import pandas as pd
from datetime import datetime, timedelta, time
from app import db
from app.models import Employee, Schedule, Attendance, ExceptionRecord, NewEmployeeReview


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

    # Detect file format based on columns
    # New Roster format: ['#', 'Name', 'Last Name', 'First Name', 'Batch', 'BO User', ...]
    # Old format: ['Odoo ID', 'First Name', 'Last Name', 'Batch', 'Company Email', ...]

    # Check for new roster format (has 'Name' column)
    if 'Name' in df.columns and '#' in df.columns:
        return process_new_roster_upload(file_path, df)

    # Check for old format
    required_columns = ['Odoo ID', 'First Name', 'Last Name', 'Batch', 'Supervisor',
                       'Manager', 'Shift', 'Department', 'Role', 'Hire Date',
                       'Company Email']

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
                ruex_id=str(row.get('BO User', '')).strip() if pd.notna(row.get('BO User')) else None,
                axonify_id=str(row.get('Axonify', '')).strip() if pd.notna(row.get('Axonify')) else None,
                status='Active'
            )

            db.session.add(employee)
            success_count += 1

        except Exception as e:
            errors.append(f'Row {idx + 2}: {str(e)}')

    db.session.commit()
    return success_count, len(errors), errors


def process_new_roster_upload(file_path, df=None):
    """
    Process new Roster format Excel upload.
    Adds employees to a review queue for admin verification.
    Returns (success_count, error_count, errors_list).
    """
    if df is None:
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            return 0, 1, [f'Error reading file: {str(e)}']

    # New Roster columns: ['#', 'Name', 'Last Name', 'First Name', 'Batch', 'BO User',
    # 'Axonify', 'Supervisor', 'Manager', 'Tier', 'Shift', 'Schedule', 'Department',
    # 'Role', 'Phase 1 Date', 'Phase 2 Date', 'Phase 3 Date', 'Hire Date']

    errors = []
    success_count = 0

    # Check for required columns
    required_columns = ['#', 'Name', 'Last Name', 'First Name', 'Batch', 'Supervisor',
                       'Manager', 'Shift', 'Department', 'Role', 'Hire Date']

    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        return 0, 1, [f'Missing required columns: {missing_cols}']

    for idx, row in df.iterrows():
        try:
            # Parse name - in format "First Last"
            first_name = str(row['First Name']).strip()
            last_name = str(row['Last Name']).strip()
            full_name = str(row['Name']).strip()

            # Get employee ID from '#' column
            employee_id = int(row['#'])

            # Check if employee already exists
            existing = Employee.query.get(employee_id)
            if existing:
                errors.append(f'Employee {employee_id} already exists, skipping')
                continue

            # Create NewEmployeeReview record instead of adding directly
            review = NewEmployeeReview(
                employee_id=employee_id,
                first_name=first_name,
                last_name=last_name,
                full_name=full_name,
                batch=str(row['Batch']).strip(),
                supervisor=str(row['Supervisor']).strip() if pd.notna(row.get('Supervisor')) else '',
                manager=str(row['Manager']).strip() if pd.notna(row.get('Manager')) else '',
                shift=str(row['Shift']).strip() if pd.notna(row.get('Shift')) else '',
                department=str(row['Department']).strip() if pd.notna(row.get('Department')) else '',
                role=str(row['Role']).strip() if pd.notna(row.get('Role')) else '',
                hire_date=row['Hire Date'].to_pydatetime().date() if pd.notna(row['Hire Date']) else None,
                phase_1_date=row['Phase 1 Date'].to_pydatetime().date() if pd.notna(row['Phase 1 Date']) else None,
                phase_2_date=row['Phase 2 Date'].to_pydatetime().date() if pd.notna(row['Phase 2 Date']) else None,
                phase_3_date=row['Phase 3 Date'].to_pydatetime().date() if pd.notna(row['Phase 3 Date']) else None,
                ruex_id=str(row.get('BO User', '')).strip() if pd.notna(row.get('BO User')) else None,
                axonify_id=str(row.get('Axonify', '')).strip() if pd.notna(row.get('Axonify')) else None,
                notes='New employee added from roster upload - pending admin review',
                status='Pending'
            )

            db.session.add(review)
            success_count += 1

        except Exception as e:
            errors.append(f'Row {idx + 2}: {str(e)}')

    db.session.commit()
    return success_count, len(errors), errors


def build_ruex_id_mapping():
    """
    Build a mapping from RUEX ID (first letter + last name) to employee Odoo ID.
    Returns a dict mapping RUEX IDs to employee records.
    """
    employees = Employee.query.all()
    mapping = {}
    for emp in employees:
        # Create RUEX ID from first letter of first name + last name (lowercase)
        ruex_id = (emp.first_name[0] if emp.first_name else '') + emp.last_name
        ruex_id = ruex_id.lower().strip()
        mapping[ruex_id] = emp.employee_id
    return mapping


def process_schedule_upload(file_path, employee_file_path=None):
    """
    Process schedule Excel upload and add to database.

    Args:
        file_path: Path to the schedule Excel file
        employee_file_path: Optional path to employee Excel file for RUEX ID matching

    Returns:
        (success_count, error_count, errors_list)
    """
    errors = []
    success_count = 0

    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        return 0, 1, [f'Error reading file: {str(e)}']

    # Detect format - check if first row has actual data or just headers
    # New format: Headers in row 0 with names like 'Employee - ID'
    # Old format: Headers in row 0 with names like 'Employee - ID'
    # Both formats should be compatible, but we need to handle row 0 as header

    # Check for new format (multi-level headers in row 0)
    first_row = df.iloc[0].astype(str).tolist() if len(df) > 0 else []
    is_new_format = 'Employee - ID' in first_row

    # Skip header row if it's in the first row
    if is_new_format:
        df = df.iloc[1:].reset_index(drop=True)

    # Map column names to expected format
    # New format columns might be: 'Employee - ID', 'Employee - First Name', 'Employee - Last Name',
    # 'Date - Nominal Date', 'Earliest - Start', 'Latest - Stop', 'Work - Code'
    # Old format columns: 'Employee - ID', 'Date - Nominal Date', 'Earliest - Start',
    # 'Latest - Stop', 'Work - Code'

    required_columns = ['Employee - ID', 'Date - Nominal Date', 'Earliest - Start',
                       'Latest - Stop', 'Work - Code']

    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        return 0, 1, [f'Missing required columns: {missing_cols}']

    # Build RUEX ID mapping if employee file is provided
    ruex_mapping = {}
    if employee_file_path:
        try:
            emp_df = pd.read_excel(employee_file_path)
            # Build mapping from RUEX ID (first letter + last name) to Odoo ID
            for idx, row in emp_df.iterrows():
                first_name = str(row.get('First Name', '')).strip()
                last_name = str(row.get('Last Name', '')).strip()
                odoo_id = row.get('Odoo ID')

                if first_name and last_name and pd.notna(odoo_id):
                    # Create RUEX ID: first letter of first name + last name (lowercase)
                    ruex_id = (first_name[0] if first_name else '') + last_name
                    ruex_id = ruex_id.lower()
                    ruex_mapping[ruex_id] = int(odoo_id)
        except Exception as e:
            errors.append(f'Error reading employee file: {str(e)}')

    for idx, row in df.iterrows():
        try:
            # The Employee - ID column contains RUEX ID (first letter + last name)
            # Try to look up the Odoo ID from mapping
            ruex_id = str(row['Employee - ID']).strip().lower()

            if ruex_id in ruex_mapping:
                employee_id = ruex_mapping[ruex_id]
            elif ruex_id.isdigit():
                # If it's already a number, use it directly
                employee_id = int(ruex_id)
            else:
                # Try to find employee by name if RUEX ID not in mapping
                # Parse the RUEX ID to extract first letter and last name
                if len(ruex_id) > 1:
                    first_letter = ruex_id[0]
                    last_name = ruex_id[1:]
                    emp = Employee.query.filter(
                        Employee.first_name.ilike(f'{first_letter}%'),
                        Employee.last_name.ilike(f'{last_name}%')
                    ).first()
                    if emp:
                        employee_id = emp.employee_id
                    else:
                        errors.append(f'Row {idx + 2}: Could not find employee for RUEX ID {ruex_id}')
                        continue
                else:
                    errors.append(f'Row {idx + 2}: Invalid RUEX ID format {ruex_id}')
                    continue

            # Parse date - handle both datetime objects and strings
            date_val = row['Date - Nominal Date']
            if pd.notna(date_val):
                if hasattr(date_val, 'to_pydatetime'):
                    start_date = date_val.to_pydatetime().date()
                else:
                    # Handle string dates
                    start_date = pd.to_datetime(str(date_val)).date()
            else:
                start_date = None

            # Parse time - some may be empty (OFF day)
            start_time = None
            if pd.notna(row['Earliest - Start']):
                time_val = row['Earliest - Start']
                if hasattr(time_val, 'to_pydatetime'):
                    start_time = time_val.to_pydatetime().time()
                else:
                    # Handle string times
                    time_str = str(time_val)
                    if ':' in time_str:
                        parts = time_str.split(':')
                        if len(parts) >= 2:
                            start_time = time(int(parts[0]), int(parts[1]))

            stop_time = None
            if pd.notna(row['Latest - Stop']):
                time_val = row['Latest - Stop']
                if hasattr(time_val, 'to_pydatetime'):
                    stop_time = time_val.to_pydatetime().time()
                else:
                    # Handle string times
                    time_str = str(time_val)
                    if ':' in time_str:
                        parts = time_str.split(':')
                        if len(parts) >= 2:
                            stop_time = time(int(parts[0]), int(parts[1]))

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
