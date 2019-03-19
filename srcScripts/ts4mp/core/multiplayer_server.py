import socket
import threading

import ts4mp
from ts4mp.debug.log import ts4mp_log
from ts4mp.core.mp_sync import outgoing_lock, outgoing_commands
from ts4mp.core.mp_sync import incoming_lock
from ts4mp.core.networking import generic_send_loop, generic_listen_loop
from ts4mp.core.csn import show_client_connect_on_server
from ts4mp.core.mp_sync import HeartbeatMessage
from ts4mp.core.csn import show_unsuccessful_server_host

import time
class Server:
    def __init__(self):
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.serversocket.settimeout(15)

        self.host = "localhost"
        self.port = 9999
        self.alive = True
        self.serversocket.bind((self.host, self.port))
        self.clientsocket = None

    def listen(self):
        threading.Thread(target=self.listen_loop, args=[]).start()

    def send(self):
        threading.Thread(target=self.send_loop, args=[]).start()

    def send_loop(self):
        while self.alive:
            messages_sent = 0
            if self.clientsocket is not None:
                ts4mp_log("Messages", "Sending {} messages".format(len(outgoing_commands)))
                with outgoing_lock:
                    for data in outgoing_commands:
                        generic_send_loop(data, self.clientsocket)
                        outgoing_commands.remove(data)
                        messages_sent += 1
                        if messages_sent >= 100:
                            break
                time.sleep(0.2)



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
        try:
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
        except socket.error as e:
            show_unsuccessful_server_host()
            ts4mp_log("sockets", str(e))
            self.alive = False
            self.serversocket.shutdown(socket.SHUT_RDWR)
            self.serversocket.close()
    def kill(self):
        self.alive = False

