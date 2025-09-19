"""
Database application context manager for Discord bot
Provides Flask app context for SQLAlchemy operations
"""

import os
from flask import Flask
from models import db

# Create Flask app instance for database context
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database with app
db.init_app(app)

def init_database():
    """Initialize database tables"""
    try:
        with app.app_context():
            db.create_all()
            
            # Get table info
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"✅ Database tables created successfully!")
            print(f"✅ Created {len(tables)} tables: {', '.join(tables)}")
            
        return True
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False

def get_db_session():
    """Get database session with proper context"""
    return db.session

def with_db_context(func):
    """Decorator to ensure database operations have Flask app context"""
    def wrapper(*args, **kwargs):
        with app.app_context():
            return func(*args, **kwargs)
    return wrapper

# Push application context for the lifetime of the bot process
# This ensures all database operations have proper context
app_context = app.app_context()
app_context.push()

print("🗄️ Database app context established for bot lifetime")