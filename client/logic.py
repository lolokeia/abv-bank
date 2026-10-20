from client import session
from shared import protocol, comms, codes
import tabulate


def _send_n_recv(action, data=None, _retry=True):
    sock = session.state["sock"]
    if sock is None:
        return comms.error(code=codes.CONNECTION_NO)
    
    req = comms.request(action=action, data=data)
    token = session.state.get('token')
    try:
        if token:
            req['token'] = token
        protocol.send_message(message=req, sock=session.state["sock"])
    except Exception as e:
        return comms.error(code='send.error', data={"e": e})
    
    try:
        resp = protocol.recv_message(sock=session.state["sock"])
    except Exception as e:
        return comms.error(code='recv.error', data={"e": e})

    
    if resp.get('code') == codes.SESSION_EXPIRED and _retry:
        relog = quiet_relog()
        if relog.get('status') != 'ok':
            return relog
        return _send_n_recv(action, data, _retry=False)
    
    return resp







def get_current_acc():
    return session.state['current_acc']

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
        history = get_his['data'].get('history')
        if history is None:
            return "История пуста"
        return tabulate.tabulate(
            history,
            headers=["Тип", "Сумма", "Баланс", "Описание", "Дата"])
    else: 
        return "Ошибка показа истории"
    

def quiet_relog():
    login_input = session.state['login']
    pin = session.state['pin']

    resp = login(login_input, pin)
    if resp.get('status') == "ok":
        return resp
    else: return resp