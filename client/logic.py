from client import session
from shared import protocol, comms
import tabulate


def _send_n_recv(action, data=None, _retry=True):
    sock = session.state["sock"]
    if sock is None:
        return comms.error(message=f'Ошибка: нет подключения к серверу', code='no_connection')
    
    req = comms.request(action=action, data=data)
    token = session.state.get('token')
    try:
        if token:
            req['token'] = token
            protocol.send_message(message=req, sock=session.state["sock"])
        else:
            protocol.send_message(message=req, sock=session.state["sock"])
    except Exception as e:
        return comms.error(message=f'Ошибка отправки: {e}', code='send_error')
    
    try:
        resp = protocol.recv_message(sock=session.state["sock"])
    except Exception as e:
        return comms.error(message=f'Ошибка приема: {e}', code='recv_error')

    
    if resp.get('code') == 'session_expired' and _retry:
        relog = quiet_relog()
        if relog.get('status') != 'ok':
            return relog
        return _send_n_recv(action, data, _retry=False)
    
    return resp








# no token required
def login(login_input, pin_input):
    login_msg = _send_n_recv(action='login', data={'login': login_input, 'pin': pin_input})
    if login_msg.get('status') == "ok":
        session.state['token'] = login_msg['data'].get('token')
    return login_msg

def register(login_input, name_input, pin_input):
    return _send_n_recv(action='register', data={'login': login_input, 'name': name_input, 'pin': pin_input})


# token required
def logout():
    resp = _send_n_recv(action='logout')
    if resp and resp.get('status') == 'ok':
        session.state['token'] = None
        session.state['login'] = None
        session.state['pin'] = None
        session.state['balance'] = None
    return resp


def get_balance():
    return _send_n_recv(action='get_balance')

def deposit(amount):
    return _send_n_recv(action='deposit', data={'amount': amount})

def withdraw(amount):
    return _send_n_recv(action='withdraw', data={'amount': amount})

def payment(amount=None):
    return _send_n_recv(action='payment', data={'amount': amount})

def transfer(recv_login, amount):
    return _send_n_recv(action='transfer', data={'amount': amount, 'recv_login': recv_login})

def burn(pin):
    return _send_n_recv(action='burn', data={'pin': pin})

def get_history(isrecent=True):
    return _send_n_recv(action='get_history', data={'isrecent': isrecent},)

def change_pin(old_pin, new_pin):
    resp = _send_n_recv(action='change_pin', data={'old_pin': old_pin, 'new_pin': new_pin})
    if resp.get('status') == 'ok':
        session.state['pin'] = new_pin
    return resp

def change_name(new_name):
    resp = _send_n_recv(action='change_name', data={'new_name': new_name})
    if resp.get('status') == 'ok':
        session.state['name'] = new_name
    return resp

def change_login(new_login):
    resp = _send_n_recv(action='change_login', data={'new_login': new_login})
    if resp.get('status') == 'ok':
        session.state['login'] = new_login
    return resp

def format_history(isrecent=True):
    get_his = get_history(isrecent=isrecent)
    if get_his.get('status') == "ok":
        history = get_his['data'].get('transactions')
        if history is None:
            return "История пуста"
        return tabulate.tabulate(
            history,
            headers=["Тип", "Сумма", "Баланс", "Описание", "Дата"])
    else: 
        return "Ошибкапоказа истории"
    

def quiet_relog():
    login_input = session.state['login']
    pin = session.state['pin']

    resp = login(login_input, pin)
    if resp.get('status') == "ok":
        return resp
    else: return resp