import socket, threading, time
import customtkinter as ctk
import tabulate as tabu
from client import locales as lo, logic, session as se
from shared import codes
import client_config as config


lo.json_init()


def close():
    if se.state['sock']:
        se.state["sock"].close()
    exit(0)


def watchdog():
    time.sleep(10)
    while True:
        print(se.state['sock'])
        ping = logic.ping()
        if ping == False:
            se.state['sock'] = connect_to_server()
        else:
            continue
        time.sleep(5)


def connect_to_server(host=config.HOST, port=config.PORT):
    app.after_idle(show_connect)
    se.state['conn_tries'] = 1
    update_connect()
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            app.after_idle(hide_connect)
            se.state['conn'] == True
            return sock
        except (TimeoutError, ConnectionRefusedError, OSError) as e:
            print(f"conn: {e}")
            se.state['conn_tries'] += 1
            print(f"Connection try: {se.state['conn_tries']}")
            update_connect()
        time.sleep(5)
            
            

app = ctk.CTk()

def clear_screen():
    for widget in app.winfo_children():
        if widget == conn_overlay: #or widget == abv_label:
            continue
        try:
            widget.destroy()
        except Exception: pass

def change_screen(screen):
    app.after(0, _change_screen_gui, screen)

def _change_screen_gui(screen):
    clear_screen()
    if screen in SCREENS:
        SCREENS[screen]()
    else:
        se.state['last_error'] = "client.screen_not_found"
        SCREENS["error"]()



conn_overlay = ctk.CTkFrame(app, fg_color="#1F1E1E")

connect_label = ctk.CTkLabel(conn_overlay, text=lo.loc("client.connecting"), font=("Arial", 24))
connect_label.place(relx=0.5, rely=0.4, anchor="center")

progressbar = ctk.CTkProgressBar(conn_overlay, orientation="horizontal", indeterminate_speed=0.5)
progressbar.set(0)
progressbar.start()
progressbar.place(relx=0.5, rely=0.5, anchor="center")

tries_label = ctk.CTkLabel(conn_overlay, text=f"{lo.loc('client.tries')}{se.state['conn_tries']}", font=("Arial", 14))
tries_label.place(relx=0.5, rely=0.6, anchor="center")

long_label = ctk.CTkLabel(conn_overlay, text=lo.loc(""), font=("Arial", 10))
long_label.place(relx=0.5, rely=0.8, anchor="center")

exit_btn = ctk.CTkButton(conn_overlay, text=lo.loc("client.exit"), font=("Arial", 10), command=exit)

def update_connect():
    tries_label.configure(text=f"{lo.loc('client.tries')}{se.state['conn_tries']}")

    if se.state['conn_tries'] >= 10:
        long_label.configure(text=lo.loc("client.long_connection"))
        exit_btn.place(relx=0.5, rely=0.9, anchor="center")
    else:
        long_label.configure(text=lo.loc(""))
        exit_btn.place_forget()

def show_connect():
    conn_overlay.place(relwidth=1, relheight=1, x=0, y=0)
    conn_overlay.lift()

def hide_connect():
    conn_overlay.place_forget()

def show_error_screen():
    error_label = ctk.CTkLabel(app, text=f"{lo.loc('client.error')}: {lo.loc(se.state['last_error'])}", font=("Arial", 14))
    error_label.place(relx=0.5, rely=0.45, anchor="center")

    exit_btn = ctk.CTkButton(app, text=lo.loc("client.exit"), font=("Arial", 14), command=close, fg_color="#5C4E4E")
    exit_btn.place(relx=0.5, rely=0.55, anchor="center")


def show_login_screen():
    
    err = se.state.pop("login_error", None)
    
    main_label = ctk.CTkLabel(app, text=lo.loc("login.main"), font=("Arial", 24))
    main_label.place(relx=0.5, rely=0.2, anchor="center")

    login_entry = ctk.CTkEntry(app, placeholder_text=lo.loc("login.login_entry"))
    login_entry.place(relx=0.5, rely=0.40, anchor="center")

    pin_entry = ctk.CTkEntry(app, placeholder_text=lo.loc("login.pin_entry"), show="*")
    pin_entry.place(relx=0.5, rely=0.50, anchor="center")

    error_label = ctk.CTkLabel(app, text=lo.loc(err) if err else "", font=("Arial", 12), text_color="red")
    error_label.place(relx=0.5, rely=0.6, anchor="center")

    exit_btn = ctk.CTkButton(app, text=lo.loc("client.exit"), font=("Arial", 14), command=close, fg_color="#5C4E4E")
    exit_btn.place(relx=0.85, rely=0.05, anchor="center")

    def on_click():
            login = login_entry.get().strip()
            pin = pin_entry.get().strip()

            def worker():
                resp = logic.login(login, pin)
                if resp.get("status") == "ok":
                    se.state["login"] = login
                    se.state["pin"] = pin
                    se.state["token"] = resp['data'].get("token")
                    app.after(0, lambda: change_screen("main"))
                else:
                    se.state["login_error"] = resp.get("code", "server.error")
                    app.after(0, lambda: change_screen("login"))

            threading.Thread(target=worker, daemon=True).start()

    login_button = ctk.CTkButton(app, text=lo.loc("login.button"), font=("Arial", 16), command=on_click)
    login_button.place(relx=0.5, rely=0.7, anchor="center")

SCREENS = {
    "error": show_error_screen,
    "login": show_login_screen,
}
def client_main():
    try:
        if not se.state['sock']:
            se.state['conn'] = True
            se.state['sock'] = connect_to_server()
        if not se.state['token']:
            change_screen("login")
        time.sleep(0.1)

    except Exception as e:
        se.state['last_error'] = e
        change_screen("error")



threading.Thread(target=client_main, daemon=True).start()
threading.Thread(target=watchdog, daemon=True).start()

app.title(lo.loc("title"))
app.geometry("400x400")
app.mainloop()