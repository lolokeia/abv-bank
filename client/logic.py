from client import session
from shared import protocol, comms, codes, log
import tabulate, time, threading
timeout = 15


def _send_n_recv(action, data=None, _retry=True):
    if action != "ping":
        log.info(f"[logic] request: {action}")


    if not session.runtime['aquire'].wait(timeout=timeout):
        log.warn(f"[logic] no sock for {action} within {timeout}s")
        return comms.error(code=codes.CONNECTION_NO)
    
    sock = session.runtime["sock"]

    if not sock:
        return comms.error(code=codes.CONNECTION_NO)

    req = comms.request(action=action, data=data)
    token = session.runtime.get('token')
    try:
        if token:
            req['token'] = token

        with session.runtime['sock_lock']:
            if action != "ping":
                log.req(f"[logic] Sent: {action}")
            protocol.send_message(message=req, sock=sock)


    except (TimeoutError, ConnectionAbortedError, ConnectionRefusedError, ConnectionResetError) as e:
        log.warn(f"[logic] timeout or connection error: {action} > {e}")
        return comms.error(code='connection.error', data={"e": e})
    
    except (AttributeError, OSError) as e:
        log.error(f"[logic] No sock or sock closed error: {action} > {e}")
        return comms.error(code='sock.error', data={"e": e})

    except Exception as e:
        log.error(f"[logic] Exception: {action} > {e}")
        return comms.error(code='send.error', data={"e": e})
    
    try:
        with session.runtime['sock_lock']:
            resp = protocol.recv_message(sock=sock)
            if action != "ping":
                log.resp(f"[logic] Received: {action} > {resp.get('status')}")
            
    except (TimeoutError, ConnectionAbortedError, ConnectionRefusedError, ConnectionResetError) as e:
        log.warn(f"[logic] Recv error: {action} > {e}")
        return comms.error(code='connection.error', data={"e": e})
    
    except Exception as e:
        log.error(f"[logic] Exception: {action} > {e}")
        return comms.error(code='recv.error', data={"e": e})

    if resp:
        if resp.get('code') == codes.SESSION_EXPIRED and _retry:
            log.warn(f"[logic] Session expired")
            relog = quiet_relog()
            if relog.get('status') != 'ok':
                log.info(f"[logic] Relogged")
                return relog
            return _send_n_recv(action, data, _retry=False)
    
    return resp







def get_current_acc():
    return session.runtime['current_acc'][0]

# no token required
def login(login_input, pin_input):
    login_msg = _send_n_recv(action='login', data={'login': login_input, 'pin': pin_input})
    if login_msg.get('status') == "ok":
        session.runtime['token'] = login_msg['data'].get('token')
    return login_msg

def register(login_input, name_input, pin_input):
    return _send_n_recv(action='register', data={'login': login_input, 'name': name_input, 'pin': pin_input})


# token required
def logout():
    resp = _send_n_recv(action='logout')
    if resp and resp.get('status') == 'ok':
        session.runtime['token'] = None
    return resp

def get_accounts():
    return _send_n_recv(action='get_accounts')

def get_balance():
    return _send_n_recv(action='get_balance', data={'acc_num': get_current_acc()})

def deposit(amount):
    return _send_n_recv(action='deposit', data={'amount': amount, 'acc_num': get_current_acc()})

def withdraw(amount):
    return _send_n_recv(action='withdraw', data={'amount': amount, 'acc_num': get_current_acc()})

def payment(amount=None):
    return _send_n_recv(action='payment', data={'amount': amount, 'acc_num': get_current_acc()})

def transfer(recv_num, amount):
    return _send_n_recv(action='transfer', data={'amount': amount, 'recv_num': recv_num, 'acc_num': get_current_acc()})

def burn(pin):
    return _send_n_recv(action='burn', data={'pin': pin, 'acc_num': get_current_acc()})

def get_history(isrecent=True):
    return _send_n_recv(action='get_history', data={'isrecent': isrecent})

def change_pin(old_pin, new_pin):
    resp = _send_n_recv(action='change_pin', data={'old_pin': old_pin, 'new_pin': new_pin})
    if resp.get('status') == 'ok':
        session.runtime['pin'] = new_pin
    return resp

def change_name(new_name):
    resp = _send_n_recv(action='change_name', data={'new_name': new_name})
    if resp.get('status') == 'ok':
        session.runtime['name'] = new_name
    return resp

def change_login(new_login):
    resp = _send_n_recv(action='change_login', data={'new_login': new_login})
    if resp.get('status') == 'ok':
        session.runtime['login'] = new_login
    return resp

def format_history(isrecent=True):
    get_his = get_history(isrecent=isrecent)
    if get_his.get('status') == "ok":
        history = get_his['data'].get('history')
        if history is None:
            return "История пуста"
        return tabulate.tabulate(
            history,
            headers=["Тип", "Сумма", "Баланс", "Описание", "Дата"])
    else: 
        return "Ошибка показа истории"
    
def ping():
    return _send_n_recv(action='ping')
    
def quiet_relog():
    log.info(f"[logic] Relogging")
    login_input = session.runtime['login']
    pin = session.runtime['pin']

    resp = login(login_input, pin)
    if resp.get('status') == "ok":
        return resp
    else:
        log.warn(f"[logic] Not relogged")
        session.runtime['token'] = None
        session.runtime['login'] = None
        session.runtime['pin'] = None
        return resp


def create_acc(name, currency="RUB"):
    return _send_n_recv(action='create_acc', data={'name': name, "currency": currency})

def delete_acc(pin):
    return _send_n_recv(action='delete_acc', data={'acc_num': get_current_acc(), 'pin': pin})