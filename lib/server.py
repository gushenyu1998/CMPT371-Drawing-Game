import socket
import threading
import os
import sys
import json
import time
from fnmatch import fnmatch

import Pixcel
import Map
import random
import numpy as np

TCP_PORT = 59000
host = 'localhost'

data_stock = []
data_example = []


def server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, TCP_PORT))
    s.listen(5)

    print('waiting for connection')

    def tcp_link(socket_thread=s, addr=None):
        print('Accept new connection from %s:%s' % addr)
        socket_thread.send('connect success!'.encode())
        while True:
            for i in range(2500):
                a = {"index": i, "loc": [random.randint(0, 4)]}
                send = json.dumps(a)+";;"
                socket_thread.send(send.encode())
            for i in range(2500):
                a = {"index": i, "loc": [0]}
                send = json.dumps(a)+";;"
                socket_thread.send(send.encode())

    sock, addr = s.accept()
    tcp_link(sock, addr)


if __name__ == '__main__':
    for i in range(-1,2): print(i)
    # print(len('{"UID": 1, "draw_record": [287, 233], "more": true}'))
