import socket, threading, time, random
import customtkinter as ctk
import tabulate as tabu
from client import locales as lo, logic, session as se
from shared import codes
import client_config as config
import pyperclip
from tkinter import font
import ctktooltip
from PIL import Image, ImageSequence

ICON_FONT = (("Segoe MDL2 Assets", "Segoe UI Symbol", "Arial"), 20)

lo.json_init()

def close():
    if se.state['sock']:
        se.state["sock"].close()
    exit(0)

def logout():
    logic.logout()
    change_screen('main')

def get_accounts():
    get_accounts_tries=0
    while get_accounts_tries <= 5:
        accounts = logic.get_accounts()
        if not accounts:
            return False
        if accounts.get('status') == 'ok':
            if accounts['data'].get('accounts') == {}:
                se.state['accounts'] = accounts['data'].get('accounts')
                return False
            se.state['accounts'] = accounts['data'].get('accounts')
            get_accounts_tries = 0
            return True
        else:
            get_accounts_tries += 1
        time.sleep(0.5)

    if get_accounts_tries >= 5:
        app.after_idle(hide_loading)
        return False
    
def cvrt_mul(amount):
    amount = float(amount)
    amount = amount * 100
    amount = int(amount)
    return amount

def cvrt_div(amount):
    amount = int(amount)
    amount = amount / 100
    return amount

def watchdog():
    while True:
        if se.state['conn'] == True:
            time.sleep(config.WATCHDOG_TIMEOUT)
            continue
        # print(se.state['sock'])
        ping = logic.ping()
        # print(ping)
        if ping == False:
            se.state['sock'] = connect_to_server()
            time.sleep(config.WATCHDOG_TIMEOUT)
        else:
            time.sleep(config.WATCHDOG_TIMEOUT)
            continue


def connect_to_server(host=config.HOST, port=config.PORT):
    se.state['conn'] = True
    app.after_idle(show_connect)
    se.state['conn_tries'] = 1
    app.after_idle(update_connect)
    while se.state['conn'] == True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            app.after_idle(hide_connect)
            se.state['conn'] = False
            return sock
        except (TimeoutError, ConnectionRefusedError, OSError) as e:
            print(f"conn: {e}")
            se.state['conn_tries'] += 1
            print(f"Connection try: {se.state['conn_tries']}")
            app.after_idle(update_connect)
            time.sleep(1)
            continue
            
def card_build(parent, acc_num, acc_name, acc_currency, is_frozen, acc_bal):
    def random_color(min, max):
        n = 40
        r = random.randint(min, max)
        g = random.randint(min, max)
        b = random.randint(min, max)
        value = f'#{r:02x}{g:02x}{b:02x}'
        border = f'#{r-n:02x}{g-n:02x}{b-n:02x}'
        return value, border
    
    color, border = random_color(70, 170)
    card = ctk.CTkFrame(parent, width=350, height=100, border_width=5, fg_color=color, border_color=border)
    
    card.pack_propagate(False) 

    card.pack()


    def onclick(event=None):
            se.state['current_acc'] = [acc_num, acc_name, acc_currency, acc_bal, is_frozen]
            card.after_idle(lambda: change_screen('account'))
            return
    
    name_label = ctk.CTkLabel(card, text=f'{acc_name}', font=('arial_black', 16))
    name_label.place(relx=0.03, rely=0.2, anchor='w')

    bal_label = ctk.CTkLabel(card, text=f'{cvrt_div(acc_bal)} {acc_currency}', font=('arial_black', 28))
    bal_label.place(relx=0.03, rely=0.5, anchor='w')

    num_label = ctk.CTkLabel(card, text=f'{lo.loc('acc.acc')}{acc_num}', font=('arial_black', 16), text_color="#E6E6E6")
    num_label.place(relx=0.03, rely=0.8, anchor='w')

    card.bind("<Button-1>", onclick)
    name_label.bind("<Button-1>", onclick)
    bal_label.bind("<Button-1>", onclick)
    num_label.bind("<Button-1>", onclick)

    card.configure(cursor="hand2")
    name_label.configure(cursor="hand2")
    bal_label.configure(cursor="hand2")
    num_label.configure(cursor="hand2")


    


