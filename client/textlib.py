import os

RED = "\033[91m"
YELLOW = "\x1B[33m"
GREEN = "\033[92m"
RESET = "\033[0m"

def clear():
    print("\033[2J\033[H", end="")

def show_balance(bal):
    print(f"Баланс: {round(bal, 2)}Р")

def line():
    print("="*50)

def red(msg):
    print(f"{RED} {msg} {RESET}")

def green(msg):
    print(f"{GREEN} {msg} {RESET}")