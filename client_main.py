from client import logic
import socket
from client import session
import time

def connect_to_server(host="127.0.0.1", port=9999):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    session.state['sock'] = sock
    return sock

if not session.state['sock']:
    sock = connect_to_server()
    session.state['sock'] = sock

login_input = 'bebebe'
pin_input = '0000'

login_msg = logic.register(login_input, 'илья', pin_input)
session.state["login"] = login_input
session.state["pin"] = pin_input

if login_msg.get('status') == 'ok':
    session.state['token'] = login_msg['data'].get('token')
else:
    print("Логин не удался:", login_msg.get('message'))

print(login_msg.get('token'))
print(login_msg)
print(logic.deposit(1000))
# print(logic.payment())
# print(logic.payment(10))
# print(logic.withdraw(100))
# print(logic.transfer('olo', 100))
# print(logic.get_balance())
# print(logic.get_history())
# print("")
# print("")
# print(logic.format_history())
# print("")
# print("")
# print(logic.burn('1111'))
# timer = 65

# while timer > 0:
#     timer -= 1
#     print(str(timer) + '                         ', end="\r", flush=True)
#     time.sleep(1)


# print(logic.deposit(10000))
# print(logic.burn('1111'))


# print(logic.deposit(1000))
# print(logic.burn('1111'))

# print("")
# print("")
# print(logic.format_history())
# print("")
# print("")

print(logic.logout())