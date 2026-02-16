# Operations DB - API Documentation

## Base URL
```
http://127.0.0.1:5443/api
```

## Authentication
Most API endpoints require authentication. Use the `/login` endpoint first to obtain a session.

---

## Endpoints

### Health Check
```
GET /health
```
Returns health status.

---

## Employee Endpoints

### Get All Employees
```
GET /employees
```
**Query Parameters:**
- `status` - Filter by status (default: "Active")

**Response:**
```json
[
  {
    "employee_id": 41031748911,
    "first_name": "Heily",
    "last_name": "Melendez",
    "full_name": "Heily Melendez",
    "company_email": "heily.melendez@7managedservices.com",
    "department": "Customer Support",
    "role": "Associate",
    "shift": "Morning",
    "status": "Active"
  }
]
```

### Get Single Employee
```
GET /employees/<int:employee_id>
```
**Response:**
```json
{
  "employee_id": 41031748911,
  "first_name": "Heily",
  "last_name": "Melendez",
  "full_name": "Heily Melendez",
  "company_email": "heily.melendez@7managedservices.com",
  "batch": "2024-01",
  "supervisor": "Jane Smith",
  "manager": "Bob Johnson",
  "tier": 2,
  "shift": "Morning",
  "department": "Customer Support",
  "role": "Associate",
  "hire_date": "2024-01-15",
  "phase_1_date": "2024-02-15",
  "phase_2_date": "2024-03-15",
  "phase_3_date": "2024-04-15",
  "status": "Active",
  "attrition_date": null,
  "point_balance": 0
}
```

### Create Employee
```
POST /employees
Content-Type: application/json

{
  "employee_id": 41031748911,
  "first_name": "John",
  "last_name": "Doe",
  "company_email": "john.doe@7managedservices.com",
  "batch": "2024-01",
  "supervisor": "Jane Smith",
  "manager": "Bob Johnson",
  "shift": "Morning",
  "department": "Customer Support",
  "role": "Associate",
  "tier": 1
}
```

### Update Employee
```
PUT /employees/<int:employee_id>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "tier": 2,
  "status": "Active",
  "attrition_date": "2025-12-31"
}
```

### Delete Employee
```
DELETE /employees/<int:employee_id>
```

### Bulk Import Employees
```
POST /employees/batch
Content-Type: multipart/form-data

file: Excel file with columns:
  - Odoo ID (required)
  - First Name (required)
  - Last Name (required)
  - Batch (required)
  - Supervisor (required)
  - Manager (required)
  - Shift (required)
  - Department (required)
  - Role (required)
  - Hire Date (required)
  - Company Email (required)
  - Tier (optional)
  - Agent ID (optional)
  - BO User (optional)
  - Axonify (optional)
```

**Response:**
```json
{
  "message": "Bulk employee import completed",
  "success_count": 50,
  "error_count": 2,
  "errors": ["Row 15: Employee already exists", "Row 23: Missing required column"]
}
```

---

## Schedule Endpoints

### Get Schedules
```
GET /schedules
```
**Query Parameters:**
- `start_date` - Filter by start date (YYYY-MM-DD)
- `end_date` - Filter by end date (YYYY-MM-DD)
- `employee_id` - Filter by employee ID

### Create Schedule
```
POST /schedules
Content-Type: application/json

{
  "employee_id": 41031748911,
  "start_date": "2026-02-17",
  "start_time": "08:00",
  "stop_date": "2026-02-17",
  "stop_time": "17:00",
  "work_code": "REG"
}
```

### Bulk Import Schedules (with RUEX ID matching)
```
POST /schedules/batch
Content-Type: multipart/form-data

file: Excel file with columns:
  - Employee - ID (RUEX ID or Odoo ID) (required)
  - Date - Nominal Date (required)
  - Earliest - Start (required)
  - Latest - Stop (required)
  - Work - Code (required)

employee_file: (optional) Employee Excel file for RUEX ID mapping
```

**RUEX ID Format:** First letter of first name + last name (lowercase)
- Example: "John Smith" → `jsmith`
- Example: "Maria Garcia" → `mgarcia`

**Response:**
```json
{
  "message": "Bulk schedule import completed",
  "success_count": 100,
  "error_count": 3,
  "errors": ["Row 15: Could not find employee for RUEX ID abrown"]
}
```

---

## Attendance Endpoints

### Get Attendances
```
GET /attendances
```
**Query Parameters:**
- `start_date` - Filter by date (YYYY-MM-DD)
- `end_date` - Filter by date (YYYY-MM-DD)
- `employee_id` - Filter by employee ID

### Create Attendance
```
POST /attendances
Content-Type: application/json

{
  "employee_id": 41031748911,
  "date": "2026-02-17",
  "check_in": "08:00",
  "check_out": "17:00",
  "exception_type": "OT",
  "notes": "Overtime for project"
}
```

### Update Attendance
```
PUT /attendances/<int:employee_id>/<string:date>
Content-Type: application/json

{
  "check_out": "18:00",
  "exception_type": "OT",
  "notes": "Updated overtime notes"
}
```

