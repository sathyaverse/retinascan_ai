import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'retinascan.db')
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_active = 1 WHERE is_active = 0 OR is_active IS NULL")
        conn.commit()
        print(f"Successfully activated all inactive users in {db_path} (rows affected: {cursor.rowcount})")
        conn.close()
    except Exception as e:
        print(f"Error updating database: {e}")
else:
    print(f"Database not found at {db_path}")
