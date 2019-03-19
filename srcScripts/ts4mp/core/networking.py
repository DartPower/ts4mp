import pickle
import sys
from struct import unpack, pack

from ts4mp.debug.log import ts4mp_log


def generic_send_loop(data, socket):
    data = pickle.dumps(data)
    length = pack('>Q', sys.getsizeof(data))

    socket.sendall(length)
    socket.sendall(data)
    #ts4mp_log("send", "Sending {} bytes of data".format(sys.getsizeof(data)))


def generic_listen_loop(socket, data, size):
    new_command = None
    if size is None:
        size = socket.recv(8)
        (size,) = unpack('>Q', size)
        size = int(size)
    elif size > sys.getsizeof(data):
        bytes_to_receive = size - sys.getsizeof(data)
        new_data = socket.recv(bytes_to_receive)
        data += new_data
    elif size == sys.getsizeof(data):
        #ts4mp_log("receive", "Received new command with {} bytes of data".format(sys.getsizeof(data)))

        data = pickle.loads(data)

        new_command = data


        size = None
        data = b''

    return new_command, data, size
