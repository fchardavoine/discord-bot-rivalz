"""
Database initialization and setup for Discord bot
"""

import os
from flask import Flask
from models import db

def init_database():
    """Initialize the database with all tables"""
    try:
        # Create Flask app for database context
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 300,
            "pool_pre_ping": True,
        }
        
        # Initialize database
        db.init_app(app)
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Print table info
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"✅ Created {len(tables)} tables: {', '.join(tables)}")
            
        return True
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    if success:
        print("🎉 Database initialization completed!")
    else:
        print("💥 Database initialization failed!")