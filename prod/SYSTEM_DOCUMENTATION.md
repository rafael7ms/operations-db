# Operations DB - System Documentation

## Overview

Operations DB is a workforce scheduling and attendance management system built with Flask, designed for operations departments. The application manages employees, schedules, attendance records, leave requests, exceptions, and reward points programs.

---

## Architecture

### Technology Stack
- **Framework**: Flask (Python)
- **Database**: SQLite (production-ready for deployment)
- **ORM**: SQLAlchemy
- **Excel Processing**: Pandas + OpenPyXL
- **Authentication**: Flask-Login
- **Deployment**: AWS (S3, Lambda, API Gateway) via SAM/Terraform

### Database Design

The database uses a **split architecture** with separate tables for current data and historical/archived data:

| Main Table | History Table | Purpose |
|------------|---------------|---------|
| `employees` | `employees_history` | Active vs archived employees |
| `schedules` | `schedules_history` | Current vs old schedules (>2 months) |
| `attendances` | `attendances_history` | Current vs archived attendance |
| - | - | - |

---

## Data Models

### 1. Employee (`employees`)
Represents active employees in the system.

| Field | Type | Description |
|-------|------|-------------|
| `employee_id` | BigInteger | Primary key (Odoo ID) |
| `first_name` | String(100) | Employee first name |
| `last_name` | String(100) | Employee last name |
| `full_name` | String(200) | Combined name |
| `company_email` | String(150) | Work email (unique) |
| `access_card` | String(50) | Physical access card number |
| `token_serial` | String(100) | Security token serial |
| `building_card` | String(50) | Building access card |
| `batch` | String(20) | Hiring batch/ cohort |
| `agent_id` | BigInteger | Agent system ID |
| `ruex_id` | String(50) | RUEX ID (first letter + last name) |
| `axonify_id` | String(50) | Axonify training ID |
| `supervisor` | String(100) | Direct supervisor name |
| `manager` | String(100) | Manager name |
| `tier` | Integer | Performance tier |
| `shift` | String(20) | Day/Night/Rotating |
| `department` | String(50) | Department name |
| `role` | String(50) | Job role title |
| `hire_date` | Date | Original hire date |
| `phase_1_date` | Date | Training phase 1 completion |
| `phase_2_date` | Date | Training phase 2 completion |
| `phase_3_date` | Date | Training phase 3 completion |
| `status` | String(20) | Active/Inactive/On Leave |
| `attrition_date` | Date | Termination date |
| `created_at` | DateTime | Record creation timestamp |
| `updated_at` | DateTime | Last update timestamp |

### 2. EmployeeHistory (`employees_history`)
Archived employee records with `archived_date`.

### 3. Schedule (`schedules`)
Daily work schedule for employees.

| Field | Type | Description |
|-------|------|-------------|
| `schedule_id` | Integer | Primary key |
| `employee_id` | BigInteger | Foreign key to employees |
| `start_date` | Date | Work date |
| `start_time` | Time | Shift start time |
| `stop_date` | Date | Shift end date (handles overnight) |
| `stop_time` | Time | Shift end time |
| `work_code` | String(50) | REG, NIGHT, OT, OFF, TRAIN, etc. |
| `created_at` | DateTime | Record creation timestamp |

### 4. ScheduleHistory (`schedules_history`)
Archived schedules older than 2 months.

### 5. Attendance (`attendances`)
Check-in records with exceptions tracking.

| Field | Type | Description |
|-------|------|-------------|
| `attendance_id` | Integer | Primary key |
| `employee_id` | BigInteger | Foreign key to employees |
| `date` | Date | Attendance date |
| `check_in` | Time | Employee check-in time |
| `check_out` | Time | Employee check-out time |
| `exception_type` | String(50) | OT, Sick, Vacation, etc. |
| `notes` | Text | Additional notes |
| `created_at` | DateTime | Record creation timestamp |
| **Unique Constraint**: `employee_id + date` |

### 6. AttendanceHistory (`attendances_history`)
Archived attendance records.

### 7. LeaveRequest (`leave_requests`)
Vacation, sick leave, and personal time requests.