def prompt(prompts, redir):

    combo = ("acc_from", "acc_to")

    top = ctk.CTkToplevel(app)
    top.title(lo.loc("client.enter_data"))
    top.geometry("300x" + str(100 + len(prompts) * 50))
    top.attributes("-topmost", True)
    top.grab_set()
    entries = {}

    for i, field in enumerate(prompts):

        label = lo.loc(f"prompt.{field}")


        if field in combo:
            widget = ctk.CTkComboBox(top, values=se.state('accounts'))
            widget.set(label)
        else: 
            widget = ctk.CTkEntry(top, placeholder_text=label)
            
        widget.grid(row=i, column=1, padx=10, pady=10)
        
        entries[field] = widget

    def _onclick():
        values = []

        for field in prompts:
            val = entries[field].get().strip()

            if field == 'amount':
                try:
                    val = cvrt_mul(val)
                except ValueError:
                    se.state['last_error'] = 'amount.not_digit'
                    app.after_idle(lambda: change_screen('error'))
                    return
            
            values.append(val)


        def worker():
            try:
                resp = getattr(logic, redir)(*values)

                if resp['status'] == "error":
                    se.state['last_error'] = resp.get('code')
                    app.after_idle(lambda: change_screen('error'))
                else: app.after_idle(lambda: change_screen('main'))
            except Exception as e:
                se.state['last_error'] = str(e)
                app.after_idle(lambda: change_screen('error'))

        threading.Thread(target=worker, daemon=True).start()
        top.destroy()
        return
        
    submit_btn = ctk.CTkButton(top, text=lo.loc(f"accounts.{redir}"), command=_onclick)
    submit_btn.grid(row=len(prompts), column=0, columnspan=2, pady=15)

    error_lbl = ctk.CTkLabel(top, text="")
    error_lbl.grid(row=len(prompts)+1, column=0, columnspan=2)

app = ctk.CTk()

def clear_screen():
    for widget in app.winfo_children():
        if widget == conn_overlay or widget == loading_overlay:
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

def btn_exit():
    return ctk.CTkButton(conn_overlay, text='\uE711', font=ICON_FONT, command=close, fg_color="transparent", width=40, height=40)






def play(idx=0):
    if not conn_overlay.winfo_exists():
        return
    gif_lbl.configure(image=frames[idx])
    conn_overlay.after(40, lambda: play((idx + 1) % len(frames)))

conn_overlay = ctk.CTkFrame(app, fg_color="#1F1E1E")

connect_label = ctk.CTkLabel(conn_overlay, text=lo.loc("client.connecting"), font=("Arial", 24))
connect_label.place(relx=0.5, rely=0.3, anchor="center")

frames = [ctk.CTkImage(f.copy(), f.copy(), size=(64, 64)) for f in ImageSequence.Iterator(Image.open("loading.gif"))]

gif_lbl = ctk.CTkLabel(conn_overlay, image=frames[0], text="")
gif_lbl.place(relx=0.5, rely=0.5, anchor="center")

play()
# progressbar = ctk.CTkProgressBar(conn_overlay, orientation="horizontal", indeterminate_speed=0.5)
# progressbar.set(0)
# progressbar.start()
# progressbar.place(relx=0.5, rely=0.5, anchor="center")

tries_label = ctk.CTkLabel(conn_overlay, text=f"{lo.loc('client.tries')}{se.state['conn_tries']}", font=("Arial", 14))
tries_label.place(relx=0.5, rely=0.7, anchor="center")

long_label = ctk.CTkLabel(conn_overlay, text=lo.loc(""), font=("Arial", 10))
long_label.place(relx=0.5, rely=0.9, anchor="center")

exit_btn = btn_exit()

def update_connect():
    if not conn_overlay.winfo_exists() or not tries_label.winfo_exists():
        return
    tries_label.configure(text=f"{lo.loc('client.tries')}{se.state['conn_tries']}")
    conn_overlay.lift()
    if se.state['conn_tries'] >= 10:
        long_label.configure(text=lo.loc("client.long_connection"))
        exit_btn.place(relx=0.5, rely=0.8, anchor="center")
    else:
        long_label.configure(text=lo.loc(""))
        exit_btn.place_forget()

def show_connect():
    conn_overlay.place(relwidth=1, relheight=1, x=0, y=0)
    conn_overlay.lift()

def hide_connect():
    conn_overlay.place_forget()

loading_overlay = ctk.CTkFrame(app, fg_color="#1F1E1E")

loading = ctk.CTkLabel(loading_overlay, text=lo.loc("client.loading"), font=("Arial", 20))
loading.place(relx=0.5, rely=0.5, anchor="center")


def show_loading():
    loading_overlay.place(relwidth=1, relheight=1, x=0, y=0)
    loading_overlay.lift()

def hide_loading():
    loading_overlay.place_forget()

