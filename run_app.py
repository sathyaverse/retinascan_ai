import subprocess
import os
import sys
import time

log_path = os.path.join(os.path.dirname(__file__), 'app_run.log')
python_exe = os.path.join(os.path.dirname(__file__), 'venv', 'Scripts', 'python.exe')
app_py = os.path.join(os.path.dirname(__file__), 'app.py')

# Clean old log
if os.path.exists(log_path):
    try:
        os.remove(log_path)
    except:
        pass

env = os.environ.copy()
env['PYTHONUNBUFFERED'] = '1'

with open(log_path, 'w', encoding='utf-8') as f:
    f.write(f"Starting app.py via wrapper with PIPE using {python_exe}...\n")
    f.flush()
    try:
        process = subprocess.Popen(
            [python_exe, '-u', app_py],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=os.path.dirname(__file__),
            env=env,
            text=True
        )
        f.write(f"Started process with PID: {process.pid}\n")
        f.flush()
        
        # Read output in real-time
        start_time = time.time()
        # Set stdout to non-blocking or just read line by line
        # Since readline blocks, we can run a loop checking if process is still running
        while True:
            # Check if process has output
            # On Windows, we can use select or just let readline block, but wait,
            # if we do a blocking readline, it will block until a newline.
            # If the process terminates, readline returns empty string.
            line = process.stdout.readline()
            if line:
                f.write(f"[App Output] {line}")
                f.flush()
            else:
                # No output and process terminated
                ret = process.poll()
                if ret is not None:
                    f.write(f"Process exited with code: {ret}\n")
                    f.flush()
                    break
                else:
                    time.sleep(0.1)
            
            # Timeout check to prevent wrapping process from running forever
            if time.time() - start_time > 15:
                f.write("Timeout: Process is still running in background. Disconnecting monitor.\n")
                f.flush()
                break
                
    except Exception as e:
        f.write(f"Failed to start process: {e}\n")
        f.flush()
