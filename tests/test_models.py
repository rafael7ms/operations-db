"""Tests for opsdb application models."""
import pytest
from datetime import date
from app import db
from app.models import (
    User, DBUser, Employee, AdminOptions,
    RewardReason, EmployeeReward
)


@pytest.fixture(scope='module')
def app():
    """Create application for testing."""
    from app import create_app

    app = create_app('development')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope='module')
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope='module')
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def session(app):
    """Create new database session for a test with rollback.

    Uses db.session directly which is a scoped_session.
    The function scope ensures fresh session per test.
    """
    # Clear any existing session state
    db.session.remove()

    # Begin a transaction
    db.session.begin()

    yield db.session

    # Rollback the transaction
    db.session.rollback()
    # Remove session to clean up
    db.session.remove()


@pytest.fixture(scope='function')
def user_fixture(session):
    """Create a test user."""
    user = User(
        username='testuser',
        email='test@example.com',
        is_admin=False
    )
    user.set_password('testpassword123')
    session.add(user)
    session.commit()
    return user


@pytest.fixture(scope='function')
def admin_user_fixture(session):
    """Create a test admin user."""
    user = User(
        username='adminuser',
        email='admin@example.com',
        is_admin=True
    )
    user.set_password('adminpassword123')
    session.add(user)
    session.commit()
    return user


@pytest.fixture(scope='function')
def dbuser_fixture(session):
    """Create a test DB user."""
    dbuser = DBUser(
        username='dbuser',
        email='dbuser@example.com',
        is_superuser=False,
        is_active=True
    )
    dbuser.set_password('dbpassword123')
    session.add(dbuser)
    session.commit()
    return dbuser


@pytest.fixture(scope='function')
def super_dbuser_fixture(session):
    """Create a test super DB user."""
    dbuser = DBUser(
        username='superdbuser',
        email='superdbuser@example.com',
        is_superuser=True,
        is_active=True
    )
    dbuser.set_password('superdbpassword123')
    session.add(dbuser)
    session.commit()
    return dbuser


@pytest.fixture(scope='function')
def employee_fixture(session):
    """Create a test employee."""
    employee = Employee(
        employee_id=1001,
        first_name='John',
        last_name='Doe',
        full_name='John Doe',
        company_email='john.doe@company.com',
        access_card='AC123456',
        token_serial='TS789012',
        building_card='BC345678',
        batch='2024-01',
        agent_id='AG001',
        bo_user='BO001',
        axonify='AX001',
        supervisor='Jane Supervisor',
        manager='Bob Manager',
        tier=2,
        shift='Morning',
        department='IT Support',
        role='Agent',
        hire_date=date(2024, 1, 15),
        status='Active'
    )
    session.add(employee)
    session.commit()
    return employee


@pytest.fixture(scope='function')
def admin_options_fixture(session):
    """Create test admin options."""
    options = [
        AdminOptions(category='leave_type', value='Vacation'),
        AdminOptions(category='leave_type', value='Sick'),
        AdminOptions(category='leave_type', value='Personal'),
        AdminOptions(category='work_code', value='Regular'),
        AdminOptions(category='work_code', value='Training'),
        AdminOptions(category='exception_type', value='Absent'),
        AdminOptions(category='exception_type', value='Late'),
        AdminOptions(category='change_type', value='Swap'),
        AdminOptions(category='change_type', value='Cover'),
    ]
    session.add_all(options)
    session.commit()
    return options


@pytest.fixture(scope='function')
def reward_reason_fixture(session):
    """Create test reward reasons."""
    reasons = [
        RewardReason(reason='Excellent Performance', points=100, is_active=True),
        RewardReason(reason='Team Player', points=50, is_active=True),
        RewardReason(reason='Innovation Award', points=75, is_active=True),
        RewardReason(reason='Attendance', points=25, is_active=True),
    ]
    session.add_all(reasons)
    session.commit()
    return reasons


