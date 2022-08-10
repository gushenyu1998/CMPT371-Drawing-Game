import threading
import socket
import time
import json
from fnmatch import fnmatch

class DrawGameClient:
    def __init__(self, server_address, port):

        self.server_address = server_address
        self.port = port


        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


        self.client.connect((str(self.server_address), self.port))

        self.uid = None


    def client_receive(self):
        while True:
            try:
                message = self.client.recv(1024).decode('utf-8')
                print(message)
                if fnmatch(str(message),'{"PID": *}'):
                    PID_string = json.loads(message)
                    self.uid = PID_string["PID"]
                    print("Received UID = ", self.uid)

                    

            except:
                print('Error!')
                self.client.close()
                break


    def client_send(self, message):
        while True:
            self.client.send(message)

    def receiveThread(self):
        receive_thread = threading.Thread(target=self.client_receive)
        receive_thread.start()

    def sendTThread(self):
        send_thread = threading.Thread(target=self.client_send)
        send_thread.start()



    def runClient(self):
        print("Client starting ...")
        self.receiveThread()








if __name__ == "__main__":
    game_client = DrawGameClient("127.0.0.1", 59000)
    game_client.runClient()