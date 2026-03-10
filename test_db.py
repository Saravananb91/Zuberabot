import psycopg2
import sys

print("Attempting to connect to PostgreSQL...")
try:
    conn = psycopg2.connect("postgresql://localhost:5432/zubera_bot", connect_timeout=5)
    print("Successfully connected!")
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f"Failed to connect: {e}")
    sys.exit(1)
