# Operations DB - Production Version

This folder contains a standalone production version of the Operations DB application.

## Structure

```
prod/
├── app/              # Flask application package
├── static/           # Static assets (CSS, JS, images)
├── templates/        # HTML templates
├── run.py            # Application entry point
├── init_db.py        # Database initialization script
├── requirements.txt  # Python dependencies
└── opsdb.db          # SQLite database (created by init_db.py)
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Initialize the database (first time only):
```bash
python init_db.py
```

2. Start the server:
```bash
python run.py
```

3. Access the application at: http://localhost:5443

## Default Credentials

- Admin: username `admin`, password `admin123`
- DB Admin: username `db_admin`, password `dbadmin123`

## Connection String

To connect another application to this database, use:

```
sqlite:///C:/path/to/prod/opsdb.db
```

Or in environment variable format:
```
DATABASE_URL=sqlite:///C:/path/to/prod/opsdb.db
```

## Notes

- This is a development server. For production deployment, use a proper WSGI server like Gunicorn or Waitress.
- The database is SQLite, suitable for single-instance deployment.
- Changes to the app code require a server restart.
