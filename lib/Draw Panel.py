import json
import random
import socket
import threading
import time

import pygame as pg
import math
from pygame.locals import *
import numpy as np

from lib import server

from multiprocessing import Process

Client_UID = 1
color = (0, 0, 0)
map_cell = 10
cell_pixel_length = 60

TCP_Port = 12005
server_host = 'localhost'

draw_data = []
current_picture = []
lock_list = np.ones((map_cell * cell_pixel_length, map_cell * cell_pixel_length), dtype=int)

time_sleep = 3


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
        if self.drawing:
            for p in self.get_line(position):
                pg.draw.circle(self.screen, self.color, p, 5)
        self.last_position = position


class Painter:
    def __init__(self, Sock):
        pg.display.set_caption("Test Test Test")
        self.window = (600, 700)
        self.clock = pg.time.Clock()
        self.screen = pg.display.set_mode(self.window, 0, 32)
        self.brush = Brush(self.screen)
        self.map = None
        self.paint_size = 10
        self.sock = Sock

    def run(self):
        self.screen.fill((255, 255, 255))
        self.game_init()
        # self.game_update()
        print("Thread painter start")
        while True:
            self.clock.tick(10)
            for event in pg.event.get():
                if event.type == QUIT:
                    exit()
                elif event.type == MOUSEBUTTONDOWN or \
                        event.type == MOUSEMOTION or \
                        event.type == MOUSEBUTTONUP:
                    self.paint_judgement(position=event.pos, event_type=event.type)
            if len(draw_data) > 200:
                while len(draw_data) != 0:
                    message = draw_data.pop()
                    sending = json.dumps(message)
                    string = str(sending)+';'
                    self.sock.send(string.encode())
            pg.display.update()

    def game_init(self):
        block_x = 60
        block_y = 60

        # if self.map is not None:
        #     for i in range(600):
        #         for j in range(600):
        #             if self.map[i][j] == 1:
        #                 pg.draw.rect(self.screen, (255, 0, 0), (i, j, 1, 1))

        for i in range(11):
            pg.draw.line(self.screen, (0, 0, 0), (i * block_y, 0), (i * block_y, 600), 3)
        for j in range(11):
            pg.draw.line(self.screen, (0, 0, 0), (0, j * block_x), (600, j * block_x), 3)

    def game_update(self):
        if self.map is not None:
            for i in range(600):
                for j in range(600):
                    if self.map[i][j] == 1:
                        pg.draw.rect(self.screen, (255, 0, 0), (i, j, 1, 1))
                    elif self.map[i][j] == 2:
                        pg.draw.rect(self.screen, (0, 255, 0), (i, j, 1, 1))

    def paint_judgement(self, position, event_type):
        paint_broad = int(self.paint_size / 2)
        for x in range(-paint_broad, paint_broad):
            for y in range(-paint_broad, paint_broad):
                x_axis = position[0] + x
                y_axis = position[1] + y
                if 1 < x_axis < 599 and 1 < y_axis < 599 and lock_list[x_axis][y_axis] == True:
                    if event_type == MOUSEBUTTONDOWN:
                        self.brush.start((x_axis, y_axis))
                        message = {'UID': Client_UID, 'draw_record': (x_axis, y_axis), 'occupied': True}
                        draw_data.append(message)
                        return
                    elif event_type == MOUSEMOTION:
                        self.brush.Draw((x_axis, y_axis))
                        if self.brush.drawing:
                            message = {'UID': Client_UID, 'draw_record': (x_axis, y_axis), 'occupied': True}
                            draw_data.append(message)
                    elif event_type == MOUSEBUTTONUP:
                        self.brush.close()
                        message = {'UID': Client_UID, 'draw_record': (x_axis, y_axis), 'occupied': False}
                        draw_data.append(message)
                        return


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
