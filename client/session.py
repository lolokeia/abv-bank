import threading

state = {
    'running': True,
    'conn': False,
    'sock': None,
    'sock_lock': threading.Lock(),
    'token': None,
    'login': None,
    'name': None,
    'pin': None,
    'accounts': {},
    'current_acc': None,
    'last_error': None,
    'lang': {},
    'conn_tries': 0
    }

