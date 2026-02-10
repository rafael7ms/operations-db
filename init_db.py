from datetime import datetime
from app import create_app, db
from app.models import Employee, AdminOptions, RewardReason
from app.utils.parsers import parse_name
import pandas as pd
import os


def init_database():
    """Initialize the database, seed defaults, and import Roster.xlsx."""
    # Use absolute path to the opsdb directory
    base_dir = r'C:\Users\RafaelAsprilla\OneDrive - 7 Managed Services S.A\Documents\DEV\opsdb'
    roster_path = os.path.join(base_dir, 'Roster.xlsx')

    app = create_app('development')

    with app.app_context():
        # Create all tables
        db.create_all()
        print('Tables created successfully!')

        # Add default admin user if not exists
        from app.models import User, DBUser
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@opsdb.local',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print('Default admin user created (username: admin, password: admin123)')

        # Add default database management user if not exists
        db_admin = DBUser.query.filter_by(username='db_admin').first()
        if not db_admin:
            db_admin = DBUser(
                username='db_admin',
                email='db_admin@opsdb.local',
                is_superuser=True
            )
            db_admin.set_password('dbadmin123')
            db.session.add(db_admin)
            print('Default DB admin user created (username: db_admin, password: dbadmin123)')

        # Add default dropdown options
        default_options = {
            'leave_type': ['Vacation', 'Sick', 'Personal', 'Unplanned'],
            'work_code': ['Regular', 'Training', 'Nesting', 'Meeting', 'New Hire Training'],
            'exception_type': ['Absent', 'Late', 'Early Leave', 'New Hire'],
            'status': ['Active', 'Inactive', 'On Leave'],
            'shift': ['Morning', 'Night', 'Mixed Shift'],
            'department': ['Customer Support', 'Operations', 'Training', 'IBC Support', 'Quality', 'Accounting', 'BNS', 'HR'],
            'role': ['Associate', 'OM', 'Trainer', 'Analyst', 'Supervisor', 'Receptionist'],
        }

        for category, values in default_options.items():
            for value in values:
                existing = AdminOptions.query.filter_by(category=category, value=value).first()
                if not existing:
                    option = AdminOptions(category=category, value=value, is_active=True)
                    db.session.add(option)
        print('Default dropdown options added!')

        # Add reward reasons
        reward_reasons = [
            ('Customer of the Month', 50),
            ('Quality Check Excellence', 30),
            ('Team Player', 25),
            ('Attendance Perfect', 20),
            ('Speed Leader', 15),
        ]

        for reason, points in reward_reasons:
            existing = RewardReason.query.filter_by(reason=reason).first()
            if not existing:
                db.session.add(RewardReason(reason=reason, points=points, is_active=True))
        print('Reward reasons added!')

        # Import employees from Roster.xlsx
        if os.path.exists(roster_path):
            print(f'\nImporting employees from {roster_path}...')
            df = pd.read_excel(roster_path)
            print(f'  Found {len(df)} rows in Roster.xlsx')

            imported_count = 0
            for idx, row in df.iterrows():
                try:
                    # Parse name (handles both "First Last" and "Last, First" formats)
                    first_name = str(row['First Name']).strip()
                    last_name = str(row['Last Name']).strip()

                    # Auto-generate company email
                    company_email = f"{first_name.lower()}.{last_name.lower()}@7managedservices.com"

                    # Handle missing Agent ID
                    agent_id = None
                    if pd.notna(row['Agent ID']):
                        try:
                            agent_id = int(row['Agent ID'])
                        except (ValueError, TypeError):
                            pass

                    # Handle employee_id - check if it's a valid integer
                    try:
                        employee_id = int(row['Odoo ID'])
                    except (ValueError, TypeError):
                        print(f'  Skipping row {idx + 2}: Invalid Odoo ID value: {row["Odoo ID"]}')
                        continue

                    employee = Employee(
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
                    db.session.add(employee)
                    imported_count += 1

                except Exception as e:
                    print(f'  Error importing row {idx + 2}: {str(e)}')

            db.session.commit()
            print(f'\nSuccessfully imported {imported_count} employees!')

            # Show sample of imported employees
            print('\nSample of imported employees:')
            for emp in Employee.query.limit(5).all():
                print(f'  - {emp.full_name} ({emp.company_email})')
        else:
            print(f'\nRoster.xlsx not found at expected path: {roster_path}')
            print('Skipping employee import. You can import later via the admin interface.')

        print('\nDatabase initialization complete!')
        print(f'Admin login: username="admin", password="admin123"')


def create_user(username, email, password, is_superuser=False):
    """Create a new database user."""
    from app.models import DBUser
    from app import create_app

    app = create_app('development')

    with app.app_context():
        # Check if user exists
        existing = DBUser.query.filter_by(username=username).first()
        if existing:
            print(f'User "{username}" already exists.')
            return False

        user = DBUser(
            username=username,
            email=email,
            is_superuser=is_superuser
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f'User "{username}" created successfully!')
        return True


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--create-user':
        # Interactive user creation
        print("Create New Database User")
        print("------------------------")
        username = input("Username: ")
        email = input("Email: ")
        password = input("Password: ")
        is_superuser = input("Is Superuser? (y/N): ").lower() == 'y'

        create_user(username, email, password, is_superuser)
    else:
        init_database()
