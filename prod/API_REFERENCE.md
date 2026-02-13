# opsdb API Reference

Base URL: `https://<api-id>.execute-api.<region>.amazonaws.com/api`

## Authentication

Most endpoints require no authentication for internal use. For external access, add API keys or IAM authentication.

---

## Employee Management

### List Employees
```
GET /api/employees
```
**Query Params:**
- `status` - Filter by status (Active/Inactive)
- `department` - Filter by department
- `shift` - Filter by shift
- `role` - Filter by role
- `tier` - Filter by tier
- `search` - Search in name/email
- `limit` - Results per page (default: 100, max: 1000)
- `offset` - Pagination offset

**Response:**
```json
{
  "total": 50,
  "limit": 100,
  "offset": 0,
  "data": [
    {
      "employee_id": 12345,
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "company_email": "john.doe@company.com",
      "department": "IT",
      "role": "Developer",
      "shift": "Day",
      "status": "Active",
      "tier": 2
    }
  ]
}
```

### Get Single Employee
```
GET /api/employees/{employee_id}
```

### Create Employee
```
POST /api/employees
```
**Body:**
```json
{
  "employee_id": 12345,
  "first_name": "John",
  "last_name": "Doe",
  "company_email": "john.doe@company.com",
  "batch": "2024-01",
  "supervisor": "Jane Smith",
  "manager": "Bob Johnson",
  "shift": "Day",
  "department": "IT",
  "role": "Developer",
  "hire_date": "2024-01-15",
  "tier": 2,
  "phase_1_date": "2024-01-15",
  "phase_2_date": "2024-02-15",
  "phase_3_date": "2024-03-15"
}
```

### Bulk Import Employees
```
POST /api/employees/batch?dry_run=false
```
**Body:** `multipart/form-data` with file field

### Update Employee
```
PUT /api/employees/{employee_id}
```

### Delete Employee
```
DELETE /api/employees/{employee_id}
```

### Search Employees
```
GET /api/employees/search?q={query}&limit=20
```

---

## Schedule Management

### List Schedules
```
GET /api/schedules?start_date=2024-01-01&end_date=2024-01-31
```

### Create Schedule
```
POST /api/schedules
```
**Body:**
```json
{
  "employee_id": 12345,
  "start_date": "2024-01-15",
  "stop_date": "2024-01-16",
  "start_time": "08:00:00",
  "stop_time": "17:00:00",
  "work_code": "REG"
}
```

### Schedule Swap/Cover
```
POST /api/schedule_changes
```
**Body:**
```json
{
  "employee_id": 12345,
  "replacement_id": 67890,
  "schedule_date": "2024-01-15",
  "change_type": "swap"
}
```

---

## Attendance Management

### List Attendances
```
GET /api/attendances?start_date=2024-01-01&end_date=2024-01-31
```

### Create Attendance
```
POST /api/attendances
```
**Body:**
```json
{
  "employee_id": 12345,
  "date": "2024-01-15",
  "check_in": "08:00:00",
  "check_out": "17:00:00",
  "exception_type": "OT",
  "notes": "Overtime for project"
}
```

### Daily Attendance Report
```
GET /api/attendances/daily-report?date=2024-01-15
```

---

## Leave Requests

### List Leave Requests
```
GET /api/leave_requests?status=Pending
```

### Create Leave Request
```
POST /api/leave_requests
```
**Body:**
```json
{
  "employee_id": 12345,
  "leave_type": "Vacation",
  "start_date": "2024-02-01",
  "end_date": "2024-02-05"
}
```

### Approve Leave
```
POST /api/leave_requests/{leave_id}/approve
```
**Body:**
```json
{
  "approved_by": 67890
}
```

### Reject Leave
```
POST /api/leave_requests/{leave_id}/reject
```

### Cancel Leave
```
DELETE /api/leave_requests/{leave_id}
```

---

## Exception Records

### List Exceptions
```
GET /api/exceptions?status=Pending
```

### Create Exception
```
POST /api/exceptions
```
**Body:**
```json
{
  "employee_id": 12345,
  "exception_type": "Training",
  "start_date": "2024-01-20",
  "end_date": "2024-01-22",
  "work_code": "TRAIN",
  "supervisor_override": "Jane Smith"
}
```

### Process Exception
```
POST /api/exceptions/{exception_id}/process
```

---

## Reward Management

### List Reward Reasons
```
GET /api/rewards/reasons
```

### Create Reward Reason
```
POST /api/rewards/reasons
```
**Body:**
```json
{
  "reason": "Employee of the Month",
  "points": 100,
  "is_active": true
}
```

### Award Points
```
POST /api/rewards/award
```
**Body:**
```json
{
  "employee_id": 12345,
  "reason_id": 1,
  "points": 50,
  "date_awarded": "2024-01-15",
  "notes": "Great performance on project"
}
```

### Bulk Award Points
```
POST /api/rewards/award/batch
```
**Body:** `multipart/form-data` with file field

### Employee Reward History
```
GET /api/rewards/employee/{employee_id}
```

### Total Points
```
GET /api/rewards/employee/{employee_id}/total
```

### List Redemptions
```
GET /api/rewards/redemptions
```

### Redeem Points
```
POST /api/rewards/redemptions
```
**Body:**
```json
{
  "employee_id": 12345,
  "points_redeemed": 50,
  "redemption_type": "Gift Card",
  "redemption_details": "$50 Amazon Gift Card",
  "is_approved": true
}
```

---

## Admin Options

### List Admin Options
```
GET /api/admin/options?category=leave_type
```

### Create Admin Option
```
POST /api/admin/options
```
**Body:**
```json
{
  "category": "leave_type",
  "value": "Bereavement"
}
```

### Update Admin Option
```
PUT /api/admin/options/{option_id}
```

---

## Reporting Endpoints

### Employees Report
```
GET /api/reports/employees
```

### Schedules Report
```
GET /api/reports/schedules
```

### Attendances Report
```
GET /api/reports/attendances
```

### Rewards Report
```
GET /api/reports/rewards
```

### Redemptions Report
```
GET /api/reports/redemptions
```

### Leave Requests Report
```
GET /api/reports/leave_requests
```

### Exceptions Report
```
GET /api/reports/exceptions
```

### Dashboard Summary
```
GET /api/reports/dashboard?date=2024-01-15
```

---

## Error Responses

```json
{
  "error": "Resource not found",
  "errors": ["employee_id must reference a valid active employee"]
}
```

**Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad request (validation error)
- `404` - Resource not found
- `409` - Conflict (duplicate)
- `500` - Server error
