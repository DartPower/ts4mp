import socket
import threading

import ts4mp
from ts4mp.debug.log import ts4mp_log
from ts4mp.core.mp_sync import outgoing_lock, outgoing_commands
from ts4mp.core.mp_sync import incoming_lock
from ts4mp.core.networking import generic_send_loop, generic_listen_loop
from ts4mp.core.csn import show_client_connect_on_server
from ts4mp.configs.server_config import SERVER_HOST, SERVER_PORT
from ts4mp.core.mp_sync import HeartbeatMessage
import time
class Server:
    def __init__(self):
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.host = SERVER_HOST
        self.port = SERVER_PORT
        self.alive = True
        self.serversocket.bind((self.host, self.port))
        self.clientsocket = None

    def listen(self):
        threading.Thread(target=self.listen_loop, args=[]).start()

    def send(self):
        threading.Thread(target=self.send_loop, args=[]).start()

    def send_loop(self):
        while self.alive:
            if self.clientsocket is not None:
                ts4mp_log("Messages", "Sending {} messages".format(len(outgoing_commands)))
                with outgoing_lock:
                    for data in outgoing_commands:
                        generic_send_loop(data, self.clientsocket)
                        outgoing_commands.remove(data)


            # time.sleep(1)


    def heartbeat(self):
        threading.Thread(target=self.heartbeat_loop, args=[]).start()

    def heartbeat_loop(self):
        while self.alive:
            if self.clientsocket is not None:
                outgoing_commands.append(HeartbeatMessage(time.time()))
            #send a heartbeat message every 100 milliseconds
            time.sleep(0.1)


    def listen_loop(self):
        self.serversocket.listen(5)
        self.clientsocket, address = self.serversocket.accept()
        show_client_connect_on_server()
        ts4mp_log("network", "Client Connect")

        clientsocket = self.clientsocket
        size = None
        data = b''

        while self.alive:
            new_command, data, size = generic_listen_loop(clientsocket, data, size)
            if new_command is not None:
                with incoming_lock:
                    ts4mp.core.mp_sync.incoming_commands.append(new_command)

    def kill(self):
        self.alive = False

