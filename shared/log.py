from datetime import datetime
from config import LOG_PATH

def error(msg):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | [ERROR] - {msg}\n")
    print(f"{datetime.now()} | [ERROR] - {msg}\n")

def warn(msg):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | [WARN] - {msg}\n")
    print(f"{datetime.now()} | [WARN] - {msg}\n")

def info(msg):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | [INFO] - {msg}\n")
    print(f"{datetime.now()} | [INFO] - {msg}\n")


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