try:
    # библиотеки python
    import socket, threading, time, random
    from PIL import Image, ImageSequence

    # ctk и аддоны
    import customtkinter as ctk
    import ctktooltip
    # import ctktable

    # импорты из API
    from client import locales as lo, logic, session as se, settings
    from shared import codes, log

    # сторонние импорты
    import pyperclip


except ModuleNotFoundError as e:
    print("[PRE-INIT] Could not initialize some libraries!")
    print(e)
    exit(1)

print("[PRE-INIT] Libraries initialized")



ICON_FONT = (("Segoe MDL2 Assets", "Segoe UI Symbol", "Arial"), 20)

# инициализация
def client_init():
    try:
        log.log_init('latest_client.log')
        log.clear()
        log.info("[INIT] Log initiated")

        log.info(f"[INIT] Initiating settings")
        settings.init()

        time.sleep(0.2)

        lo.json_init()

        log.info("[INIT] JSON localization initialized.")
        log.info(f"[INIT] selected lang: {lo.loc('lang')}. if you see 'lang' it means no localization used")
    except Exception as e:
        print(f"[PRE-INIT] Could not init main")
        print(f"[PRE-INIT] Error: {e}")
        input("Critical failure detected, Press enter to exit")
        exit(1)
client_init()

log.debug(f"SETTINGS: {se.settings}")
log.debug(f"RUNTIME: {se.runtime}")


# маленькие функции
def close():
    log.info("[Main] Closing")
    if se.runtime['sock']:
        se.runtime["sock"].close()
    se.runtime['running'] = False
    time.sleep(1)
    exit(0)


def open_settings(from_screen):
    se.runtime['prev_screen'] = from_screen
    change_screen('settings')



def logout():
    log.info("[Main] logging out")
    logic.logout()
    change_screen('main')

def get_accounts():
    get_accounts_tries=0
    
    while get_accounts_tries <= 5:
        log.info(f"[Main] getting accounts try №{get_accounts_tries}")
        accounts = logic.get_accounts()
        if not accounts:
            return False
        if accounts.get('status') == 'ok':
            if accounts['data'].get('accounts') == {}:
                se.runtime['accounts'] = accounts['data'].get('accounts')
                return False
            se.runtime['accounts'] = accounts['data'].get('accounts')
            get_accounts_tries = 0
            return True
        else:
            log.warn("[Main] account timeout")
            get_accounts_tries += 1
        time.sleep(0.5)

    if get_accounts_tries >= 5:
        log.warn("[Main] account error")
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
    tick = 0
    se.runtime['pings'] = 0

    log.info(f"[WD] Watchdog started")

    while se.runtime['running'] == True:

        if se.settings['debug'] == True:
            log.debug(f"tick: {tick}")
        sock = se.runtime['sock']

        if se.runtime['need_restart']:
            try:
                se.runtime['aquire'].clear()
                se.runtime['sock'].close()
                se.runtime['sock'] = None
                se.runtime['need_restart'] = False
            except Exception:
                log.error("[WD] cannot set sock to closed")
                se.runtime['sock'] = None
                se.runtime['aquire'].clear()
                pass

        if se.runtime['conn'] == True:
            # log.info("[WD] Already connecting")
            pass
        
        else:
        # print(se.runtime['sock'])
        
        # print(ping)
    
            if not sock:
                log.info("[WD] No sock detected")
                def connect():
                    host = se.settings['ip']
                    port = se.settings['port']

                    se.runtime['sock'] = connect_to_server(host, port)
                    se.runtime['aquire'].set()
                if se.runtime['conn'] == False:
                    log.info("[WD] starting connect")
                    threading.Thread(target=connect, daemon=True).start()
                pass
            else:
                def ping_it():
                    se.runtime['ping_stat'] = True
                    log.info("[PING] starting ping")
                    ping = logic.ping()

                    if ping:
                        ping = ping.get('status')

                    if ping == "ok":
                        se.runtime['ping_stat'] = False
                        log.info("[PING] ping good")
                        se.runtime['pings'] = 0
                        pass
                    else: se.runtime['pings'] += 1; log.warn("[PING] ping dead")

                    if se.runtime['pings'] >= se.settings['wd_max_missed_pings']:
                        log.warn("[PING] max ping misses reached")
                        try:
                            se.runtime['aquire'].clear()
                            se.runtime['sock'].close()
                            se.runtime['sock'] = None
                        except Exception:
                            log.error("[WD] cannot set sock to closed")
                            se.runtime['sock'] = None
                            se.runtime['aquire'].clear()
                            pass
                        se.runtime['pings'] = 0
                    se.runtime['ping_stat'] = False
                            

                if se.runtime['ping_stat'] == False and tick % se.settings['wd_timeout'] == 0:
                    threading.Thread(target=ping_it, daemon=True).start()

        tick += 1
        time.sleep(se.settings['wd_tick'])

    log.info("[WD] Closed")
    return

    


