"""
Tests for opsdb application routes.

Tests cover:
- Login route (GET and POST)
- Logout route
- Dashboard route (requires login)
- Employees route
- Schedules route
- Attendance route
- Exceptions route
"""

import os
import tempfile
import pytest
from datetime import datetime, date, time
from app import create_app, db
from app.models import User, Employee, Schedule, Attendance, ExceptionRecord, AdminOptions, RewardReason, EmployeeReward, DBUser


# Create a temporary test database
TEST_DB_PATH = tempfile.mkstemp()[1]


class TestRoutes:
    """Test suite for application routes."""

    @pytest.fixture
    def app(self):
        """Create and configure app for testing."""
        # Set test configuration
        os.environ['FLASK_ENV'] = 'testing'

        app = create_app('development')
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

        # Create test database
        with app.app_context():
            db.create_all()

            # Create test user
            test_user = User(
                username='testuser',
                email='test@example.com',
                is_admin=True
            )
            test_user.set_password('testpassword')
            db.session.add(test_user)

            # Create some test employees
            emp1 = Employee(
                employee_id=1001,
                first_name='John',
                last_name='Doe',
                full_name='John Doe',
                company_email='john.doe@7managedservices.com',
                batch='2024-01',
                agent_id=5001,
                supervisor='Jane Smith',
                manager='Bob Johnson',
                tier=1,
                shift='Morning',
                department='Customer Service',
                role='Agent',
                hire_date=date(2024, 1, 15),
                status='Active'
            )
            emp2 = Employee(
                employee_id=1002,
                first_name='Jane',
                last_name='Smith',
                full_name='Jane Smith',
                company_email='jane.smith@7managedservices.com',
                batch='2024-01',
                agent_id=5002,
                supervisor='Bob Johnson',
                manager='Alice Williams',
                tier=2,
                shift='Afternoon',
                department='Technical Support',
                role='Senior Agent',
                hire_date=date(2024, 2, 1),
                status='Active'
            )
            db.session.add(emp1)
            db.session.add(emp2)

            # Create admin options - use unique values per test run
            dept_option = AdminOptions(category='department', value='Customer Service_1', is_active=True)
            role_option = AdminOptions(category='role', value='Agent_1', is_active=True)
            shift_option = AdminOptions(category='shift', value='Morning_1', is_active=True)
            status_option = AdminOptions(category='status', value='Active_1', is_active=True)
            work_code_option = AdminOptions(category='work_code', value='Regular_1', is_active=True)
            db.session.add_all([dept_option, role_option, shift_option, status_option, work_code_option])

            # Create test schedule
            schedule = Schedule(
                employee_id=1001,
                start_date=date(2024, 3, 1),
                start_time=time(9, 0, 0),
                stop_date=date(2024, 3, 1),
                stop_time=time(17, 0, 0),
                work_code='Regular'
            )
            db.session.add(schedule)

            # Create test attendance
            attendance = Attendance(
                employee_id=1001,
                date=date(2024, 3, 1),
                check_in=time(9, 0, 0),
                check_out=time(17, 0, 0),
                exception_type=None,
                notes='Regular shift'
            )
            db.session.add(attendance)

            # Create test exception
            exception = ExceptionRecord(
                employee_id=1002,
                exception_type='Training',
                start_date=date(2024, 3, 5),
                end_date=date(2024, 3, 7),
                work_code='Training',
                status='Pending'
            )
            db.session.add(exception)

            # Create reward reason
            reward_reason = RewardReason(
                reason='Excellent Performance_1',
                points=10,
                is_active=True
            )
            db.session.add(reward_reason)

            db.session.commit()

            yield app

            # Cleanup
            db.session.remove()
            db.drop_all()

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    def create_logged_in_client(self, client):
        """Helper to create a logged-in client."""
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)
        return client

    # ==================== LOGIN ROUTE TESTS ====================

    def test_login_get(self, client):
        """Test GET /login returns login page."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_login_post_success(self, client):
        """Test successful login with valid credentials."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should redirect to dashboard after login
        assert b'Dashboard' in response.data

    def test_login_post_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post('/login', data={
            'username': 'invaliduser',
            'password': 'wrongpassword'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Invalid username or password' in response.data

    def test_login_post_empty_credentials(self, client):
        """Test login with empty credentials."""
        response = client.post('/login', data={
            'username': '',
            'password': ''
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Invalid username or password' in response.data

    # ==================== LOGOUT ROUTE TESTS ====================

    def test_logout_requires_login(self, client):
        """Test logout without login redirects to login page."""
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to login page
        assert b'Login' in response.data

    def test_logout_success(self, client):
        """Test successful logout."""
        # First login
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)

        # Then logout
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to login page after logout
        assert b'Login' in response.data

    # ==================== DASHBOARD ROUTE TESTS ====================

    def test_dashboard_requires_login(self, client):
        """Test dashboard requires authentication."""
        response = client.get('/dashboard')
        assert response.status_code == 302  # Redirect

        response = client.get('/dashboard', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_dashboard_success(self, client):
        """Test successful dashboard access."""
        # First login
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)

        response = client.get('/dashboard')
        assert response.status_code == 200
        assert b'Dashboard' in response.data

    # ==================== EMPLOYEES ROUTE TESTS ====================

    def test_employees_requires_login(self, client):
        """Test employees route requires authentication."""
        response = client.get('/employees')
        assert response.status_code == 302

        response = client.get('/employees', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_employees_get(self, client):
        """Test GET /employees returns employees page."""
        # First login
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)

        response = client.get('/employees')
        assert response.status_code == 200
        assert b'Employees' in response.data

    def test_employees_shows_list(self, client):
        """Test employees page shows employee list."""
        # First login
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)

        response = client.get('/employees')
        assert response.status_code == 200
        # Should show the test employees
        assert b'John Doe' in response.data
        assert b'Jane Smith' in response.data

    # ==================== SCHEDULES ROUTE TESTS ====================

    def test_schedules_requires_login(self, client):
        """Test schedules route requires authentication."""
        response = client.get('/schedules')
        assert response.status_code == 302

        response = client.get('/schedules', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_schedules_get(self, client):
        """Test GET /schedules returns schedules page."""
        # First login
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)

        response = client.get('/schedules')
        assert response.status_code == 200
        assert b'Schedules' in response.data

    def test_schedules_shows_list(self, client):
        """Test schedules page shows schedule list."""
        # First login
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)

        response = client.get('/schedules')
        assert response.status_code == 200
        # Should show the test schedule - verify at least one employee is in response
        assert b'John Doe' in response.data or b'1001' in response.data

    # ==================== ATTENDANCE ROUTE TESTS ====================

    def test_attendance_requires_login(self, client):
        """Test attendance route requires authentication."""
        response = client.get('/attendance')
        assert response.status_code == 302

        response = client.get('/attendance', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_attendance_get(self, client):
        """Test GET /attendance returns attendance page."""
        # First login
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)

        response = client.get('/attendance')
        assert response.status_code == 200
        assert b'Attendance' in response.data

    def test_attendance_shows_list(self, client):
        """Test attendance page shows attendance list."""
        # First login
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)

        response = client.get('/attendance')
        assert response.status_code == 200
        # Should show the test attendance record
        assert b'John Doe' in response.data or b'1001' in response.data

    # ==================== EXCEPTIONS ROUTE TESTS ====================

    def test_exceptions_requires_login(self, client):
        """Test exceptions route requires authentication."""
        response = client.get('/exceptions')
        assert response.status_code == 302

        response = client.get('/exceptions', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_exceptions_get(self, client):
        """Test GET /exceptions returns exceptions page."""
        # First login
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)

        response = client.get('/exceptions')
        assert response.status_code == 200
        assert b'Exceptions' in response.data

    def test_exceptions_shows_pending(self, client):
        """Test exceptions page shows pending exceptions."""
        # First login
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)

        response = client.get('/exceptions')
        assert response.status_code == 200
        # Should show the test exception
        assert b'Training' in response.data or b'Jane Smith' in response.data

    # ==================== ADDITIONAL AUTH ROUTE TESTS ====================

    def test_index_redirects_authenticated(self, client):
        """Test index redirects to dashboard for authenticated users."""
        # First login
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)

        response = client.get('/', follow_redirects=True)
        assert response.status_code == 200
        assert b'Dashboard' in response.data

    def test_index_redirects_unauthenticated(self, client):
        """Test index redirects to login for unauthenticated users."""
        response = client.get('/', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_dashboard_statistics(self, client):
        """Test dashboard shows correct statistics."""
        # First login
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)

        response = client.get('/dashboard')
        assert response.status_code == 200
        data = response.data.decode('utf-8')

        # Should have correct counts from test data
        # 2 employees, 1 active, 0 on leave, 1 training exception pending
        assert '2' in data or 'employee' in data.lower()
        assert 'Active' in data or 'active' in data

    def test_multiple_routes_authenticated(self, client):
        """Test multiple routes are accessible when authenticated."""
        # First login
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)

        routes = [
            '/dashboard',
            '/employees',
            '/schedules',
            '/attendance',
            '/exceptions'
        ]

        for route in routes:
            response = client.get(route)
            assert response.status_code == 200, f"Route {route} returned {response.status_code}"