| Field | Type | Description |
|-------|------|-------------|
| `leave_id` | Integer | Primary key |
| `employee_id` | BigInteger | Foreign key to employees |
| `leave_type` | String(50) | Vacation/Sick/Personal/Bereavement |
| `start_date` | Date | Leave start date |
| `end_date` | Date | Leave end date |
| `status` | String(20) | Pending/Approved/Rejected |
| `approved_by` | BigInteger | Foreign key to approving employee |
| `created_at` | DateTime | Request submission timestamp |
| `approved_at` | DateTime | Approval timestamp |

### 8. ScheduleChange (`schedule_changes`)
Swap/cover request records.

| Field | Type | Description |
|-------|------|-------------|
| `change_id` | Integer | Primary key |
| `employee_id` | BigInteger | Original employee |
| `replacement_id` | BigInteger | Replacement employee |
| `schedule_date` | Date | Date of schedule change |
| `change_type` | String(20) | Swap/Cover |
| `status` | String(20) | Pending/Approved/Rejected |
| `created_at` | DateTime | Request timestamp |

### 9. RewardReason (`reward_reasons`)
Definitions for reward point categories.

| Field | Type | Description |
|-------|------|-------------|
| `reason_id` | Integer | Primary key |
| `reason` | String(150) | Description (unique) |
| `points` | Integer | Points awarded |
| `is_active` | Boolean | Enable/disable reason |
| `created_at` | DateTime | Record creation timestamp |

### 10. EmployeeReward (`employee_rewards`)
Points awards and redemption tracking.

| Field | Type | Description |
|-------|------|-------------|
| `reward_id` | Integer | Primary key |
| `employee_id` | BigInteger | Employee receiving points |
| `reason_id` | Integer | Foreign key to reward reasons |
| `points` | Integer | Points awarded |
| `date_awarded` | Date | Award date |
| `notes` | Text | Award notes |
| `awarded_by` | BigInteger | Admin who awarded |
| `is_spent` | Boolean | Redemption status |
| `spent_at` | DateTime | When points were spent |
| `spent_by` | BigInteger | Who approved redemption |
| `spend_reason` | Text | Reason for spending |
| `created_at` | DateTime | Record creation timestamp |

### 11. EmployeeRewardRedemption (`employee_reward_redemptions`)
Detailed redemption records.

| Field | Type | Description |
|-------|------|-------------|
| `redemption_id` | Integer | Primary key |
| `employee_id` | BigInteger | Employee redeeming points |
| `points_redeemed` | Integer | Number of points |
| `redemption_date` | DateTime | Redemption timestamp |
| `redemption_type` | String(50) | Gift card/merchandise/donation |
| `redemption_details` | Text | Specific item details |
| `notes` | Text | Additional notes |
| `approved_by` | BigInteger | Approving manager |
| `approved_at` | DateTime | Approval timestamp |
| `is_approved` | Boolean | Auto-approved by default |

### 12. ExceptionRecord (`exceptions`)
Batch exception processing (Training, Nesting, New Hire Training, etc.).

| Field | Type | Description |
|-------|------|-------------|
| `exception_id` | Integer | Primary key |
| `employee_id` | BigInteger | Employee affected |
| `exception_type` | String(50) | Training/Nesting/Vacation/etc. |
| `start_date` | Date | Exception start date |
| `end_date` | Date | Exception end date |
| `work_code` | String(50) | Work code during exception |
| `status` | String(20) | Pending/Completed |
| `notes` | Text | Additional notes |
| `supervisor_override` | String(100) | Supervisor approval |
| `created_at` | DateTime | Record creation timestamp |
| `processed_by` | BigInteger | Processing admin |
| `processed_at` | DateTime | Processing timestamp |

### 13. AdminOptions (`admin_options`)
Predefined dropdown values managed by admin.

| Field | Type | Description |
|-------|------|-------------|
| `option_id` | Integer | Primary key |
| `category` | String(50) | Category (department, role, shift, etc.) |
| `value` | String(100) | Option value |
| `is_active` | Boolean | Enable/disable |
| `created_at` | DateTime | Record creation timestamp |
| **Unique Constraint**: `category + value` |

