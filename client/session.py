import threading

settings = {
    'ip': None,
    'port': None,
    'language': None,
    'wd_timeout': None,
    'wd_tick': None,
    'wd_max_missed_pings': None,
    'debug': None
}

runtime = {
    #main
    'running': True,

    #net
    'sock': None,
    'sock_lock': threading.Lock(),
    'ping_stat': False,
    'pings': 0,
    'conn_tries': 0,
    'conn': False,
    'need_restart': False,


    #auth
    'token': None,
    'login': None,
    'name': None,
    'pin': None,
    'accounts': {},
    'current_acc': None,


    # UI
    'last_error': None,
    'retry_btn': None,
    'loading_msg': '',
    'aquire': threading.Event(),
    'snapshot': {},
    'prev_screen': None,
    }

defaults = {
    'ip': "127.0.0.1",
    'port': 9999,
    'language': 'ru_ru',
    'wd_timeout': 14,
    'wd_tick': 0.5,
    'wd_max_missed_pings': 2,
    'debug': False
}

lang = {"lang": {}}