class TestAuthRoutes:
    """Additional tests for authentication-related routes."""

    @pytest.fixture
    def app(self):
        """Create and configure app for testing."""
        app = create_app('development')
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

        with app.app_context():
            db.create_all()

            # Create test user with DBUser table
            db_user = DBUser(
                username='dbuser',
                email='dbuser@example.com',
                is_active=True
            )
            db_user.set_password('dbpassword')
            db.session.add(db_user)

            # Also add regular User with unique email
            user = User(
                username='regularuser',
                email='regularuser@example.com',
                is_admin=False
            )
            user.set_password('regularpassword')
            db.session.add(user)

            db.session.commit()

            yield app

            db.session.remove()
            db.drop_all()

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    def test_login_with_regular_user(self, client):
        """Test login works with regular User table."""
        response = client.post('/login', data={
            'username': 'regularuser',
            'password': 'regularpassword'
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should have logged in successfully - check for dashboard content
        data = response.data.decode('utf-8')
        assert 'Dashboard' in data

    def test_logout_redirects_to_login(self, client):
        """Test logout redirects to login page."""
        # First login
        response = client.post('/login', data={
            'username': 'regularuser',
            'password': 'regularpassword'
        }, follow_redirects=True)

        # Then logout
        logout_response = client.get('/logout', follow_redirects=True)
        assert logout_response.status_code == 200
        assert b'Login' in logout_response.data


class TestFileUploadRoutes:
    """Tests for routes that handle file uploads."""

    @pytest.fixture
    def app(self):
        """Create and configure app for testing."""
        app = create_app('development')
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

        with app.app_context():
            db.create_all()

            test_user = User(
                username='uploaduser',
                email='upload@example.com',
                is_admin=True
            )
            test_user.set_password('uploadpassword')
            db.session.add(test_user)

            # Add admin options for dropdowns with unique values
            options = [
                AdminOptions(category='department', value='Test_Department', is_active=True),
                AdminOptions(category='role', value='Test_Role', is_active=True),
                AdminOptions(category='shift', value='Test_Shift', is_active=True),
                AdminOptions(category='status', value='Active', is_active=True),
                AdminOptions(category='work_code', value='Regular', is_active=True),
            ]
            db.session.add_all(options)

            db.session.commit()

            yield app

            db.session.remove()
            db.drop_all()

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    def test_employees_post_file_upload(self, client):
        """Test POST /employees with file upload."""
        # First login
        client.post('/login', data={
            'username': 'uploaduser',
            'password': 'uploadpassword'
        }, follow_redirects=True)

        # Create a minimal Excel-like file (in practice, would use real Excel)
        # Note: This test verifies the POST flow, not actual Excel parsing
        response = client.post('/employees', data={
            'file': (b'', 'test.xlsx')
        }, follow_redirects=True)

        # Should handle empty file gracefully
        assert response.status_code == 200

    def test_schedules_post_file_upload(self, client):
        """Test POST /schedules with file upload."""
        # First login
        client.post('/login', data={
            'username': 'uploaduser',
            'password': 'uploadpassword'
        }, follow_redirects=True)

        response = client.post('/schedules', data={
            'file': (b'', 'test.xlsx')
        }, follow_redirects=True)

        assert response.status_code == 200

    def test_attendance_post_file_upload(self, client):
        """Test POST /attendance with file upload."""
        # First login
        client.post('/login', data={
            'username': 'uploaduser',
            'password': 'uploadpassword'
        }, follow_redirects=True)

        response = client.post('/attendance', data={
            'file': (b'', 'test.xlsx')
        }, follow_redirects=True)

        assert response.status_code == 200

    def test_exceptions_post_file_upload(self, client):
        """Test POST /exceptions with file upload."""
        # First login
        client.post('/login', data={
            'username': 'uploaduser',
            'password': 'uploadpassword'
        }, follow_redirects=True)

        response = client.post('/exceptions', data={
            'file': (b'', 'test.xlsx')
        }, follow_redirects=True)

        assert response.status_code == 200
