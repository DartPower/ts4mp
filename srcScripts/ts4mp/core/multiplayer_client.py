import socket
import threading

import ts4mp
import ts4mp.core.mp
from ts4mp.debug.log import ts4mp_log, Timer
from ts4mp.core.mp_sync import outgoing_lock, outgoing_commands
from ts4mp.core.networking import generic_send_loop, generic_listen_loop
from ts4mp.configs.server_config import HOST, PORT
from ts4mp.core.mp_sync import incoming_lock
from ts4mp.core.csn import show_client_connect_on_client, show_client_connection_failure
import time
class Client:
    def __init__(self):
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.serversocket.settimeout(5)
        self.host = 0
        self.port = 0
        self.alive = True
        self.connected = False
        self.ever_recieved_data = False
    def listen(self):
        threading.Thread(target=self.listen_loop, args=[]).start()

    def send(self):
        threading.Thread(target=self.send_loop, args=[]).start()

    def send_loop(self):
        try:
            self.serversocket.connect((self.host, self.port))
            self.connected = True

            while self.alive:

                with outgoing_lock:
                    with Timer("send network time"):
                        for data in outgoing_commands:
                            generic_send_loop(data, self.serversocket)
                            outgoing_commands.remove(data)

                # time.sleep(1)
        except Exception as e:
            show_client_connection_failure()
            ts4mp_log("sockets", str(e))

            self.connected = False

    def listen_loop(self):
        serversocket = self.serversocket
        size = None
        data = b''
        while self.alive:
            if self.connected:
                try:
                    new_command, data, size = generic_listen_loop(serversocket, data, size)
                    if new_command is not None:
                        if not self.ever_recieved_data:
                            show_client_connect_on_client()

                            ts4mp.core.mp.on_successful_client_connect()
                            self.ever_recieved_data = True
                        with incoming_lock:
                            ts4mp.core.mp_sync.incoming_commands.append(new_command)
                except socket.error as e:
                    ts4mp_log("sockets", "Catastrophic failure: {}".format(e))

                    show_client_connection_failure()
                    self.connected = False


            # time.sleep(1)

    def kill(self):
        self.alive = False
