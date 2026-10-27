import os
import sys
import subprocess
import time

time.sleep(0)

base_dir = os.path.dirname(os.path.abspath(__file__))
client_script = os.path.join(base_dir, "client_main.py")

if not os.path.exists(client_script):
    print(f"file {client_script} not found!")
    sys.exit(1)


if sys.platform == 'win32':

    subprocess.Popen(['python.exe', client_script])

elif sys.platform.startswith('linux') or sys.platform == 'darwin':
    subprocess.Popen(
        [sys.executable, client_script],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )