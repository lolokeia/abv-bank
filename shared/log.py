import threading
from datetime import datetime
from pathlib import Path
from shared import collibry

LOG_PATH: Path | str | None = None
_log_lock = threading.Lock()


def log_init(path=None):
    global LOG_PATH
    if path is not None:
        LOG_PATH = Path(path)
        # Автоматически создаем родительские папки, если их нет
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    else:
        LOG_PATH = None
    return LOG_PATH


def datetime_now():
    return datetime.now().strftime('%d.%m.%Y %H:%M:%S')


def time_now():
    return datetime.now().strftime('%H:%M:%S')


def _log(level, color, msg, fullcoltext=False, print_cmd=True, print_log=True):
    with _log_lock:
        if print_log and LOG_PATH:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(f"{datetime_now()} | [{level}] - {msg}\n")

        if print_cmd:
            if fullcoltext:
                print(f"{collibry.BRIGHT_BLACK}{time_now()}{collibry.RESET} | {color}[{level}] - {msg}{collibry.RESET}")
            else:
                print(f"{collibry.BRIGHT_BLACK}{time_now()}{collibry.RESET} | {color}[{level}]{collibry.RESET} - {msg}")



def error(msg): _log("ERROR", collibry.BOLD + collibry.RED, msg, fullcoltext=True)
def warn(msg):  _log("WARN", collibry.YELLOW, msg)
def info(msg, print_log=True):  _log("INFO", collibry.GREEN, msg, print_log=print_log)
def crit(msg):  _log("CRITICAL", collibry.BOLD + collibry.BG_RED, msg, fullcoltext=True)
def con(msg, print_log=True): _log("CONSOLE", collibry.BG_BRIGHT_BLACK, msg, print_log=print_log)
def cmd(msg): _log("CMD", collibry.BG_BRIGHT_BLACK, msg, print_cmd=False)

def req(msg): _log("REQUEST", collibry.ITALIC, msg)
def resp(msg): _log("RESPONSE", collibry.ITALIC, msg)

def debug(msg): _log("DEBUG", collibry.BG_BRIGHT_BLACK, msg)


logo_art = """
 █████╗ ██████╗ ██╗   ██╗    ██████╗  █████╗ ███╗   ██╗██╗  ██╗
██╔══██╗██╔══██╗██║   ██║    ██╔══██╗██╔══██╗████╗  ██║██║ ██╔╝
███████║██████╔╝██║   ██║    ██████╔╝███████║██╔██╗ ██║█████╔╝ 
██╔══██║██╔══██╗╚██╗ ██╔╝    ██╔══██╗██╔══██║██║╚██╗██║██╔═██╗ 
██║  ██║██████╔╝ ╚████╔╝     ██████╔╝██║  ██║██║ ╚████║██║  ██╗
╚═╝  ╚═╝╚═════╝   ╚═══╝      ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝
                    made by lolokeia\n"""


def logo(title="server started"):
    with _log_lock:
        if LOG_PATH:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write("=" * 23 + f" {title} at {datetime_now()} " + "=" * 22 + "\n\n")
        print(logo_art)


def clear():
    with _log_lock:
        if LOG_PATH:
            with open(LOG_PATH, "w", encoding="utf-8") as f:
                f.write("=" * 35 + " LOG CLEARED " + "=" * 36 + "\n\n")
    return LOG_PATH
