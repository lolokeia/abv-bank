import socket, threading, time
import customtkinter as ctk
import tabulate as tabu
from client import logic, session as se, locale as lo
from shared import codes
import client_config as config


lo.json_init()

def connect_to_server(host=config.HOST, port=config.PORT):
    sock = se.state["sock"]
    se.state['conn_tries'] = 0
    while True:
        print(f"Connection try: {se.state['conn_tries']}")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            return sock
        except (TimeoutError, ConnectionRefusedError):
            se.state['conn_tries'] += 1
            change_screen("connect")

app = ctk.CTk()

def clear_screen():
    for widget in app.winfo_children():
        widget.destroy()

def change_screen(screen):
    app.after(0, _change_screen_gui, screen)

def _change_screen_gui(screen):
    clear_screen()
    if screen in SCREENS:
        SCREENS[screen]()
    else:
        se.state['last_error'] = "client.screen_not_found"
        SCREENS["error"]()


def show_error_screen():
    error_label = ctk.CTkLabel(app, text=f"{lo.loc('client.error')}: {lo.loc(se.state['last_error'])}", font=("Arial", 24))
    error_label.pack(pady=30)

def show_connect_screen():
    connect_label = ctk.CTkLabel(app, text=lo.loc("client.connecting"), font=("Arial", 24))
    connect_label.place(relx=0.5, rely=0.4, anchor="center")

    progressbar = ctk.CTkProgressBar(app, orientation="horizontal", determinate_speed=0.20)
    progressbar.set(0)
    progressbar.start()
    progressbar.place(relx=0.5, rely=0.5, anchor="center")

    tries_label = ctk.CTkLabel(app, text=f"{lo.loc("client.tries")}{se.state['conn_tries']}", font=("Arial", 14))
    tries_label.place(relx=0.5, rely=0.6, anchor="center")

    if se.state['conn_tries'] > 10:
        long_label = ctk.CTkLabel(app, text=lo.loc("client.long_connection"), font=("Arial", 10))
        long_label.place(relx=0.5, rely=0.8, anchor="center")



def show_login_screen(if_login_err=False):
    
    err = se.state.pop("login_error", None)
    
    main_label = ctk.CTkLabel(app, text=lo.loc("login.main"), font=("Arial", 24))
    main_label.place(relx=0.5, rely=0.2, anchor="center")

    login_entry = ctk.CTkEntry(app, placeholder_text=lo.loc("login.login_entry"))
    login_entry.place(relx=0.5, rely=0.40, anchor="center")

    pin_entry = ctk.CTkEntry(app, placeholder_text=lo.loc("login.pin_entry"), show="*")
    pin_entry.place(relx=0.5, rely=0.50, anchor="center")

    error_label = ctk.CTkLabel(app, text=lo.loc(err) if err else "", font=("Arial", 12), text_color="red")
    error_label.place(relx=0.5, rely=0.6, anchor="center")

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
    "connect": show_connect_screen,
    "login": show_login_screen,
}
def client_main():
    try:
        change_screen("connect")
        if not se.state['sock']:
            sock = connect_to_server()
            se.state['sock'] = sock
        if not se.state['token']:
            change_screen("login")

        
        time.sleep(0.1)
    except Exception as e:
        se.state['last_error'] = e
        change_screen("error")



threading.Thread(target=client_main, daemon=True).start()

app.title(lo.loc("title"))
app.geometry("300x300")
app.mainloop()