def connect_to_server(host, port):
    log.info("[Conn] connecting")

    se.runtime['conn'] = True
    app.after_idle(show_connect)
    se.runtime['conn_tries'] = 1
    app.after_idle(update_connect)
    while se.runtime['conn'] == True and se.runtime['running'] == True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            app.after_idle(hide_connect)
            se.runtime['conn'] = False
            log.info("[Conn] connected")
            return sock
        except (TimeoutError, ConnectionRefusedError, OSError) as e:
            log.warn(f"[Conn] cannot connect: {e}")
            se.runtime['conn_tries'] += 1
            app.after_idle(update_connect)
            time.sleep(1)
            continue
    log.info("[Conn] Exiting connection func")


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
            log.info(f"[Main] card {acc_name} clicked")
            se.runtime['current_acc'] = [acc_num, acc_name, acc_currency, acc_bal, is_frozen]
            card.after_idle(lambda: change_screen('account'))
            return
    
    name_label = ctk.CTkLabel(card, text=f'{acc_name}', font=('arial_black', 16))
    name_label.place(relx=0.03, rely=0.2, anchor='w')

    bal_label = ctk.CTkLabel(card, text=f'{cvrt_div(acc_bal)} {acc_currency}', font=('arial_black', 28))
    bal_label.place(relx=0.03, rely=0.5, anchor='w')

    num_label = ctk.CTkLabel(card, text=f'{lo.loc('acc.acc')}{acc_num}', font=('arial_black', 16), text_color="#E6E6E6")
    num_label.place(relx=0.03, rely=0.8, anchor='w')

    card.bind("<ButtonRelease-1>", onclick)
    name_label.bind("<ButtonRelease-1>", onclick)
    bal_label.bind("<ButtonRelease-1>", onclick)
    num_label.bind("<ButtonRelease-1>", onclick)

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
    acc = se.runtime['current_acc']

    if "amount" in prompts:
        bal = ctk.CTkLabel(top, text=f"счет - {acc[1]}, баланс - {cvrt_div(acc[3])} {acc[2]}")
        bal.grid(row=0, column=1, padx=10, pady=0)

    for i, field in enumerate(prompts, start=1):

        label = lo.loc(f"prompt.{field}")

        if field in combo:
            accounts = se.runtime['accounts']
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
        se.runtime['loading_msg'] = lo.loc("loadmsg.processing")
        app.after(0, show_loading)
        values = []

        for field in prompts:
            val = entries[field].get().strip()

            if field == 'amount':
                if val == "" and redir != "payment":
                    se.runtime['last_error'] = 'amount.not_digit1'
                    app.after(0, hide_loading)
                    app.after_idle(lambda: change_screen('error'))
                    return
                if val != "":
                    try:
                        val = cvrt_mul(val)
                    except ValueError:
                        se.runtime['last_error'] = 'amount.not_digit2'
                        app.after(0, hide_loading)
                        app.after_idle(lambda: change_screen('error'))

                if val == "" and redir == "payment":
                    val = None
            values.append(val)
            
            


        def worker():
            try:
                resp = getattr(logic, redir)(*values)

                if resp['status'] == "error":
                    data = resp.get('data')
                    se.runtime['last_error'] = f"{lo.loc(resp.get('code'))}"
                    if data:
                        se.runtime['last_error'] += f"\n{data.get('e')}"
                    app.after(0, hide_loading)
                    app.after_idle(lambda: change_screen('error'))
                else:
                    app.after(0, hide_loading)
                    app.after_idle(lambda: change_screen('main'))
            except Exception as e:
                se.runtime['last_error'] = str(e)
                app.after(0, hide_loading)
                app.after_idle(lambda: change_screen('error'))

            se.runtime['loading_msg'] = ""

        threading.Thread(target=worker, daemon=True).start()
        top.destroy()
        return
        
    submit_btn = ctk.CTkButton(top, text=lo.loc(f"accounts.{redir}"), command=_onclick)
    submit_btn.grid(row=len(prompts)+1, column=0, columnspan=2, pady=15)

    error_lbl = ctk.CTkLabel(top, text="")
    error_lbl.grid(row=len(prompts)+2, column=0, columnspan=2)



# создание app
app = ctk.CTk()
log.info("[INIT] Main window created")


