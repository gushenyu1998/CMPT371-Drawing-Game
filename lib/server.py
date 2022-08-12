import socket
import threading
import os
import sys
import json
import time
from fnmatch import fnmatch

import numpy

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
            for i in range(50):
                for j in range(50):
                    a = {"UID": random.randint(1, 4), "loc": (i,j)}
                    send = json.dumps(a) + ";;"
                    socket_thread.send(send.encode())

            for i in range(50):
                for j in range(50):
                    a = {"UID": 0, "loc": (i, j)}
                    send = json.dumps(a) + ";;"
                    socket_thread.send(send.encode())
                    time.sleep(0.001)



    sock, addr = s.accept()
    tcp_link(sock, addr)


if __name__ == '__main__':
    server()
    # a = numpy.zeros((10,10),dtype=int)
    # k = 1
    # for i in range(10):
    #     for j in range(10):
    #         a[i][j] = k
    #         k+=1
    # cell = a[0:5, 0:5]
    # a[5::7, 5::7] = 13
    # a[6][6] = 13
    # print(a)
    # print(a[5:7][5:7])
    # print(len('{"UID": 1, "draw_record": [287, 233], "more": true}'))
