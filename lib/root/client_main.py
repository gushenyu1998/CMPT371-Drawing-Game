from res.Game_Client_Draw_Panel import *

if __name__ == '__main__':
    host = input("Please input your room IP or domain: ")
    server_host = str(host)
    port = input("Please input your room port number: ")
    TCP_Port = int(port)
    connection_setter(server_host, TCP_Port)
    client_run_proccess()
