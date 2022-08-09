import socket
import threading
import time




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




    def handle_client(self, client):
        while True:
            try:
                message = client.recv(1024)

            except:
                print("there is an error with ", client)
                break

    def broadcast(self, message):
        for client in self.clients:
            client.send(message)

    

    def run(self):
        print('Server is starting ...')
        while True:
            if self.current_uid == self.max_uid:
                time.sleep(3)
                self.broadcast("GAMESTART".encode('utf-8'))

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

        





if __name__ == "__main__":
    game_server = DrawGameServer(59000,3)
    game_server.run()
    # run()