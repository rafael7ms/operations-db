from app import db
from app.models import User, AdminOptions


def init_db(app):
    """Initialize the database with default values."""
    with app.app_context():
        # Create all tables
        db.create_all()

        # Add default admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@opsdb.local',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)

        db.session.commit()
        print('Database initialized successfully!')


def seed_default_data(app):
    """Seed the database with default values."""
    with app.app_context():
        # Add default dropdown options
        from app.models import AdminOptions
        from app.config import config
        default_config = config['default']

        for category, values in default_config.DEFAULT_DROPDOWN_OPTIONS.items():
            for value in values:
                existing = AdminOptions.query.filter_by(
                    category=category, value=value
                ).first()
                if not existing:
                    option = AdminOptions(
                        category=category,
                        value=value,
                        is_active=True
                    )
                    db.session.add(option)

        # Add reward reasons
        from app.models import RewardReason
        default_reasons = [
            ('Customer of the Month', 50),
            ('Quality Check Excellence', 30),
            ('Team Player', 25),
            ('Attendance Perfect', 20),
            ('Speed Leader', 15),
        ]

        for reason, points in default_reasons:
            existing = RewardReason.query.filter_by(reason=reason).first()
            if not existing:
                reward_reason = RewardReason(
                    reason=reason,
                    points=points,
                    is_active=True
                )
                db.session.add(reward_reason)

        db.session.commit()
        print('Default data seeded successfully!')
