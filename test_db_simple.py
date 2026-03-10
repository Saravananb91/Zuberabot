"""Simple test to debug the SQLAlchemy issue."""

import os
os.environ["DATABASE_URL"] = "postgresql://postgres:zubera123@localhost:5432/zubera_bot"

try:
    print("Importing database models...")
    from zuberabot.database.models import Base, User, ChatSession, UserWorkspace
    print("✅ Models imported successfully!")
    
    print("\nImporting database manager...")
    from zuberabot.database.postgres import DatabaseManager
    print("✅ Database manager imported successfully!")
    
    print("\nInitializing database...")
    db = DatabaseManager()
    print("✅ Database initialized!")
    
    print("\nCreating tables...")
    db.create_tables()
    print("✅ Tables created!")
    
    print("\n🎉 All imports and initializations successful!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
