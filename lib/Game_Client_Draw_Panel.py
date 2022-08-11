import json
import math
import socket
import threading
import time
from fnmatch import fnmatch
import numpy as np
import pygame as pg
from pygame.locals import *

Client_UID = 1
color = (0, 0, 0)
map_cell = 10
cell_pixel_length = 60
color_list = [(255, 255, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]

TCP_Port = 59000
server_host = 'localhost'

draw_data = []
UID_list = [0, 1, 2, 3, 4]
current_picture = np.zeros((600, 600), dtype=int)
lock_list = np.ones((10, 10), dtype=int)

text_game = "Your color is: {}\n"
player1 = "first player is: Player{}, {}"
player2 = "Second player is: Player{}, {}"
player3 = "Third player is: Player{}, {}"
player4 = "Last player is: Player{}, {}"


def delete_list_duplicate():
    global draw_data
    if draw_data is None:
        draw_data = []
    draw_data = [dict(t) for t in set([tuple(d.items()) for d in draw_data])]


def client_update(cell=None):
    if cell is not None:
        x_axis = (cell['index'] % 10) * 60
        y_axis = int(cell['index'] / 10) * 60
        k = 0
        for i in range(60):
            for j in range(60):
                current_picture[x_axis + i][y_axis + j] = cell['loc'][k]
                lock_list[int(x_axis / 60)][int(y_axis / 60)] = cell['islock']
                k += 1


def game_check():
    Players = []
    for UID in UID_list:
        if UID == 0:
            continue
        temp = (np.sum(current_picture == UID)) / 360000
        Players.append({'UID': UID, 'percentage': temp})
    # test = [{'UID': 1, 'percentage': 0.1},
    #         {'UID': 2, 'percentage': 0.2},
    #         {'UID': 3, 'percentage': int(time.time())},
    #         {'UID': 4, 'percentage': 0.3}]
    new = sorted(Players, key=lambda k: k.__getitem__('percentage'))
    return new


def check_win():
    p = game_check()
    nth_player = 0
    for temp in p:
        if temp['percentage'] >= 0.5:
            return True, nth_player
        nth_player += 1
    return False, 0


class Brush(object):
    def __init__(self, screen):
        self.color = color
        self.screen = screen
        self.drawing = False
        self.size = 50
        self.last_position = None
        self.last_color = (0, 0, 0)
        self.pencil = True

    def start(self, position):
        self.drawing = True
        self.last_position = position

    def close(self):
        self.drawing = False

    def set_size(self, size):
        if size > 50:
            size = 50
        elif size < 1:
            size = 1
        self.size = size

    def get_line(self, position):
        lenx = position[0] - self.last_position[0]
        leny = position[1] - self.last_position[1]
        length = math.sqrt(lenx ** 2 + leny ** 2)
        if length <= 0:
            length = 1
        cosx = lenx / length
        sinx = leny / length
        points = []
        for i in range(int(length)):
            points.append((self.last_position[0] + i * cosx, self.last_position[1] + i * sinx))
        points.append((self.last_position[0] + length * cosx, self.last_position[1] + length * sinx))
        return points

    def Draw(self, position):
        paint_broad = 5
        if self.drawing:
            for p in self.get_line(position):
                for x in range(-paint_broad, paint_broad):
                    for y in range(-paint_broad, paint_broad):
                        if abs(x) + abs(y) <= paint_broad:
                            x_axis = p[0] + x
                            y_axis = p[1] + y
                            if lock_list[int(x_axis / 60) - 3][int(y_axis / 60) - 3]:
                                pg.draw.circle(self.screen, self.color, (x_axis, y_axis), 1)
                                message = {'UID': Client_UID, 'draw_record': (int(x_axis), int(y_axis)), 'more': True}
                                draw_data.append(message)

        self.last_position = position


class Painter:
    def __init__(self, Sock):
        pg.display.set_caption("Test Test Test")
        self.window = (600, 800)
        self.clock = pg.time.Clock()
        self.screen = pg.display.set_mode(self.window, 0, 32)
        self.brush = Brush(self.screen)
        self.paint_size = 10
        self.sock = Sock

    def run(self):
        pg.init()
        self.screen.fill((255, 255, 255))
        self.draw_game_line()

        while True:
            self.clock.tick(600)
            for event in pg.event.get():
                if event.type == QUIT:
                    exit()
                elif event.type == MOUSEBUTTONDOWN or \
                        event.type == MOUSEMOTION or \
                        event.type == MOUSEBUTTONUP:
                    self.paint_judgement(position=event.pos, event_type=event.type)
            self.text_update()
            if len(draw_data) > 10240:
                delete_list_duplicate()
                self.sending_data()
            pg.display.update()

    def draw_game_line(self):
        block_x = 60
        block_y = 60
        for i in range(11):
            pg.draw.line(self.screen, (0, 0, 0), (i * block_y, 0), (i * block_y, 600), 3)
        for j in range(11):
            pg.draw.line(self.screen, (0, 0, 0), (0, j * block_x), (600, j * block_x), 3)

    def Draw_update(self, map=None):
        if map is not None:
            for i in range(600):
                for j in range(600):
                    pg.draw.rect(self.screen, color_list[map[i][j]], (i, j, 1, 1))
        self.draw_game_line()

    def paint_judgement(self, position, event_type):
        if position[0] <= 600 or position[1] <= 600:
            if event_type == MOUSEBUTTONDOWN:
                self.brush.start(position)
                message = {'UID': Client_UID, 'draw_record': position, 'more': True}
                draw_data.append(message)
            elif event_type == MOUSEMOTION:
                self.brush.Draw(position)
            elif event_type == MOUSEBUTTONUP:
                self.brush.close()
                message = {'UID': Client_UID, 'draw_record': (min(position[0], 600), min(position[1], 600)),
                           'more': False}
                delete_list_duplicate()
                for i in range(10):
                    draw_data.append(message)
                self.sending_data()

    def sending_data(self):
        while len(draw_data) != 0:
            message = draw_data.pop()
            sending = json.dumps(message)
            string = str(sending) + ';'
            self.sock.send(string.encode())
        return

    def text_update(self):
        rect = pg.Surface((600, 200))
        rect.fill((255, 255, 255))
        self.screen.blit(rect, (0, 600))
        game_proccess = game_check()

        game_text1 = player1.format(game_proccess[0]['UID'], game_proccess[0]['percentage'])
        font_t = pg.font.SysFont('arial', 30)
        text = font_t.render(game_text1, True, (0, 0, 0))
        self.screen.blit(text, (20, 620))

        game_text2 = player2.format(game_proccess[1]['UID'], game_proccess[1]['percentage'])
        font_t = pg.font.SysFont('arial', 30)
        text = font_t.render(game_text2, True, (0, 0, 0))
        self.screen.blit(text, (20, 660))

        game_text3 = player3.format(game_proccess[2]['UID'], game_proccess[2]['percentage'])
        font_t = pg.font.SysFont('arial', 30)
        text = font_t.render(game_text3, True, (0, 0, 0))
        self.screen.blit(text, (20, 700))

        game_text4 = player4.format(game_proccess[3]['UID'], game_proccess[3]['percentage'])
        font_t = pg.font.SysFont('arial', 30)
        text = font_t.render(game_text4, True, (0, 0, 0))
        self.screen.blit(text, (20, 740))


class TCP_client:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((server_host, TCP_Port))
        connection = self.sock.recv(1024).decode()
        print(connection)
        if len(connection) != 0:
            self.Painter = Painter(self.sock)
        else:
            print('connection not success')
            return

    def get_painter(self):
        return self.Painter

    def client_draw_panel(self, a = None):
        self.Painter.run()

    def receive_message(self):
        while True:
            data_stock = []
            try:
                data = self.sock.recv(1024).decode()
                data_stock = data.split(';;')
            except Exception as e:
                print('receive message error, detail:', repr(e))
                self.sock.close()
            while len(data_stock) != 0:
                data_js = data_stock.pop()
                if fnmatch(str(data_js), '{"index": *, "islock": *, "loc": *}'):
                    data_json = json.loads(data_js)
                    # client_update(data_json)
                    # self.Painter.Draw_update(current_picture)
                    print(data_json)

    def build_player(self):
        try:
            loop_time_out = 1000
            global Client_UID
            global color
            while loop_time_out >= 0:
                loop_time_out -= 1
                time.sleep(0.1)
                try:
                    data = self.sock.recv(125).decode()
                finally:
                    print("Building Client......")
                data_stock = data.split(';;')
                while len(data_stock) != 0:
                    data_js = data_stock.pop()
                    if fnmatch(str(data_js), '{"PID": *}'):
                        data_json = json.loads(data_js)
                        Client_UID = data_json['PID']
                        color = color_list[Client_UID]
                        print("Build Client Success......., ")
                        print("Client UID is {}, color is: {}".format(Client_UID,color))
                        for i in range(100):
                            self.sock.send("{'UID': 1, 'draw_record': [344, 247], 'more': False}")
                        return

        except:
            print('Build client error')

    # def sender_test(self):
    #     while True:
    #         time.sleep(0.1)
    #         try:
    #             self.sock.send('{"UID":1,"draw_record":(10,10),"more":False};'.encode())
    #             print('{"UID": 1,"draw_record": (10,10),"more": False};')
    #         except Exception as e:
    #             print(repr(e))

    def run(self):
        self.build_player()
        th1 = threading.Thread(target=self.receive_message)
        th2 = threading.Thread(target=self.Painter.run(), args=(self.Painter,))
        th1.start()
        th2.start()
        th1.join()
        th2.join()


def client_run_proccess():
    time.sleep(1)
    app = TCP_client()
    app.run()

if __name__ == '__main__':
    client_run_proccess()