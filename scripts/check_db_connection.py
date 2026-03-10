import os
import sys
import time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Get URL from env or default
# WE MUST LOAD .ENV MANUALLY if not running via start_bot.ps1
try:
    with open(os.path.join(project_root, ".env"), "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#") and "=" in line:
                key, val = line.strip().split("=", 1)
                os.environ[key] = val
                print(f"Loaded {key} from .env")
except FileNotFoundError:
    print("No .env file found!")

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/zubera_bot")

print(f"\n--- Checking Connection to: {DATABASE_URL} ---")

try:
    # Use short timeout to fail fast
    engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5})
    
    print("Attempting to connect...")
    start_time = time.time()
    
    with engine.connect() as conn:
        print(f"Connection Successful! (Took {time.time() - start_time:.2f}s)")
        
        print("Checking tables...")
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in result]
        print(f"Found existing tables: {tables}")
        
except OperationalError as e:
    print(f"\n❌ CONNECTION FAILED: {e}")
    print("\nPossible Causes:")
    print("1. PostgreSQL server is not running.")
    print("2. Wrong username/password.")
    print("3. Database 'zubera_bot' does not exist (Did you run CREATE DATABASE?)")
    print("4. Firewall blocking port 5432.")
except Exception as e:
    print(f"\n❌ UNEXPECTED ERROR: {e}")
