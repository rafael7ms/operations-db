import os
from datetime import timedelta


def get_database_uri():
    """Get database URI from environment or use SQLite for local development."""
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        return db_url

    # For local development, use SQLite
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, '..', '..', 'opsdb.db')
    return f'sqlite:///{db_path}'


class Config:
    """Base configuration class."""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'opsdb-default-secret-key-change-in-production'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Database
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }

    # Uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Schedule settings
    SCHEDULE_RETENTION_DAYS = 60  # Keep current schedules for 2 months
    ATTENDANCE_RETENTION_DAYS = 30  # Keep attendance for 1 month before archiving

    # Predefined options (default values, admin can modify via UI)
    DEFAULT_DROPDOWN_OPTIONS = {
        'leave_type': ['Vacation', 'Sick', 'Personal', 'Unplanned'],
        'work_code': ['Regular', 'Training', 'Nesting', 'Meeting', 'New Hire Training'],
        'exception_type': ['Absent', 'Late', 'Early Leave', 'New Hire'],
        'status': ['Active', 'Inactive', 'On Leave'],
        'change_type': ['Swap', 'Cover'],
        'exception_category': ['Training', 'Nesting', 'New Hire Training', 'Vacation', 'Swap', 'Cover'],
    }

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    FLASK_ENV = 'production'

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # Production-specific setup


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
