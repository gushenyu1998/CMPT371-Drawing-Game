import json
import random
import socket
import threading
import time
from fnmatch import fnmatch

import pygame as pg
import math
from pygame.locals import *
import numpy as np
from multiprocessing import Process

Client_UID = 1
color = (0, 0, 0)
map_cell = 10
cell_pixel_length = 60
color_list = [(255, 255, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]

TCP_Port = 12005
server_host = 'localhost'

draw_data = []
UID_list = [0, 1, 2, 3, 4]
current_picture = np.zeros((600, 600), dtype=int)
lock_list = np.ones((10, 10), dtype=int)

time_sleep = 3


def delete_list_duplicate():
    global draw_data
    if draw_data is None:
        draw_data = []
    draw_data = [dict(t) for t in set([tuple(d.items()) for d in draw_data])]


def client_update(cell=None, islock=True):
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
        temp = UID_list.count(UID)
        Players.append(temp / 360000)
    return Players


def check_win():
    p = game_check()
    nth_player = 0
    for temp in p:
        if temp >= 0.5:
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
                            if lock_list[int(x_axis / 60)][int(y_axis / 60)]:
                                pg.draw.circle(self.screen, self.color, (x_axis, y_axis), 1)
                                message = {'UID': Client_UID, 'draw_record': (int(x_axis), int(y_axis)), 'more': True}
                                draw_data.append(message)

        self.last_position = position


class Painter:
    def __init__(self, Sock):
        pg.display.set_caption("Test Test Test")
        self.window = (600, 700)
        self.clock = pg.time.Clock()
        self.screen = pg.display.set_mode(self.window, 0, 32)
        self.brush = Brush(self.screen)
        self.paint_size = 10
        self.sock = Sock

    def run(self):
        self.screen.fill((255, 255, 255))
        self.draw_game_line()
        print("Thread painter start")
        while True:
            self.clock.tick(600)
            for event in pg.event.get():
                if event.type == QUIT:
                    exit()
                elif event.type == MOUSEBUTTONDOWN or \
                        event.type == MOUSEMOTION or \
                        event.type == MOUSEBUTTONUP:
                    self.paint_judgement(position=event.pos, event_type=event.type)
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
        if event_type == MOUSEBUTTONDOWN:
            self.brush.start(position)
            message = {'UID': Client_UID, 'draw_record': position, 'more': True}
            draw_data.append(message)
        elif event_type == MOUSEMOTION:
            self.brush.Draw(position)
        elif event_type == MOUSEBUTTONUP:
            self.brush.close()
            message = {'UID': Client_UID, 'draw_record': position, 'more': False}
            delete_list_duplicate()
            for i in range(10):
                draw_data.append(message)
            print("mouse up triggered: \n", lock_list)

            self.sending_data()

    def sending_data(self):
        while len(draw_data) != 0:
            message = draw_data.pop()
            sending = json.dumps(message)
            string = str(sending) + ';'
            self.sock.send(string.encode())
        return

    def receive_data(self):
        data = self.sock.recv(10240).decode()
        data_stock = data.split(';;')
        while len(data_stock) != 0:
            data_js = data_stock.pop()
            if fnmatch(str(data_js), '{"index": *, "islock": *, "loc": *}'):
                data_json = json.loads(data_js)
                client_update(data_json)
                self.Draw_update(current_picture)
        pass


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

    def run(self):

        global color
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        self.Painter.run()

    def Paint_run(self):
        pass

    def receiver_run(self):
        pass


if __name__ == '__main__':
    proccess = []

    app = TCP_client()
    app.run()
    # p2 = Process(target=server.server())
    # print('test')
    # p1 = Process(target=app.run())
    # p1.start()
    #
    # p1.join()
    # p2.join()

    # ink = []
    # map = Map.Map(map_cell, cell_pixel_length, 4)
    # for i in range(600):
    #     for j in range(600):
    #         ran = random.randint(0, 1)
    #         ink.append(Pixcel.Pixcel(ran, time.time(), False, False, i, j, True))
    # ink[-1] = Pixcel.Pixcel(0, time.time(), False, False, 599, 599, False)
    # map.draw(ink)
    # map_temp = map.readWholeMap()
    # k = 0
    #
    # map_a = np.zeros((600, 600), dtype=int)
    # for i in range(600):
    #     for j in range(600):
    #         map_a[i][j] = map_temp[0][k]['UID']
    #         k += 1
    #
    # color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    # app = Painter()
    # app.run()

    # temp = []
    # with open('../yaml_test.yaml','r') as f:
    #     temp = yaml.load(f.read())
    #     print(temp[0])
