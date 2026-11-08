# библиотеки python
import socket, threading, time, random
from PIL import Image, ImageSequence

# ctk и аддоны
import customtkinter as ctk
import ctktooltip
# import ctktable

# импорты из API
from client import locales as lo, logic, session as se
from shared import codes

# Импорт конфига
import client_config as config

# сторонние импорты
import pyperclip



ICON_FONT = (("Segoe MDL2 Assets", "Segoe UI Symbol", "Arial"), 20)

# инициализация локализации
lo.json_init()


# маленькие функции
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




# соединение с сервером
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


# сборка карточки счета
def card_build(parent, acc_num, acc_name, acc_currency, is_frozen, acc_bal):
    def scale_to_hex(number):
        if number < 10:
            number = 10
        elif number > 99:
            number = 99

        dec_value = round(80 + (number - 10) * 64 / 89)
        
        return hex(dec_value)[2:].upper().zfill(2)

    def random_color(acc_num):
        n = 20
        
        r_dec = int(acc_num[0:2])
        g_dec = int(acc_num[2:4])
        b_dec = int(acc_num[4:6])
        
        r = scale_to_hex(r_dec)
        g = scale_to_hex(g_dec)
        b = scale_to_hex(b_dec)
        value = f'#{r}{g}{b}'
        
        r_border = scale_to_hex(r_dec - n)
        g_border = scale_to_hex(g_dec - n)
        b_border = scale_to_hex(b_dec - n)
        border = f'#{r_border}{g_border}{b_border}'
        
        return value, border
    
    color, border = random_color(acc_num)
    card = ctk.CTkFrame(parent, width=350, height=100, border_width=5, fg_color=color, border_color=border)
    
    card.pack_propagate(False) 

    card.pack(pady=5)


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


    

# промт для разных действий
def prompt(prompts, redir):

    combo = ("acc_from", "acc_to", "recv_acc")

    top = ctk.CTkToplevel(app)
    top.resizable(False, False)
    top.title(lo.loc("client.enter_data"))
    top.geometry("300x" + str(100 + len(prompts) * 50))
    top.attributes("-topmost", True)
    top.grab_set()
    entries = {}
    acc = se.state['current_acc']

    if "amount" in prompts:
        bal = ctk.CTkLabel(top, text=f"счет - {acc[1]}, баланс - {cvrt_div(acc[3])} {acc[2]}")
        bal.grid(row=0, column=1, padx=10, pady=0)

    for i, field in enumerate(prompts, start=1):

        label = lo.loc(f"prompt.{field}")

        if field in combo:
            accounts = se.state['accounts']
            display_val = [f"{item[1]} - {item[0]}" if isinstance(item, (list, tuple)) else str(item) for item in accounts]

            widget = ctk.CTkComboBox(top, values=display_val)
            widget.set(label)

            def on_account_selected(selected_display: str, _w=widget) -> None:
                account_number = selected_display.split(" - ")[-1].strip()
                _w.after_idle(lambda: _w.set(account_number))

            widget.configure(command=on_account_selected)

            def clear_hint(event=None, _w=widget, _label=label):
                if _w.get() == str(_label):
                    _w.set("")

            widget._entry.bind("<FocusIn>", clear_hint)
            widget._entry.bind("<Button-1>", clear_hint)
            
        else: 
            widget = ctk.CTkEntry(top, placeholder_text=label)
            
        widget.grid(row=i, column=1, padx=10, pady=10)
        
        entries[field] = widget

    def _onclick():
        app.after(0, show_loading)
        values = []

        for field in prompts:
            val = entries[field].get().strip()

            if field == 'amount':
                if val == "" and redir != "payment":
                    se.state['last_error'] = 'amount.not_digit1'
                    app.after(0, hide_loading)
                    app.after_idle(lambda: change_screen('error'))
                    return
                if val != "":
                    try:
                        val = cvrt_mul(val)
                    except ValueError:
                        se.state['last_error'] = 'amount.not_digit2'
                        app.after(0, hide_loading)
                        app.after_idle(lambda: change_screen('error'))

                if val == "" and redir == "payment":
                    val = None
            values.append(val)
            
            


        def worker():
            try:
                resp = getattr(logic, redir)(*values)

                if resp['status'] == "error":
                    se.state['last_error'] = resp.get('code')
                    app.after(0, hide_loading)
                    app.after_idle(lambda: change_screen('error'))
                else:
                    app.after(0, hide_loading)
                    app.after_idle(lambda: change_screen('main'))
            except Exception as e:
                se.state['last_error'] = str(e)
                app.after(0, hide_loading)
                app.after_idle(lambda: change_screen('error'))

        threading.Thread(target=worker, daemon=True).start()
        top.destroy()
        return
        
    submit_btn = ctk.CTkButton(top, text=lo.loc(f"accounts.{redir}"), command=_onclick)
    submit_btn.grid(row=len(prompts)+1, column=0, columnspan=2, pady=15)

    error_lbl = ctk.CTkLabel(top, text="")
    error_lbl.grid(row=len(prompts)+2, column=0, columnspan=2)



# создание app
app = ctk.CTk()


# Очистка и изменение экрана
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


# кнопка выхода (ap - это app)
def btn_exit(ap):
    return ctk.CTkButton(ap, text='\uE711', font=ICON_FONT, command=close, fg_color="transparent", width=40, height=40)