class TestUserModel:
    """Tests for User model."""

    def test_user_creation(self, session):
        """Test user creation."""
        user = User(
            username='user1',
            email='user1@example.com',
            is_admin=False
        )
        user.set_password('password123')
        session.add(user)
        session.commit()

        assert user.id is not None
        assert user.username == 'user1'
        assert user.email == 'user1@example.com'
        assert user.is_admin is False
        assert user.password_hash is not None
        assert user.password_hash != 'password123'

    def test_user_password_hashing(self, session):
        """Test password hashing is working correctly."""
        user = User(username='passwordtest', email='pass@example.com')
        password = 'mysecurepassword'
        user.set_password(password)

        # Verify password hash is not the plain text
        assert user.password_hash != password
        # Verify check_password works
        assert user.check_password(password) is True
        assert user.check_password('wrongpassword') is False

    def test_user_repr(self, session):
        """Test user string representation."""
        user = User(username='repruser', email='repr@example.com')
        user.set_password('password')
        session.add(user)
        session.commit()

        assert repr(user) == '<User repruser>'

    def test_admin_user_creation(self, session):
        """Test admin user creation."""
        admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True
        )
        admin.set_password('adminpass')
        session.add(admin)
        session.commit()

        assert admin.is_admin is True

    def test_user_unique_constraints(self, session):
        """Test that user email and username must be unique."""
        user1 = User(
            username='uniqueuser1',
            email='unique1@example.com',
            is_admin=False
        )
        user1.set_password('password1')
        session.add(user1)
        session.commit()

        # Test duplicate email
        user2 = User(
            username='uniqueuser2',
            email='unique1@example.com',
            is_admin=False
        )
        user2.set_password('password2')
        session.add(user2)

        with pytest.raises(Exception):
            session.flush()

        # Clean up
        session.rollback()

        # Test duplicate username
        user3 = User(
            username='uniqueuser1',
            email='unique3@example.com',
            is_admin=False
        )
        user3.set_password('password3')
        session.add(user3)

        with pytest.raises(Exception):
            session.flush()


class TestDBUserModel:
    """Tests for DBUser model."""

    def test_dbuser_creation(self, session):
        """Test DB user creation."""
        dbuser = DBUser(
            username='dbuser1',
            email='dbuser1@example.com',
            is_superuser=False,
            is_active=True,
            notes='Test DB user'
        )
        dbuser.set_password('dbpassword123')
        session.add(dbuser)
        session.commit()

        assert dbuser.id is not None
        assert dbuser.username == 'dbuser1'
        assert dbuser.email == 'dbuser1@example.com'
        assert dbuser.is_superuser is False
        assert dbuser.is_active is True
        assert dbuser.notes == 'Test DB user'
        assert dbuser.password_hash is not None
        assert dbuser.password_hash != 'dbpassword123'

    def test_dbuser_password_hashing(self, session):
        """Test DB user password hashing."""
        dbuser = DBUser(username='dbpasswordtest', email='dbpass@example.com')
        password = 'dbsecurepassword'
        dbuser.set_password(password)

        assert dbuser.password_hash != password
        assert dbuser.check_password(password) is True
        assert dbuser.check_password('wrongpassword') is False

    def test_dbuser_repr(self, session):
        """Test DB user string representation."""
        dbuser = DBUser(username='dbrepruser', email='dbrepr@example.com')
        dbuser.set_password('password')
        session.add(dbuser)
        session.commit()

        assert repr(dbuser) == '<DBUser dbrepruser>'

    def test_dbuser_superuser(self, session):
        """Test DB user superuser flag."""
        superuser = DBUser(
            username='dbsuper',
            email='dbsuper@example.com',
            is_superuser=True,
            is_active=True
        )
        superuser.set_password('superpass')
        session.add(superuser)
        session.commit()

        assert superuser.is_superuser is True

    def test_dbuser_inactive(self, session):
        """Test DB user inactive flag."""
        inactive_user = DBUser(
            username='dbinactive',
            email='dbinactive@example.com',
            is_superuser=False,
            is_active=False
        )
        inactive_user.set_password('password')
        session.add(inactive_user)
        session.commit()

        assert inactive_user.is_active is False

    def test_dbuser_unique_constraints(self, session):
        """Test DB user unique constraints."""
        user1 = DBUser(
            username='unique_dbuser',
            email='unique_db@example.com',
            is_superuser=False
        )
        user1.set_password('password1')
        session.add(user1)
        session.commit()

        # Test duplicate username
        user2 = DBUser(
            username='unique_dbuser',
            email='unique2@example.com',
            is_superuser=False
        )
        user2.set_password('password2')

        with pytest.raises(Exception):
            session.add(user2)
            session.commit()

        # Test duplicate email
        user3 = DBUser(
            username='unique_dbuser3',
            email='unique_db@example.com',
            is_superuser=False
        )
        user3.set_password('password3')

        with pytest.raises(Exception):
            session.add(user3)
            session.commit()


