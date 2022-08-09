import socket
import threading
import os
import sys
import json
import time
from fnmatch import fnmatch

import numpy as np

TCP_PORT = 12005
host = 'localhost'

data_stock = []
data_example = []

def server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, TCP_PORT))
    s.listen(5)
    print('waiting for connection')

    def tcp_link(socket_thread = s, addr = None):
        print('Accept new connection from %s:%s' % addr)
        socket_thread.send('connect success!'.encode())
        BreakFlag = True

        ## 55 or others
        while BreakFlag:
            data = socket_thread.recv(1024).decode()
            data_stock = data.split(';')
            while len(data_stock) != 0:
                data_js= data_stock.pop()
                # print("\n\n\ndata_js",data_js)
                if fnmatch(str(data_js),'{"UID": *, "draw_record": *, "more": *}'):

                    # print("=================fnmatch\n")
                    # return
                    data_json = json.loads(data_js)
                    data_example.append(data_json)
                    print(data_json['more'])
                    if not data_json['more']:
                        with open('../json_file_example','w') as f:
                            f.write(str(data_example))
                        BreakFlag = False
        socket_thread.close()
        print('Connection from %s:%s closed.' % addr)


    sock, addr = s.accept()
    tcp_link(sock, addr)

if __name__ == '__main__':
    server()
    #print(len('{"UID": 1, "draw_record": [287, 233], "more": true}'))