# Очистка и изменение экрана
def clear_screen():
    for widget in app.winfo_children():
        if widget == conn_overlay or widget == loading_overlay:
            continue
        try:
            widget.destroy()
        except Exception: pass

def change_screen(screen):
    log.info(f"[Render] Switching screen to {screen}")
    app.after(0, _change_screen_gui, screen)

def _change_screen_gui(screen):
    clear_screen()
    if screen in SCREENS:
        SCREENS[screen]()
    else:
        se.runtime['last_error'] = "client.screen_not_found"
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

tries_label = ctk.CTkLabel(conn_overlay, text=f"{lo.loc('client.tries')}{se.runtime['conn_tries']}", font=("Arial", 14))
tries_label.place(relx=0.5, rely=0.7, anchor="center")

long_label = ctk.CTkLabel(conn_overlay, text=lo.loc(""), font=("Arial", 10))
long_label.place(relx=0.5, rely=0.9, anchor="center")

exit_btn = btn_exit(conn_overlay)

def update_connect():
    if not conn_overlay.winfo_exists() or not tries_label.winfo_exists():
        return
    tries_label.configure(text=f"{lo.loc('client.tries')}{se.runtime['conn_tries']}")
    conn_overlay.lift()
    if se.runtime['conn_tries'] >= 10:
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

loading_load = ctk.CTkLabel(loading_overlay, text=se.runtime['loading_msg'], font=("Arial", 14))
loading_load.place(relx=0.5, rely=0.6, anchor="center")


def show_loading():
    loading_load.configure(text=se.runtime['loading_msg'])
    loading_overlay.place(relwidth=1, relheight=1, x=0, y=0)
    loading_overlay.lift()

    animate_spinner(spinner_lbl_load)

def hide_loading():
    loading_overlay.place_forget()

    spinner_lbl_load._stop_anim = True 

def update_loading():
    loading_load.configure(text=se.runtime['loading_msg'])


# экраны
def show_error_screen():
    error_label = ctk.CTkLabel(app, text=f"{lo.loc('client.error')}: {lo.loc(se.runtime['last_error'])}", font=("Arial", 14))
    error_label.place(relx=0.5, rely=0.45, anchor="center")

    exit_btn = btn_exit(app)
    exit_btn.place(relx=0.5, rely=0.55, anchor="center")
    
    if se.runtime['retry_btn']:
        target = se.runtime.get("retry_btn")
        retry_btn = ctk.CTkButton(app, text=lo.loc("client.retry"), font=("Arial", 14), command=lambda: change_screen(target), fg_color="#5C4E4E")
        se.runtime['retry_btn'] = None
        retry_btn.place(relx=0.5, rely=0.75, anchor="center")

    if se.runtime['token']:
        menu_btn = ctk.CTkButton(app, text=lo.loc("client.menu"), font=("Arial", 14), command=lambda: change_screen('main'), fg_color="#5C4E4E")
        menu_btn.place(relx=0.5, rely=0.65, anchor="center")


def show_login_screen():
    
    err = se.runtime.pop("login_error", None)
    
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

    if se.runtime['login']:
        login_entry.set(se.runtime['login'])
    if se.runtime['pin']:
        pin_entry.set(se.runtime['pin'])

    def on_click():
            login = login_entry.get().strip()
            pin = pin_entry.get().strip()

            se.runtime['loading_msg'] = lo.loc("loadmsg.processing")
            app.after_idle(show_loading)

            def worker():
                resp = logic.login(login, pin)
                if resp.get("status") == "ok":
                    se.runtime["login"] = login
                    se.runtime["pin"] = pin
                    se.runtime["name"] = resp['data'].get('name')
                    se.runtime["token"] = resp['data'].get("token")
                    app.after_idle(hide_loading)
                    app.after(0, lambda: change_screen("main"))
                else:
                    se.runtime["login_error"] = resp.get("code", "server.error")
                    print(resp.get('code'))
                    code = resp.get('code')

                    if code and code.startswith('login'):
                        se.runtime["pin"] = pin
                        se.runtime["login"] = None
                    elif code and code.startswith('pin'):
                        se.runtime["login"] = login
                        se.runtime["pin"] = None
                    else:
                        se.runtime["login"] = login
                        se.runtime["pin"] = pin

                    app.after_idle(hide_loading)
                    app.after(0, lambda: change_screen("login"))
                se.runtime['loading_msg'] = ""
            threading.Thread(target=worker, daemon=True).start()

    login_button = ctk.CTkButton(app, text=lo.loc("login.button"), font=("Arial", 16), command=on_click)
    login_button.place(relx=0.5, rely=0.7, anchor="center")

    link_button = ctk.CTkButton(app, text=lo.loc("register.promt"), font=("Arial", 12), fg_color='transparent', hover='transparent', command=lambda: change_screen('register'))
    link_button.place(relx=0.5, rely=0.8, anchor="center")