class TestEmployeeModel:
    """Tests for Employee model."""

    def test_employee_creation(self, session):
        """Test employee creation."""
        employee = Employee(
            employee_id=2001,
            first_name='Alice',
            last_name='Smith',
            full_name='Alice Smith',
            company_email='alice.smith@company.com',
            batch='2024-02',
            supervisor='Bob Supervisor',
            manager='Charlie Manager',
            shift='Afternoon',
            department='Sales',
            role='Sales Agent',
            hire_date=date(2024, 2, 1)
        )
        session.add(employee)
        session.commit()

        assert employee.employee_id == 2001
        assert employee.first_name == 'Alice'
        assert employee.last_name == 'Smith'
        assert employee.full_name == 'Alice Smith'
        assert employee.company_email == 'alice.smith@company.com'
        assert employee.batch == '2024-02'
        assert employee.status == 'Active'  # Default value

    def test_employee_optional_fields(self, session):
        """Test employee with optional fields."""
        employee = Employee(
            employee_id=2002,
            first_name='Bob',
            last_name='Jones',
            full_name='Bob Jones',
            company_email='bob.jones@company.com',
            access_card='AC999999',
            token_serial='TS111111',
            building_card='BC222222',
            batch='2024-03',
            agent_id='AG002',
            bo_user='BO002',
            axonify='AX002',
            supervisor='Jane Supervisor',
            manager='John Manager',
            tier=3,
            shift='Night',
            department='Finance',
            role='Senior Agent',
            hire_date=date(2024, 3, 1),
            phase_1_date=date(2024, 3, 15),
            phase_2_date=date(2024, 6, 15),
            phase_3_date=date(2024, 9, 15),
            status='Active'
        )
        session.add(employee)
        session.commit()

        assert employee.access_card == 'AC999999'
        assert employee.token_serial == 'TS111111'
        assert employee.building_card == 'BC222222'
        assert employee.tier == 3
        assert employee.phase_1_date == date(2024, 3, 15)

    def test_employee_repr(self, session):
        """Test employee string representation."""
        employee = Employee(
            employee_id=2003,
            first_name='Test',
            last_name='Employee',
            full_name='Test Employee',
            company_email='test.employee@company.com',
            batch='2024-01',
            supervisor='Supervisor',
            manager='Manager',
            shift='Morning',
            department='IT',
            role='Agent',
            hire_date=date(2024, 1, 1)
        )
        session.add(employee)
        session.commit()

        assert repr(employee) == '<Employee 2003: Test Employee>'

    def test_employee_attrition(self, session):
        """Test employee attrition tracking."""
        employee = Employee(
            employee_id=2004,
            first_name='Former',
            last_name='Employee',
            full_name='Former Employee',
            company_email='former.employee@company.com',
            batch='2024-01',
            supervisor='Supervisor',
            manager='Manager',
            shift='Morning',
            department='IT',
            role='Agent',
            hire_date=date(2024, 1, 1),
            status='Inactive',
            attrition_date=date(2024, 12, 31)
        )
        session.add(employee)
        session.commit()

        assert employee.status == 'Inactive'
        assert employee.attrition_date == date(2024, 12, 31)


class TestAdminOptionsModel:
    """Tests for AdminOptions model."""

    def test_admin_options_creation(self, session):
        """Test admin options creation."""
        option = AdminOptions(
            category='leave_type',
            value='Vacation',
            is_active=True
        )
        session.add(option)
        session.commit()

        assert option.option_id is not None
        assert option.category == 'leave_type'
        assert option.value == 'Vacation'
        assert option.is_active is True

    def test_admin_options_repr(self, session):
        """Test admin options string representation."""
        option = AdminOptions(
            category='work_code',
            value='Training'
        )
        session.add(option)
        session.commit()

        assert repr(option) == '<AdminOptions work_code: Training>'

    def test_admin_options_unique_constraint(self, session):
        """Test admin options unique constraint on category + value."""
        option1 = AdminOptions(
            category='leave_type',
            value='Sick'
        )
        session.add(option1)
        session.commit()

        # Try to create duplicate
        option2 = AdminOptions(
            category='leave_type',
            value='Sick'
        )

        with pytest.raises(Exception):
            session.add(option2)
            session.commit()

    def test_admin_options_inactive(self, session):
        """Test inactive admin options."""
        inactive_option = AdminOptions(
            category='leave_type',
            value='OldOption',
            is_active=False
        )
        session.add(inactive_option)
        session.commit()

        assert inactive_option.is_active is False


class TestRewardReasonModel:
    """Tests for RewardReason model."""

    def test_reward_reason_creation(self, session):
        """Test reward reason creation."""
        reason = RewardReason(
            reason='Customer Satisfaction',
            points=100,
            is_active=True
        )
        session.add(reason)
        session.commit()

        assert reason.reason_id is not None
        assert reason.reason == 'Customer Satisfaction'
        assert reason.points == 100
        assert reason.is_active is True

    def test_reward_reason_repr(self, session):
        """Test reward reason string representation."""
        reason = RewardReason(
            reason='Teamwork',
            points=50
        )
        session.add(reason)
        session.commit()

        assert repr(reason) == '<RewardReason Teamwork: 50 pts>'

    def test_reward_reason_unique(self, session):
        """Test reward reason unique constraint."""
        reason1 = RewardReason(
            reason='Innovation',
            points=75
        )
        session.add(reason1)
        session.commit()

        reason2 = RewardReason(
            reason='Innovation',
            points=100
        )

        with pytest.raises(Exception):
            session.add(reason2)
            session.commit()

    def test_reward_reason_inactive(self, session):
        """Test inactive reward reason."""
        inactive_reason = RewardReason(
            reason='OldReward',
            points=25,
            is_active=False
        )
        session.add(inactive_reason)
        session.commit()

        assert inactive_reason.is_active is False


