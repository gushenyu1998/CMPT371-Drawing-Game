from res.game_server_Shenyu_ver import *

if __name__ == "__main__":
    max_player = input("Please input how many players in this game: ")
    host = input("Please bind your ip for this game: ")
    game_server = DrawGameServer(str(host), 0, int(max_player))
    game_server.run()