### Bulk Import Attendances
```
POST /attendances/batch
Content-Type: multipart/form-data

file: Excel file with columns:
  - Employee - ID (Odoo ID) (required)
  - Date (required)
  - Check In (required)
  - Check Out (optional)
  - Exception (optional)
  - Notes (optional)
```

---

## Leave Request Endpoints

### Get Leave Requests
```
GET /leave_requests
```
**Query Parameters:**
- `status` - Filter by status (Pending/Approved/Rejected)
- `employee_id` - Filter by employee ID

### Create Leave Request
```
POST /leave_requests
Content-Type: application/json

{
  "employee_id": 41031748911,
  "leave_type": "Vacation",
  "start_date": "2026-03-01",
  "end_date": "2026-03-05",
  "status": "Pending"
}
```

### Approve Leave Request
```
POST /leave_requests/<int:leave_id>/approve
Content-Type: application/json

{
  "approved_by": 41000000001
}
```

---

## Exception Record Endpoints

### Get Exception Records
```
GET /exceptions
```
**Query Parameters:**
- `status` - Filter by status (Pending/Completed)
- `employee_id` - Filter by employee ID

### Create Exception Record
```
POST /exceptions
Content-Type: application/json

{
  "employee_id": 41031748911,
  "exception_type": "Training",
  "start_date": "2026-02-20",
  "end_date": "2026-02-22",
  "work_code": "TRAIN",
  "status": "Pending",
  "notes": "New hire training",
  "supervisor_override": "Jane Smith"
}
```

### Process Exception Record
```
POST /exceptions/<int:exception_id>/process
Content-Type: application/json

{
  "processed_by": 41000000001
}
```

### Bulk Import Exceptions
```
POST /exceptions/batch
Content-Type: multipart/form-data

file: Excel file with columns:
  - Employee - ID (Odoo ID) (required)
  - Exception Type (required)
  - Start Date (required)
  - End Date (required)
  - Work Code (optional)
  - Supervisor Override (optional)
  - Notes (optional)
```

---

## Admin Options Endpoints

### Get Admin Options
```
GET /admin/options
```
**Query Parameters:**
- `category` - Filter by category (department, role, shift, status, etc.)

### Create Admin Option
```
POST /admin/options
Content-Type: application/json

{
  "category": "department",
  "value": "Customer Support"
}
```

---

## Reward Endpoints

### Get Reward Reasons
```
GET /rewards/reasons
```
Returns list of active reward reasons with points.

### Get Employee Reward History
```
GET /rewards/employee/<int:employee_id>
```
Returns all rewards for an employee.

### Get Employee Point Balance
```
GET /rewards/employee/<int:employee_id>/balance
```
**Response:**
```json
{
  "employee_id": 41031748911,
  "employee_name": "Heily Melendez",
  "point_balance": 500
}
```

### Award Points
```
POST /rewards/award
Content-Type: application/json

{
  "employee_id": 41031748911,
  "reason_id": 1,
  "points": 50,
  "date_awarded": "2026-02-16",
  "notes": "Excellent performance",
  "awarded_by": 41000000001
}
```

### Bulk Award Points
```
POST /rewards/award/batch
Content-Type: multipart/form-data

file: Excel file with columns:
  - Employee - ID (Odoo ID) (required)
  - Reason ID (required)
  - Points (required)
  - Date Awarded (required)
  - Notes (optional)
```

### Redeem Points
```
POST /rewards/redemptions
Content-Type: application/json

{
  "employee_id": 41031748911,
  "points_redeemed": 100,
  "redemption_type": "Gift Card",
  "redemption_details": "Amazon $50 Gift Card",
  "notes": "Redeemed for gift card",
  "approved_by": 41000000001
}
```

**Response:**
```json
{
  "message": "Points redeemed successfully",
  "redemption_id": 1,
  "points_redeemed": 100,
  "remaining_balance": 400
}
```

---

## Error Responses

All errors return a JSON response with the error message:

```json
{
  "message": "Error message here"
}
```

Common status codes:
- `400` - Bad Request (invalid data)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error

---

## Example curl Commands

```bash
# Login
curl -X POST http://127.0.0.1:5443/login \
  -d "username=admin&password=admin123"

# Get employees
curl http://127.0.0.1:5443/api/employees

# Get single employee
curl http://127.0.0.1:5443/api/employees/41031748911

# Create employee
curl -X POST http://127.0.0.1:5443/api/employees \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": 41031748911,
    "first_name": "John",
    "last_name": "Doe",
    "company_email": "john.doe@7managedservices.com",
    "batch": "2024-01",
    "supervisor": "Jane Smith",
    "manager": "Bob Johnson",
    "shift": "Morning",
    "department": "Customer Support",
    "role": "Associate"
  }'

# Get point balance
curl http://127.0.0.1:5443/api/rewards/employee/41031748911/balance

# Award points
curl -X POST http://127.0.0.1:5443/api/rewards/award \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": 41031748911,
    "reason_id": 1,
    "points": 50,
    "date_awarded": "2026-02-16",
    "notes": "Great job!"
  }'
```
