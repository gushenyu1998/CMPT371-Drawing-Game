import json
import socket
import sys
import threading
import time
import queue
from fnmatch import fnmatch
import numpy as np


class DrawGameServer:  # Making the GameServer ready to launch
    def __init__(self, host, port, players):
        self.port = port
        self.host = host

        self.clients = []
        self.clients_address = []

        self.current_uid = 1
        self.max_uid = players + 1
        self.uids = []

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, port))
        self.server.listen(5)

        self.receive_drawing_queue = queue.Queue()

        self.map = np.zeros((40, 40), dtype=int)
        self.lock_list = np.zeros((8, 8), dtype=int)

        self.lock = threading.Lock()
        self.last_message = ""

        self.threads = []

    def handle_client(self, client):
        while True:
            try:
                while True:
                    self.client_receiver(client)
            except Exception as e:
                print("there is an error, detail: ", repr(e))
                break

    def check_win(self):
        temp = np.sum(self.map == 0)
        Players = []
        if temp == 0:
            message = "CLOSEGAME;;CLOSEGAME;;CLOSEGAME;;"
            for UID in self.uids:
                temp = (np.sum(self.map == UID)) / 1600
                Players.append({'UID': UID, 'percentage': temp})
            new = sorted(Players, key=lambda k: k.__getitem__('percentage'))
            new.reverse()
            winner = new[0]
            winnner_json = json.dumps(winner)
            for i in range(3):
                message += winnner_json + ";;"
            self.broadcast(message.encode())
            self.server.close()
            print("exit game server")
            exit()

    def client_receiver(self, client):  # Connecting the clients with the server
        while True:
            try:
                while True:
                    data = client.recv(1024).decode()
                    if len(data) == 0:
                        print("client close")
                        client.close()
                        sys.exit(0)
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
                client.close()
                return

    def broadcast(self, message):  # communicating client with helpful game state messages
        for client in self.clients:
            client.send(message)

    def negotiateUID(self): # starts the after all the players are connected
        while True:
            # have enough players, send start game and exit the function
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

            send_uid_data = ';;{"PID": ' + str(new_play_uid) + ', "MAX": ' + str(self.max_uid - 1) + '};;'
            for i in range(2):
                client.send(send_uid_data.encode('utf-8'))

            self.clients.append(client)
            self.clients_address.append(address)

            thread = threading.Thread(target=self.handle_client, args=(client,))
            self.threads.append(thread)
            thread.start()

    def pixel_proccess(self):
        while True:
            try:
                self.check_win()
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
                exit()
                return

    def cell_check(self, UID, position):  # checks if a cell is filled enough to be acquired by a player
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
        self.threads.append(th3)
        th3.start()

    def cell_fill_out(self, UID, position):
        p = position
        x = int(p[0] / 5) * 5
        y = int(p[1] / 5) * 5
        for i in range(5):
            for j in range(5):
                self.map[x + i][y + j] = UID

    def run(self): # Initiates the server
        print('Server is starting ... number of player in this game is: ' + str(self.max_uid - 1))
        print("This server's IP address is:" + str(self.host) + " port number is: " + str(self.server.getsockname()[1]))
        self.negotiateUID()

        print('Game in running ...')
        self.inGame()
        for thread in self.threads:
            thread.join()
