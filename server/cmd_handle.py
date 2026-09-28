from tabulate import tabulate
from server import db, transactions, auth, tokens
from shared import log
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
import time

session = PromptSession()

def format_uptime(seconds):
    seconds = int(seconds)
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if days: parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def cmd_help(args, state):
    if len(args) < 1:
        print("Commands:")
        for name in sorted(COMMANDS):
            desc = DESC.get(name, "")
            print(f"  {name:<12} {desc}")
        return
    name = args[0].lower()
    if name not in COMMANDS:
        print(f"unknown command: {name}")
        return
    print(f"{name}: {DESC.get(name, 'no desc')}")



def cmd_show_table(args, state):
    if len(args) < 1:
        print("Usage: table users|tokens|transactions")
        return

    table = args[0].lower()
    if table == "users":
        tabu = db.table_get_users()
        print(tabulate(tabu, headers=["UUID", "login", "name", "balance", "Time created", "role"]))
    elif table == "tokens":
        tabu = db.table_get_tokens()
        print(tabulate(tabu, headers=["Token", "UUID", "Time created", "Expiration time"]))
    elif table == "transactions":
        tabu = db.table_get_tr()
        print(tabulate(tabu, headers=["ID", "UUID", "Type", "amount", "new balance", "desc", "time"]))
    else: print("table not found"); return



def cmd_exit(args, state):
    state["running"] = False



def cmd_token(args, state):
    if len(args) < 1:
            print("Usage: token delete <token>|delete_user <uuid>|nuke_all|get <uuid>|cleanup")
            return
    
    name = args[0].lower()
    if name == "delete":
        if len(args) < 2:
            print("please enter argument")
            return
        db.remove_token(args[1])

    elif name == "delete_user":
        if len(args) < 2:
            print("please enter argument")
            return
        db.remove_token_by_uuid(args[1])

    elif name == "nuke_all":
        usure = input("Are you sure? Yes/No: ")
        if usure.lower() == "yes":
            db.unsafe_remove_all_tokens()
            print("sucсessful")
        else: print("cancelled")

    elif name == "get":
        if len(args) < 2:
            print("please enter argument")
            return
        print(tabulate(db.get_tokens_by_uuid(args[1]), headers=["Token", "UUID", "Time created", "Expiration time"]))
    elif name == "cleanup":
        count = tokens.cleanup()
        msg = f"Deleted {count} expired tokens"
        print(msg)
        return msg


def cmd_user(args, state):
    usage = "Usage: user list|info <login>|delete <uuid>|create <login> <name> <pin>"
    if len(args) < 1:
        print(usage)
        return
    name = args[0].lower()

    if name == "list":
        cmd_show_table(["users"], state)
    elif name == "info":
        if len(args) < 2:
            print(usage)
            return
        user_uuid = db.get_user_by_login(args[1])
        if user_uuid:
            print(f"{args[1]} info:\n", tabulate([db.get_user(user_uuid)], headers=["UUID", "login", "name", "balance", "Time created", "role"]))
            print(f"\nactive tokens:",)
            cmd_token(["get", user_uuid], state)
            rows = db.tr_get_recent(user_uuid, 10)
            rows = [list(r) for r in rows]
            print(f"\nlast 10 transactions:")
            print(tabulate(rows, headers=["type", "amount", "balance_after", "desc", "time"]))
        else:
            print("user not found")
            return
    elif name == "delete":
        if not args[1]:
            print("please enter uuid")
            return
        usure = input("Are you sure? Yes/No: ")
        if usure.lower() == "yes":
            db.delete_user(args[1])
            print("sucсessful")
        else: print("cancelled")
    elif name == "create":
        if len(args) < 4:
            print(usage)
            return
        reg = auth.register(args[1], args[2], args[3])
        print(f"{reg.get("status")} - {reg.get("message")}")
        