def show_error_screen():
    error_label = ctk.CTkLabel(app, text=f"{lo.loc('client.error')}: {lo.loc(se.state['last_error'])}", font=("Arial", 14))
    error_label.place(relx=0.5, rely=0.45, anchor="center")

    exit_btn = btn_exit()
    exit_btn.place(relx=0.5, rely=0.55, anchor="center")
    
    if se.state['retry_btn']:
        target = se.state.get("retry_btn")
        retry_btn = ctk.CTkButton(app, text=lo.loc("client.retry"), font=("Arial", 14), command=lambda: change_screen(target), fg_color="#5C4E4E")
        se.state['retry_btn'] = None
        retry_btn.place(relx=0.5, rely=0.75, anchor="center")

    if se.state['token']:
        menu_btn = ctk.CTkButton(app, text=lo.loc("client.menu"), font=("Arial", 14), command=lambda: change_screen('main'), fg_color="#5C4E4E")
        menu_btn.place(relx=0.5, rely=0.65, anchor="center")


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

    exit_btn = btn_exit()
    exit_btn.place(relx=0.85, rely=0.05, anchor="center")

    def on_click():
            login = login_entry.get().strip()
            pin = pin_entry.get().strip()

            def worker():
                resp = logic.login(login, pin)
                if resp.get("status") == "ok":
                    se.state["login"] = login
                    se.state["pin"] = pin
                    se.state["name"] = resp['data'].get('name')
                    se.state["token"] = resp['data'].get("token")
                    app.after(0, lambda: change_screen("main"))
                else:
                    se.state["login_error"] = resp.get("code", "server.error")
                    app.after(0, lambda: change_screen("login"))

            threading.Thread(target=worker, daemon=True).start()

    login_button = ctk.CTkButton(app, text=lo.loc("login.button"), font=("Arial", 16), command=on_click)
    login_button.place(relx=0.5, rely=0.7, anchor="center")

    link_button = ctk.CTkButton(app, text=lo.loc("register.promt"), font=("Arial", 12), fg_color='transparent', hover='transparent', command=lambda: change_screen('register'))
    link_button.place(relx=0.5, rely=0.8, anchor="center")

def show_register_screen():
    err = se.state.pop("login_error", None)
        
    main_label = ctk.CTkLabel(app, text=lo.loc("register.main"), font=("Arial", 24))
    main_label.place(relx=0.5, rely=0.2, anchor="center")
    
    login_entry = ctk.CTkEntry(app, placeholder_text=lo.loc("register.login_entry"))
    login_entry.place(relx=0.5, rely=0.30, anchor="center")

    name_entry = ctk.CTkEntry(app, placeholder_text=lo.loc("register.name_entry"))
    name_entry.place(relx=0.5, rely=0.40, anchor="center")
    
    pin_entry = ctk.CTkEntry(app, placeholder_text=lo.loc("register.pin_entry"))#, show="*")
    pin_entry.place(relx=0.5, rely=0.50, anchor="center")
    
    error_label = ctk.CTkLabel(app, text=lo.loc(err) if err else "", font=("Arial", 12), text_color="red")
    error_label.place(relx=0.5, rely=0.6, anchor="center")
    
    exit_btn = btn_exit()
    exit_btn.place(relx=0.85, rely=0.05, anchor="center")
    
    def on_click():
        login = login_entry.get().strip()
        pin = pin_entry.get().strip()
        name = name_entry.get().strip()
    
        def worker():
            resp = logic.register(login, name, pin)
            if resp.get("status") == "ok":
                se.state["login"] = login
                se.state["pin"] = pin
                se.state["name"] = name
                se.state["token"] = resp['data'].get("token")
                app.after(0, lambda: change_screen("main"))
            else:
                se.state["login_error"] = resp.get("code", "server.error")
                app.after(0, lambda: change_screen("register"))
    
        threading.Thread(target=worker, daemon=True).start()
    
    register_button = ctk.CTkButton(app, text=lo.loc("register.button"), font=("Arial", 16), command=on_click)
    register_button.place(relx=0.5, rely=0.7, anchor="center")

    link_button = ctk.CTkButton(app, text=lo.loc("login.promt"), font=("Arial", 12), fg_color='transparent', hover='transparent', command=lambda: change_screen('login'))
    link_button.place(relx=0.5, rely=0.8, anchor="center")