def show_register_screen():
    err = se.runtime.pop("login_error", None)
        
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

        se.runtime['loading_msg'] = lo.loc("loadmsg.processing")
        app.after_idle(show_loading)
    
        def worker():
            resp = logic.register(login, name, pin)
            if resp.get("status") == "ok":
                se.runtime["login"] = login
                se.runtime["pin"] = pin
                se.runtime["name"] = name
                se.runtime["token"] = resp['data'].get("token")
                app.after_idle(hide_loading)
                app.after(0, lambda: change_screen("main"))
            else:
                se.runtime["login_error"] = resp.get("code", "server.error")
                app.after_idle(hide_loading)
                app.after(0, lambda: change_screen("register"))
            se.runtime['loading_msg'] = ""
    
        threading.Thread(target=worker, daemon=True).start()
    
    register_button = ctk.CTkButton(app, text=lo.loc("register.button"), font=("Arial", 16), command=on_click)
    register_button.place(relx=0.5, rely=0.7, anchor="center")

    link_button = ctk.CTkButton(app, text=lo.loc("login.promt"), font=("Arial", 12), fg_color='transparent', hover='transparent', command=lambda: change_screen('login'))
    link_button.place(relx=0.5, rely=0.8, anchor="center")

def show_main_screen():
    if not se.runtime['token']:
        change_screen('login')
        return

    se.runtime['loading_msg'] = lo.loc("loadmsg.get_accounts")
    app.after_idle(show_loading)

    # abv_label = ctk.CTkLabel(app, text=lo.loc("title"), font=("Arial", 10))
    # abv_label.pack(pady=0, padx=20, anchor="center")

    create_acc = ctk.CTkButton(app, text=lo.loc("accounts.create_acc"), font=("Arial", 12), command=lambda: prompt(["name"], "create_acc")) # lambda: prompt(["name", "currency"], "create_acc"))
    create_acc.place(rely=0.15, relx=0.5, anchor="center")

    # кнопки
    exit_btn = ctk.CTkButton(app, text='\uE748', font=ICON_FONT, command=lambda: logout(), fg_color="transparent", width=40, height=40)
    exit_btn.place(rely=0.05, relx=0.89, anchor="e")

    settings = ctk.CTkButton(app, text="\uE713", font=ICON_FONT, width=40, height=40, fg_color='transparent', hover_color=app.cget("fg_color"), command=lambda: change_screen('settings'))
    settings.place(rely=0.05, relx=0.99, anchor="e")

    refresh = ctk.CTkButton(app, text="\uE72C", font=ICON_FONT, width=40, height=40, fg_color='transparent', hover_color=app.cget("fg_color"), command=lambda: change_screen('main'))
    refresh.place(rely=0.05, relx=0.79, anchor="e")

    # конец кнопок

    name_label = ctk.CTkLabel(app, text=f"{se.runtime['name']}", font=("Arial", 20))
    name_label.pack(pady=0, padx=0, anchor="w")

    login_label = ctk.CTkLabel(app, text=f"@{se.runtime['login']}", font=("Arial", 14), text_color="#8A8A8A")
    login_label.pack(pady=0, padx=0, anchor="w")

    cards_frame = ctk.CTkScrollableFrame(app, width=400, height=400)
    cards_frame.pack(pady=25, padx=20, fill="both", expand=True)
    
    def main_get_acc():
        log.info("[Render] Drawing main UI")
        ok = get_accounts()

        se.runtime['loading_msg'] = lo.loc("loadmsg.card_drawing")
        app.after(0, update_loading)

        if not ok:
            se.runtime['retry_btn'] = 'main'
            se.runtime['last_error'] = 'acc.cantget'
            app.after(0, hide_loading)
            app.after(0, lambda: change_screen('error'))
            return

        def render_cards():
            start_time = time.perf_counter()
            try:
                num = 1
                for acc in se.runtime['accounts']:
                    # log.info(f"[Render] Drawing card #{num}")
                    acc_num = acc[0]
                    name = acc[1]
                    currency = acc[2]
                    bal = acc[3]
                    frozen = acc[4]
                
                    card_build(cards_frame, acc_num, name, currency, frozen, bal)
                    num += 1

                elapsed_time = time.perf_counter() - start_time
                app.after_idle(lambda: log.info(f"[Render] drawn {len(se.runtime['accounts'])} cards in {elapsed_time:.4f}s"))
            except Exception as e:
                log.crit(f"[Render] cannot draw cards: {e}")
            finally:
                
                se.runtime['loading_msg'] = ""
                app.after(0, hide_loading)

        app.after_idle(render_cards)
        
        

        

    threading.Thread(target=main_get_acc, daemon=True).start()

