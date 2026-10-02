from datetime import datetime
from config import LOG_PATH
from shared import collibry


def datetime_now():
    return datetime.now().strftime('%d.%m.%Y %H:%M:%S')

def time_now():
    return datetime.now().strftime('%H:%M:%S')

def _log(level, color, msg, fullcoltext=False):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{datetime_now()} | [{level}] - {msg}\n")
    
    if fullcoltext:
        print(f"{collibry.BRIGHT_BLACK}{time_now()}{collibry.RESET} | {color}[{level}] - {msg}{collibry.RESET}")
    else:
        print(f"{collibry.BRIGHT_BLACK}{time_now()}{collibry.RESET} | {color}[{level}]{collibry.RESET} - {msg}")

def error(msg): _log("ERROR", collibry.BOLD + collibry.RED, msg, True)
def warn(msg):  _log("WARN", collibry.YELLOW, msg)
def info(msg):  _log("INFO", collibry.GREEN, msg)
def crit(msg):  _log("CRITICAL", collibry.BOLD + collibry.BG_RED, msg, True)


logo_art = """
 █████╗ ██████╗ ██╗   ██╗    ██████╗  █████╗ ███╗   ██╗██╗  ██╗
██╔══██╗██╔══██╗██║   ██║    ██╔══██╗██╔══██╗████╗  ██║██║ ██╔╝
███████║██████╔╝██║   ██║    ██████╔╝███████║██╔██╗ ██║█████╔╝ 
██╔══██║██╔══██╗╚██╗ ██╔╝    ██╔══██╗██╔══██║██║╚██╗██║██╔═██╗ 
██║  ██║██████╔╝ ╚████╔╝     ██████╔╝██║  ██║██║ ╚████║██║  ██╗
╚═╝  ╚═╝╚═════╝   ╚═══╝      ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝
                    made by lolokeia\n"""

def logo():
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"="*23 + f"server started at {datetime_now()}" + f"="*22 + "\n")
        f.write(f"\n")
    print(logo_art)

def clear():
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write("="*35 + "LOG CLEARED" + "="*36 + "\n")
        f.write(f"\n")
        pass

    return LOG_PATH