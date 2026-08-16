import os
import sys

# Kill all python processes except this one
mypid = os.getpid()
try:
    # Use taskkill to kill python.exe processes. It's okay if this process is terminated as well at the end.
    os.system("taskkill /F /IM python.exe")
except Exception as e:
    print(f"Error: {e}")