def show_account_screen():
    acc = se.runtime['current_acc']
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


def show_settings_screen():
    se.runtime['snapshot'] = se.settings.copy()

    langs_map = lo.get_available_langs()
    def on_language_change(selected_display_name: str):
        selected_code = langs_map.get(selected_display_name)
        if not selected_code:
            return

        se.settings["language"] = selected_code

        lo.clear()
        lo.json_init(selected_code)
        
    def on_save():
        raw_port = port.get()
        new_ip = ip.get()


        if not raw_port.isdigit() or not (1 <= int(raw_port) <= 65535):
        # Подсвечиваем поле порта красным при ошибке и не даем сохранить
            port.configure(border_color="red")
            return

        # 2. Проверяем, что IP/домен не пустой
        if not new_ip:
            ip.configure(border_color="red")
            return

        new_port = int(raw_port)

        if (se.settings['port'] != new_port) or (se.settings['ip'] != new_ip):
            se.runtime['need_restart'] = True

        se.settings['port'] = new_port
        se.settings['ip'] = new_ip
        
        se.runtime.pop('snapshot', None)
        settings.save()
        change_screen('main')
        return

    def on_exit():
        snapshot = se.runtime.pop('snapshot', None)
        if snapshot:
            se.settings.clear()
            se.settings.update(snapshot)
            lo.clear()
            lo.json_init(se.settings["language"])
        change_screen('main')

    
    save_btn = ctk.CTkButton(app, text=lo.loc('settings.save'), font=ICON_FONT, command=on_save)
    save_btn.place(rely=0.8, relx=0.5, anchor="center")

    exit_btn = ctk.CTkButton(app, text=lo.loc('settings.exit'), font=('Arial', 12), command=on_exit)
    exit_btn.place(rely=0.9, relx=0.5, anchor="center")

    lang_menu = ctk.CTkOptionMenu(app, values=list(langs_map.keys()), command=on_language_change)
    
    current_lang_name = lo.loc("lang")
    if current_lang_name in langs_map:
        lang_menu.set(current_lang_name)

    lang_menu.place(rely=0.3, relx=0.5, anchor="center")

    debug_var = ctk.BooleanVar(value=bool(se.settings["debug"]))
    def on_debug():
        se.settings["debug"] = debug_var.get()
        settings.save()

    checkbox = ctk.CTkCheckBox(app, text=lo.loc("settings.debug"), command=on_debug, variable=debug_var, onvalue=True, offvalue=False)
    checkbox.place(rely=0.6, relx=0.5, anchor="center")

    ip = ctk.CTkEntry(app, placeholder_text=lo.loc('settings.ip'))
    ip.insert(0, str(se.settings['ip'] or ""))
    ip.place(rely=0.4, relx=0.5, anchor="center")

    port = ctk.CTkEntry(app, placeholder_text=lo.loc('settings.port'))
    port.insert(0, str(se.settings['port'] or ""))
    port.place(rely=0.5, relx=0.5, anchor="center")



# доступные экраны (для change_screen)
SCREENS = {
    "error": show_error_screen,
    "login": show_login_screen,
    "register": show_register_screen,
    "main": show_main_screen,
    "account": show_account_screen,
    "settings": show_settings_screen,
}

# точка входа
def client_main():
    se.runtime['loading_msg'] = lo.loc("loadmsg.starting")
    app.after_idle(show_loading)

    wait_time = random.randint(0, 2)

    try:

        app.after((wait_time*1000), lambda: change_screen('main'))
        time.sleep(wait_time)
        app.after_idle(hide_loading)
        # while True:
        #     app.after((wait_time*1000), lambda: change_screen('main'))
        #     time.sleep(1)
    except Exception as e:
        app.after_idle(hide_loading)
        se.runtime['last_error'] = e
        change_screen("error")

    se.runtime['loading_msg'] = ""


# запуск


log.info("[INIT] Client_main started")
threading.Thread(target=client_main, daemon=True).start()
log.info("[INIT] Starting watchdog")
threading.Thread(target=watchdog, daemon=True).start()



app.resizable(False, False)
app.title(lo.loc("title"))
app.geometry("400x400")
app.mainloop()