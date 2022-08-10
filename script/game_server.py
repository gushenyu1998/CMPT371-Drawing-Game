import json
import socket
import threading
import time
from fnmatch import fnmatch

from lib.Map import Map
from lib.Map import Pixcel

import queue





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

        self.receive_drawing_queue = queue()
        self.map_send_queue = queue()

        # self.receiveBUffer




    def handle_client(self, client):
        while True:
            try:
                # message = client.recv(1024)


                while True:
                    time.sleep(1)
                    message = "hi"
                    client.send(message.encode('utf-8'))


            except:
                print("there is an error with ", client)
                break

    def client_recever(self, client):
        receive_data = ""
        while True:
            try:
                # message = client.recv(1024)
                ######
                while True:
                    data = client.recv(1024).decode()
                    data_stock = data.split(';')
                    while len(data_stock) != 0:
                        data_js= data_stock.pop()
                        # print("\n\n\ndata_js",data_js)
                        if fnmatch(str(data_js),'{"UID": *, "draw_record": *, "more": *}'):

                            # print("=================fnmatch\n")
                            # return
                            data_json = json.loads(data_js)
                            receive_data.append(data_json)
                            print(data_json['more'])
                            if not data_json['more']:




                                self.receive_drawing_queue.put(receive_data)
                                receive_data = ""

                                # BreakFlag = False



                #####




            except:
                print("there is an error with ", client)
                break

    def broadcast(self, message):
        for client in self.clients:
            client.send(message)


    def negotiateUID(self):
        while True:
            if self.current_uid == self.max_uid:
                time.sleep(3)
                self.broadcast("GAMESTART".encode('utf-8'))
                print("Negotiate UID finish.")
                return

            client, address = self.server.accept()
            print("New player from: ", str(address))

            '''{'UID': 1}'''
            new_play_uid = self.current_uid
            self.uids.append(new_play_uid)
            self.current_uid += 1

            print("Assign uid", new_play_uid)

            send_uid_data = '{"PID": ' + str(new_play_uid) +'}'
            client.send(send_uid_data.encode('utf-8'))



            self.clients.append(client)
            self.clients_address.append(address)


            thread = threading.Thread(target=self.handle_client, args=(client,))
            thread.start()
    
    def inGame(self):
        map = Map.Map(10,60,10)

        drop_queue_red_line = 10000



        switch = True
        while True:
            # alternately draw and send
            if switch:
                switch = not switch
                # empty receive queue
                loop_counter = 0
                while not self.receive_drawing_queue.empty():

                    map.drawJSON(self.receive_drawing_queue.get())
                    if (loop_counter >= drop_queue_red_line):
                        self.receive_drawing_queue = queue()
                        #need to add forch to judge map
                        break
                    loop_counter += 1

            else:
                switch = not switch

    

    def run(self):
        print('Server is starting ...')
        self.negotiateUID()


        





if __name__ == "__main__":
    game_server = DrawGameServer(59000,3)
    game_server.run()
    # run()