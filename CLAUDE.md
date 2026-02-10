# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an Operations Department database system for workforce scheduling and attendance management. The application is built with Flask and PostgreSQL, deployed on AWS.

## Architecture

### Database Schema

**Main Tables:**
- `employees` - Active employees with training phases (phase_1-3_date)
- `employees_history` - Archived inactive employees (no training phases)
- `schedules` - Current schedules (within 2-month retention)
- `schedules_history` - Archived schedules (>2 months)
- `attendances` - Check-ins + exceptions only (lean table)
- `attendances_history` - Monthly archived attendance records
- `leave_requests` - Vacation/sick leave requests
- `schedule_changes` - Swap/cover requests
- `admin_options` - Predefined dropdown options (managed by admin)
- `reward_reasons` - Reward point definitions
- `employee_rewards` - Points tracking
- `exceptions` - Batch exception records (Training, Nesting, New Hire Training, etc.)

**API Endpoints (`/api` prefix):**
- `/api/employees` - GET/POST/PUT/DELETE employee records
- `/api/schedules` - GET/POST schedule records
- `/api/attendances` - GET/POST attendance records
- `/api/leave_requests` - GET/POST leave requests + approve endpoint
- `/api/exceptions` - GET/POST exception records + process endpoint
- `/api/admin/options` - GET/POST admin dropdown options
- `/api/rewards/*` - Reward program endpoints

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost:5432/opsdb"
export SECRET_KEY="your-secret-key-here"

# Initialize database
python -c "from app import create_app, db; from app.database import init_db; app = create_app('development'); init_db(app)"

# Run application
python run.py
```

## Development

- **Flask App:** `app/` directory
- **Models:** `app/models.py`
- **Routes:** `app/routes/admin.py` (web UI), `app/routes/api.py` (REST API)
- **Forms:** `app/forms/` (WTForms)
- **Utils:** `app/utils/` (name parsing, cleanup, upload processing)
- **Templates:** `app/templates/`
- **Static:** `app/static/` (CSS, JS)

## Deployment on AWS

1. **Database:** PostgreSQL on AWS RDS
2. **Application:** Flask on AWS ECS or Elastic Beanstalk
3. **Storage:** S3 for uploaded files and backups
4. **Scheduled Tasks:** AWS Lambda for monthly cleanup (archive old schedules/attendances)

## Key Features

- **Dropdown Management:** Admin controls all predefined values via UI
- **Name Parsing:** Auto-detects "First Last" vs "Last, First" formats
- **Archive Process:** 2-month schedule retention, 1-month attendance retention
- **Exception Processing:** Batch upload for Training, Nesting, New Hire Training, Vacations, Swaps, Covers
- **Reward Program:** Points tracking with custom reasons

## Default Admin Credentials (after init)
- Username: `admin`
- Password: `admin123`