frames = [ctk.CTkImage(f.copy(), f.copy(), size=(64, 64)) for f in ImageSequence.Iterator(Image.open("loading.webp"))]


# гифка
def animate_spinner(label_widget, idx=None):
    if not label_widget.winfo_exists():
        return

    # Если idx is None, значит это запрос на запуск (из show_connect)
    if idx is None:
        if getattr(label_widget, "_is_animating", False):
            return
        label_widget._is_animating = True
        label_widget._stop_anim = False
        idx = 0 # Начинаем с первого кадра

    # Если пришла команда остановиться
    if getattr(label_widget, "_stop_anim", False):
        label_widget._is_animating = False
        return

    label_widget.configure(image=frames[idx])
    # 16 мс (~60 FPS) — оптимально для Tkinter. 8 мс может вызвать лаги.
    label_widget.after(8, lambda: animate_spinner(label_widget, (idx + 1) % len(frames)))


# Экран коннекта
conn_overlay = ctk.CTkFrame(app, fg_color="#1F1E1E")

connect_label = ctk.CTkLabel(conn_overlay, text=lo.loc("client.connecting"), font=("Arial", 24))
connect_label.place(relx=0.5, rely=0.3, anchor="center")

spinner_lbl_conn = ctk.CTkLabel(conn_overlay, text="", image=frames[0])
spinner_lbl_conn.place(relx=0.5, rely=0.5, anchor="center")



# progressbar = ctk.CTkProgressBar(conn_overlay, orientation="horizontal", indeterminate_speed=0.5)
# progressbar.set(0)
# progressbar.start()
# progressbar.place(relx=0.5, rely=0.5, anchor="center")

tries_label = ctk.CTkLabel(conn_overlay, text=f"{lo.loc('client.tries')}{se.state['conn_tries']}", font=("Arial", 14))
tries_label.place(relx=0.5, rely=0.7, anchor="center")

long_label = ctk.CTkLabel(conn_overlay, text=lo.loc(""), font=("Arial", 10))
long_label.place(relx=0.5, rely=0.9, anchor="center")

exit_btn = btn_exit(conn_overlay)

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
    animate_spinner(spinner_lbl_conn)

def hide_connect():
    conn_overlay.place_forget()
    spinner_lbl_conn._stop_anim = True 


# экран загрузки
loading_overlay = ctk.CTkFrame(app, fg_color="#1F1E1E")

loading = ctk.CTkLabel(loading_overlay, text=lo.loc("client.loading"), font=("Arial", 20))
loading.place(relx=0.5, rely=0.3, anchor="center")

spinner_lbl_load = ctk.CTkLabel(loading_overlay, text="", image=frames[0])
spinner_lbl_load.place(relx=0.5, rely=0.5, anchor="center")


def show_loading():
    loading_overlay.place(relwidth=1, relheight=1, x=0, y=0)
    loading_overlay.lift()

    animate_spinner(spinner_lbl_load)

def hide_loading():
    loading_overlay.place_forget()

    spinner_lbl_load._stop_anim = True 



# экраны
def show_error_screen():
    error_label = ctk.CTkLabel(app, text=f"{lo.loc('client.error')}: {lo.loc(se.state['last_error'])}", font=("Arial", 14))
    error_label.place(relx=0.5, rely=0.45, anchor="center")

    exit_btn = btn_exit(app)
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

    exit_btn = btn_exit(app)
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
    
    exit_btn = btn_exit(app)
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

    create_acc = ctk.CTkButton(app, text=lo.loc("accounts.create_acc"), font=("Arial", 12), command=lambda: prompt(["name"], "create_acc")) # lambda: prompt(["name", "currency"], "create_acc"))
    create_acc.place(rely=0.15, relx=0.5, anchor="center")

    settings = ctk.CTkButton(app, text="\uE713", font=ICON_FONT, width=40, height=40, fg_color='transparent', hover_color=app.cget("fg_color"), command=lambda: change_screen('settings'))
    settings.place(rely=0.05, relx=0.99, anchor="e")

    name_label = ctk.CTkLabel(app, text=f"{se.state['name']}", font=("Arial", 20))
    name_label.pack(pady=0, padx=0, anchor="w")

    login_label = ctk.CTkLabel(app, text=f"@{se.state['login']}", font=("Arial", 14), text_color="#8A8A8A")
    login_label.pack(pady=0, padx=0, anchor="w")

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

    exit_button = ctk.CTkButton(app, text=f"{lo.loc('client.menu')}", command=lambda: change_screen('main'), font=("Arial", 12))
    exit_button.pack(padx=0, pady=20, anchor="center")

    transfer_button = ctk.CTkButton(app, text=f"{lo.loc('accounts.delete_acc')}", command=lambda: prompt(["pin"], "delete_acc"), font=("Arial", 12), fg_color="#830000")
    transfer_button.pack(padx=0, pady=5, anchor="center")



# доступные экраны (для change_screen)
SCREENS = {
    "error": show_error_screen,
    "login": show_login_screen,
    "register": show_register_screen,
    "main": show_main_screen,
    "account": show_account_screen,
}

# точка входа
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


# запуск
threading.Thread(target=client_main, daemon=True).start()
threading.Thread(target=watchdog, daemon=True).start()


app.resizable(False, False)
app.title(lo.loc("title"))
app.geometry("400x400")
app.mainloop()