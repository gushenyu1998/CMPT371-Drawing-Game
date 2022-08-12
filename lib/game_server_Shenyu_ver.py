import json
import socket
import threading
import time
import queue
import traceback
from fnmatch import fnmatch
import numpy as np


class DrawGameServer:
    def __init__(self, port, players):
        self.port = port
        self.host = '127.0.0.1'

        self.clients = []
        self.clients_address = []

        self.current_uid = 1
        self.max_uid = players + 1
        self.uids = []

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, port))
        self.server.listen()

        self.receive_drawing_queue = queue.Queue()
        # self.map_send_queue = queue()

        self.map = np.zeros((40, 40), dtype=int)
        self.lock_list = np.zeros((8, 8), dtype=int)

        self.lock = threading.Lock()
        self.last_message = ""

    def handle_client(self, client):
        while True:
            try:
                while True:
                    self.client_recever(client)
            except Exception as e:
                # print("there is an error, detail: ", repr(e))
                break

    def client_recever(self, client):
        while True:
            try:
                while True:
                    data = client.recv(1024).decode()
                    data_stock = data.split(';')
                    if len(data_stock) != 0:
                        temp = data_stock[0] + self.last_message
                        data_stock.insert(0, temp)
                    while len(data_stock) != 0:
                        data_js = data_stock.pop()
                        if fnmatch(str(data_js), '{"UID": *, "draw_record": *, "more": *}'):
                            data_json = json.loads(data_js)
                            self.lock.acquire()
                            self.receive_drawing_queue.put(data_json)
                            self.lock.release()
            except Exception as e:
                print("Client handel exception", repr(e))
                break

    def broadcast(self, message):
        for client in self.clients:
            client.send(message)

    def negotiateUID(self):
        while True:
            # have enough play, send start game and exit the function 
            if self.current_uid == self.max_uid:
                time.sleep(3)
                self.broadcast("GAMESTART;;GAMESTART;;GAMESTART".encode('utf-8'))
                print("Negotiate UID finish.")
                return

            client, address = self.server.accept()
            print("New player from: ", str(address))

            new_play_uid = self.current_uid
            self.uids.append(new_play_uid)
            self.current_uid += 1

            print("Assign uid", new_play_uid)

            send_uid_data = ';;{"PID": ' + str(new_play_uid) + '};;'
            for i in range(2):
                client.send(send_uid_data.encode('utf-8'))

            self.clients.append(client)
            self.clients_address.append(address)

            thread = threading.Thread(target=self.handle_client, args=(client,))
            thread.start()

    def broadcast_map(self):
        '''
        Refresh the map every 10 seconds
        :return:
        '''
        while True:
            time.sleep(10)
            # refresh the map every 10 seconds
            for i in range(40):
                for j in range(40):
                    message = {"UID": int(self.map[i][j]), "loc": (i, j)}
                    sending = json.dumps(message) + ";;"
                    self.broadcast(sending.encode())
            # refresh the locklist every 10 seoncds
            for i in range(40):
                for j in range(40):
                    message = {"islock": int(self.lock_list[i][j]), "loc": (i, j)}
                    sending = json.dumps(message) + ";;"
                    self.broadcast(sending.encode())

    def pixel_proccess(self):
        while True:
            try:
                data_json = self.receive_drawing_queue.get()  # pull a data from the queue
                UID = data_json['UID']
                if data_json['more']:
                    x = data_json['draw_record'][0]
                    y = data_json['draw_record'][1]
                    if x >= 40 or y >= 40 or x < 0 or y < 0:  # file the data, and prune the index out of range
                        continue
                    if self.map[x][y] != 0:
                        continue
                    elif self.lock_list[int(x / 5)][int(y / 5)] != 0 and \
                            self.lock_list[int(x / 5)][int(y / 5)] != UID:  # prune the pixel inside the lock list
                        continue
                    else:
                        sending_pixel = {"UID": UID, "loc": (x, y)}
                        # once receive a pixel, broadcast it to let other client update the map
                        message_pixel = json.dumps(sending_pixel) + ";;"
                        self.broadcast(message_pixel.encode())
                        sending_lock = {"Lock": UID, "loc": (int(x / 5), int(y / 5))}
                        message_lock = json.dumps(sending_lock) + ";;"
                        self.broadcast(message_lock.encode())
                        self.map[x][y] = UID
                        self.lock_list[int(x / 5)][int(y / 5)] = UID
                        # update the inside map and lock list
                        if self.cell_check(UID, (x, y)):
                            # once the map was checked as full-filled, broadcast the cell
                            self.cell_fill_out(UID, (x, y))
                            i = int(x / 5) * 5
                            j = int(y / 5) * 5
                            sending_pixel = {"UID_cell": UID, "loc": (i, j)}
                            message_pixel = json.dumps(sending_pixel) + ";;"
                            for i in range(5):
                                self.broadcast(message_pixel.encode())

                else:
                    # proccess the data that shows a user pull up his mouse button
                    UID_lock = np.where(self.lock_list == UID)
                    lock_row = list(UID_lock[0])
                    lock_col = list(UID_lock[1])
                    for i in range(len(lock_row)):
                        # release the cell with are not full-filled
                        if not self.cell_check(UID, (int(lock_row[i] * 5), int(lock_col[i] * 5))):
                            self.lock_list[lock_row[i]][lock_col[i]] = 0
                            self.cell_fill_out(0, (lock_row[i] * 5, lock_col[i] * 5))
                            sending_pixel = {"Lock": 0, "loc": (int(lock_row[i]), int(lock_col[i]))}
                            message_pixel = json.dumps(sending_pixel) + ";;"
                            for k in range(5):
                                self.broadcast(message_pixel.encode())
                            clean_cell = {"UID_cell": 0, "loc": (int(lock_row[i] * 5), int(lock_col[i] * 5))}
                            clean_message = json.dumps(clean_cell) + ";;"
                            for i in range(5):
                                self.broadcast(clean_message.encode())


            except Exception as e:
                print("Map running error: details", repr(e))
                traceback.print_exc()


    def cell_check(self, UID, position):
        '''
        check if a cell is full-filled
        :param UID: check by full filled by who
        :param position: target cell in the list
        :return: Ture if a cell is 50% full-filled
        '''
        p = position
        x = int(p[0] / 5) * 5
        y = int(p[1] / 5) * 5
        cell = self.map[x:x + 5, y:y + 5]
        temp = np.sum(cell == UID)
        if temp / 25 >= 0.5:
            return True
        else:
            return False

    def inGame(self):
        th3 = threading.Thread(target=self.pixel_proccess)
        th3.start()
        # th4 = threading.Thread(target=self.broadcast_map)
        # th4.start()
        # self.pixel_proccess()

    def cell_fill_out(self, UID, position):
        p = position
        x = int(p[0] / 5) * 5
        y = int(p[1] / 5) * 5
        for i in range(5):
            for j in range(5):
                self.map[x + i][y + j] = UID

    def run(self):
        print('Server is starting ...')
        self.negotiateUID()

        print('Game in running ...')
        self.inGame()


if __name__ == "__main__":
    game_server = DrawGameServer(9006, 2)
    game_server.run()
    # run()