def show_main_screen():
    if not se.state['token']:
        change_screen('login')
        return

    
    app.after_idle(show_loading)

    # abv_label = ctk.CTkLabel(app, text=lo.loc("title"), font=("Arial", 10))
    # abv_label.pack(pady=0, padx=20, anchor="center")

    settings = ctk.CTkButton(app, text="\uE713", font=ICON_FONT, width=40, height=40, fg_color='transparent', hover_color=app.cget("fg_color"), command=lambda: change_screen('settings'))
    settings.place(rely=0.05, relx=0.99, anchor="e")

    name_label = ctk.CTkLabel(app, text=f"{se.state['name']}", font=("Arial", 20))
    name_label.pack(pady=0, padx=0, anchor="w")

    log_label = ctk.CTkLabel(app, text=f"@{se.state['login']}", font=("Arial", 14), text_color="#8A8A8A")
    log_label.pack(pady=0, padx=0, anchor="w")

    exit_btn = ctk.CTkButton(app, text='\uE748', font=ICON_FONT, command=lambda: logout(), fg_color="transparent", width=40, height=40)
    exit_btn.place(rely=0.05, relx=0.89, anchor="e")

    cards_frame = ctk.CTkScrollableFrame(app, width=400, height=400)
    cards_frame.pack(pady=25, padx=20, fill="both", expand=True)
    
    def main_get_acc():
        ok = get_accounts()

        if ok == False:
            se.state['retry_btn'] = 'main'
            se.state['last_error'] = 'acc.cantget'
            app.after(0, hide_loading)
            app.after(0, lambda: change_screen('error'))
            return

        def render_cards():
            hide_loading()
            for acc in se.state['accounts']:
                    acc_num = acc[0]
                    name = acc[1]
                    currency = acc[2]
                    bal = acc[3]
                    frozen = acc[4]
            
                    card_build(cards_frame, acc_num, name, currency, frozen, bal)

        app.after_idle(render_cards)

        

    threading.Thread(target=main_get_acc, daemon=True).start()

def show_account_screen():
    acc = se.state['current_acc']
    # print(acc)
    if acc:
        acc_data = ctk.CTkLabel(app, text=f"{acc[1]}, №{acc[0]}. баланс - {cvrt_div(acc[3])} {acc[2]}", font=("Arial", 12), cursor="hand2")
    acc_data.pack(pady=10)
    acc_data.bind("<Button-1>", lambda event: pyperclip.copy(acc[0]))
    ctktooltip.CTkToolTip(acc_data, message=lo.loc('copy.tooltip'))

    deposit_button = ctk.CTkButton(app, text=f"{lo.loc('accounts.deposit')}", command=lambda: prompt(["amount"], "deposit"), font=("Arial", 12))
    deposit_button.pack(padx=0, pady=5, anchor="w")

    withdraw_button = ctk.CTkButton(app, text=f"{lo.loc('accounts.withdraw')}", command=lambda: prompt(["amount"], "withdraw"), font=("Arial", 12))
    withdraw_button.pack(padx=0, pady=5, anchor="w")

    pay_button = ctk.CTkButton(app, text=f"{lo.loc('accounts.payment')}", command=lambda: prompt(["amount"], "payment"), font=("Arial", 12))
    pay_button.pack(padx=0, pady=5, anchor="w")

    transfer_button = ctk.CTkButton(app, text=f"{lo.loc('accounts.transfer')}", command=lambda: prompt(["recv_acc", "amount"], "transfer"), font=("Arial", 12))
    transfer_button.pack(padx=0, pady=5, anchor="w")

    # burn_button = ctk.CTkButton(app, text=f"{lo.loc('accounts.burn')}", command=lambda: prompt(["pin"], "burn"), font=("Arial", 12))
    # burn_button.pack(padx=0, pady=5, anchor="w")

    exit_button = ctk.CTkButton(app, text=f"{lo.loc('client.menu')}", command=lambda: change_screen('main'), font=("Arial", 12), fg_color="#C20202")
    exit_button.pack(padx=0, pady=20, anchor="center")

    
SCREENS = {
    "error": show_error_screen,
    "login": show_login_screen,
    "register": show_register_screen,
    "main": show_main_screen,
    "account": show_account_screen,
}


def client_main():
    app.after_idle(show_loading)

    try:
        change_screen('main')
        time.sleep(0.5)
        app.after_idle(hide_loading)
    except Exception as e:
        app.after_idle(hide_loading)
        se.state['last_error'] = e
        change_screen("error")



threading.Thread(target=client_main, daemon=True).start()
threading.Thread(target=watchdog, daemon=True).start()

app.title(lo.loc("title"))
app.geometry("400x400")
app.mainloop()