### 14. User (`users`)
System users for admin access.

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `username` | String(80) | Login username (unique) |
| `email` | String(120) | Email (unique) |
| `password_hash` | String(128) | Hashed password |
| `is_admin` | Boolean | Admin permissions |
| `created_at` | DateTime | Account creation |

### 15. DBUser (`db_users`)
Database management users (separate from system users).

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `username` | String(80) | Username (unique) |
| `email` | String(120) | Email (unique) |
| `password_hash` | String(128) | Hashed password |
| `is_superuser` | Boolean | Superuser permissions |
| `is_active` | Boolean | Account status |
| `created_at` | DateTime | Account creation |
| `last_login` | DateTime | Last login timestamp |
| `notes` | Text | Administrative notes |

---

## API Endpoints

All API endpoints are prefixed with `/api/`.

### Health Check
```
GET /api/health
Response: {"status": "healthy"}
```

### Employees

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/employees` | List all active employees |
| GET | `/api/employees/<id>` | Get single employee details |
| POST | `/api/employees` | Create new employee |
| PUT | `/api/employees/<id>` | Update employee |
| DELETE | `/api/employees/<id>` | Delete employee |
| POST | `/api/employees/batch` | Bulk import from Excel |

### Schedules

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/schedules` | List schedules (with filters) |
| POST | `/api/schedules` | Create single schedule |
| POST | `/api/schedules/batch` | Bulk import with RUEX ID matching |

**Query Parameters for Schedules:**
- `start_date`: Filter start date (YYYY-MM-DD)
- `end_date`: Filter end date (YYYY-MM-DD)
- `employee_id`: Filter by employee ID

### Attendances

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/attendances` | List attendances (with filters) |
| POST | `/api/attendances` | Create attendance record |
| PUT | `/api/attendances/<emp_id>/<date>` | Update attendance |
| POST | `/api/attendances/batch` | Bulk import from Excel |

### Leave Requests

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/leave_requests` | List leave requests |
| POST | `/api/leave_requests` | Create leave request |
| POST | `/api/leave_requests/<id>/approve` | Approve leave request |

### Exceptions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/exceptions` | List exception records |
| POST | `/api/exceptions` | Create exception record |
| POST | `/api/exceptions/<id>/process` | Process exception |
| POST | `/api/exceptions/batch` | Bulk import from Excel |

### Admin Options

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/options` | List admin options |
| POST | `/api/admin/options` | Create admin option |

### Rewards

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/rewards/reasons` | List reward reasons |
| GET | `/api/rewards/employee/<id>` | Get employee reward history |
| POST | `/api/rewards/award` | Award points to employee |
| POST | `/api/rewards/award/batch` | Bulk award points |

---

## Batch Upload Processes

### Employee Upload (`/api/employees/batch`)

**Excel Requirements:**
- Column A: `Odoo ID` (required)
- Column B: `First Name` (required)
- Column C: `Last Name` (required)
- Column D: `Batch` (required)
- Column E: `Supervisor` (required)
- Column F: `Manager` (required)
- Column G: `Shift` (required)
- Column H: `Department` (required)
- Column I: `Role` (required)
- Column J: `Hire Date` (required)
- Column K: `Company Email` (required)
- Columns L-O: Optional (Tier, Agent ID, BO User, Axonify)

**Process:**
1. Read Excel file with pandas
2. Validate required columns exist
3. Check for duplicate Odoo IDs (skip if exists)
4. Create Employee record with parsed data
5. Track errors per row

### Schedule Upload (`/api/schedules/batch`)

**Excel Requirements:**
- Column A: `Employee - ID` (RUEX ID or Odoo ID)
- Column B: `Date - Nominal Date`
- Column C: `Earliest - Start` (time)
- Column D: `Latest - Stop` (time)
- Column E: `Work - Code` (REG, NIGHT, OT, OFF, TRAIN)

**RUEX ID Matching:**
The RUEX ID format is: **first letter of first name + last name** (lowercase)

**Example:**
- Name: "John Smith" → RUEX ID: `jsmith`
- Name: "Maria Garcia" → RUEX ID: `mgarcia`