class TestEmployeeRewardModel:
    """Tests for EmployeeReward model."""

    def test_employee_reward_creation(self, session):
        """Test employee reward creation."""
        employee = Employee(
            employee_id=3001,
            first_name='Reward',
            last_name='Recipient',
            full_name='Reward Recipient',
            company_email='reward@company.com',
            batch='2024-01',
            supervisor='Supervisor',
            manager='Manager',
            shift='Morning',
            department='IT',
            role='Agent',
            hire_date=date(2024, 1, 1)
        )
        reason = RewardReason(
            reason='Excellent Work',
            points=100,
            is_active=True
        )
        session.add(employee)
        session.add(reason)
        session.commit()

        reward = EmployeeReward(
            employee_id=employee.employee_id,
            reason_id=reason.reason_id,
            points=100,
            date_awarded=date(2024, 6, 15),
            notes='Excellent customer feedback'
        )
        session.add(reward)
        session.commit()

        assert reward.reward_id is not None
        assert reward.employee_id == 3001
        assert reward.reason_id == reason.reason_id
        assert reward.points == 100
        assert reward.date_awarded == date(2024, 6, 15)
        assert reward.notes == 'Excellent customer feedback'

    def test_employee_reward_repr(self, session):
        """Test employee reward string representation."""
        employee = Employee(
            employee_id=3002,
            first_name='Test',
            last_name='Reward',
            full_name='Test Reward',
            company_email='testreward@company.com',
            batch='2024-01',
            supervisor='Supervisor',
            manager='Manager',
            shift='Morning',
            department='IT',
            role='Agent',
            hire_date=date(2024, 1, 1)
        )
        reason = RewardReason(
            reason='Test Reward',
            points=50
        )
        session.add(employee)
        session.add(reason)
        session.commit()

        reward = EmployeeReward(
            employee_id=employee.employee_id,
            reason_id=reason.reason_id,
            points=50,
            date_awarded=date(2024, 6, 15)
        )
        session.add(reward)
        session.commit()

        assert repr(reward) == f'<EmployeeReward {reward.reward_id}: {employee.employee_id} - 50 pts>'

    def test_employee_reward_relationships(self, session):
        """Test employee reward relationships."""
        employee = Employee(
            employee_id=3003,
            first_name='Rel',
            last_name='Test',
            full_name='Rel Test',
            company_email='reltest@company.com',
            batch='2024-01',
            supervisor='Supervisor',
            manager='Manager',
            shift='Morning',
            department='IT',
            role='Agent',
            hire_date=date(2024, 1, 1)
        )
        reason = RewardReason(
            reason='Relationship Test',
            points=75
        )
        session.add(employee)
        session.add(reason)
        session.commit()

        reward = EmployeeReward(
            employee_id=employee.employee_id,
            reason_id=reason.reason_id,
            points=75,
            date_awarded=date(2024, 6, 15)
        )
        session.add(reward)
        session.commit()

        # Test reward reason relationship
        assert reward.reward_reason is not None
        assert reward.reward_reason.reason == 'Relationship Test'

        # Test employee rewards relationship
        assert len(employee.rewards_earned.all()) == 1
        assert employee.rewards_earned.first() == reward

    def test_employee_reward_awarded_by(self, session):
        """Test employee reward awarded_by relationship."""
        employee = Employee(
            employee_id=3004,
            first_name='Rcv',
            last_name='Test',
            full_name='Rcv Test',
            company_email='rcvtest@company.com',
            batch='2024-01',
            supervisor='Supervisor',
            manager='Manager',
            shift='Morning',
            department='IT',
            role='Agent',
            hire_date=date(2024, 1, 1)
        )
        awarder = Employee(
            employee_id=3005,
            first_name='Awd',
            last_name='Test',
            full_name='Awd Test',
            company_email='awdtest@company.com',
            batch='2024-01',
            supervisor='Supervisor',
            manager='Manager',
            shift='Morning',
            department='IT',
            role='Supervisor',
            hire_date=date(2024, 1, 1)
        )
        reason = RewardReason(
            reason='Awarded By Test',
            points=100
        )
        session.add(employee)
        session.add(awarder)
        session.add(reason)
        session.commit()

        reward = EmployeeReward(
            employee_id=employee.employee_id,
            reason_id=reason.reason_id,
            points=100,
            date_awarded=date(2024, 6, 15),
            awarded_by=awarder.employee_id
        )
        session.add(reward)
        session.commit()

        assert reward.awarded_by_user is not None
        assert reward.awarded_by_user.employee_id == 3005
