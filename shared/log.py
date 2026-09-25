from datetime import datetime
from config import LOG_PATH


RED = "\033[91m"
YELLOW = "\x1B[33m"
GREEN = "\033[92m"
RESET = "\033[0m"


def error(msg):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | [ERROR] - {msg}\n")
    print(f"{datetime.now()} | {RED} [ERROR] {RESET} - {msg}\n")

def warn(msg):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | [WARN] - {msg}\n")
    print(f"{datetime.now()} | {YELLOW} [WARN] {RESET} - {msg}\n")

def info(msg):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | [INFO] - {msg}\n")
    print(f"{datetime.now()} | {GREEN} [INFO] {RESET} - {msg}\n")


logo_art = """
 █████╗ ██████╗ ██╗   ██╗    ██████╗  █████╗ ███╗   ██╗██╗  ██╗
██╔══██╗██╔══██╗██║   ██║    ██╔══██╗██╔══██╗████╗  ██║██║ ██╔╝
███████║██████╔╝██║   ██║    ██████╔╝███████║██╔██╗ ██║█████╔╝ 
██╔══██║██╔══██╗╚██╗ ██╔╝    ██╔══██╗██╔══██║██║╚██╗██║██╔═██╗ 
██║  ██║██████╔╝ ╚████╔╝     ██████╔╝██║  ██║██║ ╚████║██║  ██╗
╚═╝  ╚═╝╚═════╝   ╚═══╝      ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝"""

def logo():
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"="*80)
        f.write(f"\n")
    print(logo_art)