**Process:**
1. Read Excel file
2. **Optional**: If employee file provided, build RUEX→Odoo ID mapping
3. For each schedule row:
   - Look up RUEX ID in mapping (or fallback to DB name search)
   - Handle string dates/times (Excel format compatibility)
   - Handle overnight shifts (stop_time < start_time)
4. Create Schedule record

### Attendance Upload (`/api/attendances/batch`)

**Excel Requirements:**
- Column A: `Employee - ID` (Odoo ID)
- Column B: `Date`
- Column C: `Check In` (required)
- Column D: `Check Out` (optional)
- Column E: `Exception` (optional)
- Column F: `Notes` (optional)

**Process:**
1. Read Excel file
2. Validate required columns
3. Create Attendance record
4. Handle duplicate entries (unique constraint on employee+date)

### Exception Upload (`/api/exceptions/batch`)

**Excel Requirements:**
- Column A: `Employee - ID` (Odoo ID)
- Column B: `Exception Type`
- Column C: `Start Date`
- Column D: `End Date`
- Column E: `Work Code` (optional)
- Column F: `Supervisor Override` (optional)
- Column G: `Notes` (optional)

**Process:**
1. Read Excel file
2. Validate required columns
3. Create ExceptionRecord with status='Pending'
4. Track errors per row

### Reward Upload (`/api/rewards/award/batch`)

**Excel Requirements:**
- Column A: `Employee - ID` (Odoo ID)
- Column B: `Reason ID`
- Column C: `Points`
- Column D: `Date Awarded`
- Column E: `Notes` (optional)

**Process:**
1. Read Excel file
2. Validate employee exists
3. Validate reason exists and is active
4. Create EmployeeReward record
5. Track errors per row

---

## Default Values & Constants

### Status Values
- **Employee**: Active, Inactive, On Leave
- **Schedule Change**: Pending, Approved, Rejected
- **Leave Request**: Pending, Approved, Rejected
- **Exception**: Pending, Completed

### Work Codes
- `REG` - Regular shift
- `NIGHT` - Night shift
- `OT` - Overtime
- `OFF` - Day off
- `TRAIN` - Training
- `NEST` - Nesting
- `VACATION` - Vacation
- `SICK` - Sick leave

### Training Phases
- `phase_1_date` - Initial training completion
- `phase_2_date` - Intermediate training completion
- `phase_3_date` - Final training completion

---

## Deployment

### Local Development
```bash
cd prod
python run.py
```
Server runs on `http://127.0.0.1:5443`

### Default Credentials (after initialization)
- Username: `admin`
- Password: `admin123`

### AWS Deployment (SAM)
```bash
cd prod/sam
./deploy.sh
```

### AWS Deployment (Terraform)
```bash
cd prod/terraform
terraform init
terraform apply
```

---

## File Structure

```
prod/
├── app/
│   ├── __init__.py          # App factory
│   ├── models.py            # SQLAlchemy models
│   ├── routes/
│   │   ├── admin.py         # Web UI routes
│   │   └── api.py           # REST API routes
│   ├── templates/           # HTML templates
│   ├── static/
│   │   ├── css/             # Stylesheets
│   │   ├── js/              # JavaScript (script.js)
│   │   └── templates/       # Excel upload templates
│   └── utils/
│       ├── parsers.py       # Name parsing utilities
│       └── upload_processor.py  # Excel processing
├── sam/                     # AWS SAM deployment
│   ├── template.yaml
│   └── lambda_entrypoint.py
├── terraform/               # Terraform IaC
│   └── main.tf
├── run.py                   # Entry point
└── create_templates.py      # Template generator
```

---

## Key Features

1. **RUEX ID Matching**: Automatic employee lookup using name pattern
2. **Batch Processing**: Bulk Excel uploads for all entity types
3. **Template Generation**: Automatic Excel template creation
4. **Archive System**: 2-month schedule retention, 1-month attendance
5. **Reward Program**: Points tracking with redemption workflow
6. **Admin Management**: UI for managing dropdown options
7. **Name Parsing**: Auto-detects "First Last" vs "Last, First" formats

---

## Known Limitations

1. Single admin user (admin/admin123) by default
2. No audit logging for user actions
3. No email notifications for leave requests
4. SQLite only (requires PostgreSQL for production)
5. File uploads limited to /tmp directory on Linux
