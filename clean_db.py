import os
import sys

db_path = os.path.join(os.path.dirname(__file__), 'retinascan.db')
log_path = os.path.join(os.path.dirname(__file__), 'clean_db.log')

with open(log_path, 'w') as f:
    f.write("Starting cleanup...\n")
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            f.write(f"Successfully deleted {db_path}\n")
        except Exception as e:
            f.write(f"Error deleting database: {e}\n")
    else:
        f.write("retinascan.db does not exist\n")