def cmd_client(args, state):
    if len(args) < 1:
        print("Usage: client list|kick <addr>| kickall")
        return
    name = args[0].lower()
    if name == "list":
        clients = []
        for conn, addr in state["clients"].items():
            clients.append([addr[0], addr[1]])
            
        if clients:
            print(tabulate(clients, headers=["IP", "Port"]))
        else:
            print("No clients connected")
    elif name == "kick":
        if len(args) < 2:
            print("Usage: client list|kick <addr>| kickall")
            return
        address = args[1]
        if ":" not in address:
            print("Format: ip:port")
            return
        ip, port = address.split(":", 1)
        port = int(port)

        target = None
        with state["lock"]:
            for conn, addr in state["clients"].items():
                if addr[0] == ip and addr[1] == port:
                    target = conn
                    break

        if target is None:
            print(f"No client found: {ip}:{port}")
            return
        target.close()
        print(f"Kicked {ip}:{port}")

    elif name == "kickall":
        with state["lock"]:
            conns = list(state["clients"].keys())
            if not conns:
                print("No clients connected")
                return
            for conn in conns:
                try:
                    conn.close()
                except Exception:
                    pass
        print(f"Kicked {len(conns)} clients")
    


def cmd_state(args, state):
    uptime = time.monotonic() - state["start_time"]
    
    cmd_client(["list"], state)
        
    print("Server Uptime: ", format_uptime(uptime))
    print("Total requests count: ", state["requests_total"])


def cmd_tr(args, state):
    usage = "Usage: tr deposit <login> <amount>|withdraw <login> <amount>|payment <login> <amount>|set <login> <balance>|transfer <login-from> <login-to> <amount>"
    if len(args) < 2:
        print(usage)
        return
    name = args[0].lower()

    
    user_uuid = db.get_user_by_login(args[1])
    if not user_uuid:
        print(f"User with login {args[1]} not found")
        return

    if name == "deposit":
        if len(args) < 3:
            print(usage)
            return
        tr = transactions.deposit(user_uuid, args[2])
    elif name == "withdraw":
        if len(args) < 3:
            print(usage)
            return
        tr = transactions.withdraw(user_uuid, args[2])
    elif name == "payment":
        if len(args) >= 3:
            tr = transactions.payment(user_uuid, args[2])
        else:
            tr = transactions.payment(user_uuid)
    elif name == "transfer":
        if len(args) < 4:
                print(usage)
                return
        tr = transactions.transfer(user_uuid, args[2], args[3])

    elif name == "set":
        usure = input("Are you sure? Yes/No: ")
        try:
            new_balance = float(args[2])
        except ValueError:
            tr = {"status": "error", "message": f"amount must be a number"}
            print(f"{tr.get("status")} - {tr.get("message")}")
            return
        if usure.lower() == "yes":
            db.unsafe_set_balance_admin(user_uuid, new_balance)
            tr = {"status": "ok", "message": f"set balance for {args[1]} to {args[2]}"}
        else: tr = {"status": "error", "message": f"cancelled"}; print(f"{tr.get("status")} - {tr.get("message")}"); return
    else:
        print(f"transaction {args[0]} not found")
        return
    
    print(f"{tr.get("status")} - {tr.get("message")}")


def cmd_log(args, state):
    if len(args) < 1:
        print("Usage: log clear")
        return
    name = args[0].lower()
    
    if name == "clear":
        path = log.clear()
        print(f"Cleared {path}")

def cmd_restart(args, state):
    print("Restarting...")
    state["restart"] = True
    state["running"] = False
    state["sock"].close()



COMMANDS = {
    "help": cmd_help,
    "table": cmd_show_table,
    "exit": cmd_exit,
    "token": cmd_token,
    "user": cmd_user,
    "state": cmd_state,
    "client": cmd_client,
    "restart": cmd_restart,
    "tr": cmd_tr,
    "log": cmd_log,
}

DESC = {
    "help": "show this screen",
    "state": "server uptime, requests, clients",
    "table": "show table (users|tokens|transactions)",
    "token": "manage tokens (get|delete|delete_user|nuke_all)",
    "user": "manage users",
    "client": "manage clients",
    "log": "log clear",
    "db": "database info",
    "restart": "restart server",
    "exit": "stop server",
}


def handle(state):
    with patch_stdout(raw=True):
        while state["running"]:
            try:
                command = session.prompt("abv-bank > ")
            except (EOFError, KeyboardInterrupt): print("To stop server, type exit"); continue
            
            if not command: continue

            part = command.strip().split()
            name = part[0].lower()
            args = part[1:]
            cmd = COMMANDS.get(name)
            if cmd is None:
                print(f"Unknown command: {name}")
                continue
            cmd(args, state)

        