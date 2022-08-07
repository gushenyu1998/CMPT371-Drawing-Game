import random
import sys
import time

import pygame as pg
import math
from pygame.locals import *
from ruamel import yaml
import Map
import Pixcel
import numpy as np


color = (0, 0, 0)
map_cell = 10
cell_pixel_length = 60

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
                pg.draw.rect(self.screen, self.color, (p,(10,10)), self.size)
        self.last_position = position




class Painter:
    def __init__(self, map = None):
        pg.display.set_caption("Test Test Test")
        self.window = (600, 700)
        self.clock = pg.time.Clock()
        self.screen = pg.display.set_mode(self.window, 0, 32)
        self.brush = Brush(self.screen)
        self.map =map

    def run(self):
        tot = 1
        self.screen.fill((255, 255, 255))
        self.game_init()
        last_screen = []
        draw_data = []
        while True:
            self.clock.tick(60)
            for event in pg.event.get():
                if event.type == QUIT:
                    exit()
                elif event.type == MOUSEBUTTONDOWN:
                    if 0 <= event.pos[0] <= 600 and 600 >= event.pos[1] >= 0:
                        self.brush.start(event.pos)
                        draw_data.append(event.pos)
                elif event.type == MOUSEMOTION:
                    if 0 <= event.pos[0] <= 600 and 600 >= event.pos[1] >= 0:
                        self.brush.Draw(event.pos)
                        if self.brush.drawing:
                            draw_data.append(event.pos)
                elif event.type == MOUSEBUTTONUP:
                    self.brush.close()
            pg.display.update()
            print(draw_data)

    def game_init(self):
        block_x = 60
        block_y = 60

        if self.map is not None:
            for i in range(600):
                for j in range(600):
                    if self.map[i][j] == 1:
                        pg.draw.rect(self.screen, (255, 0, 0), (i, j, 1, 1))

        for i in range(11):
            pg.draw.line(self.screen, (0, 0, 0), (i * block_y, 0), (i * block_y, 600), 3)
        for j in range(11):
            pg.draw.line(self.screen, (0, 0, 0), (0, j * block_x), (600,  j * block_x), 3)

    def game_update(self):
        if self.map is not None:
            for i in range(600):
                for j in range(600):
                    if self.map[i][j] == 1:
                        pg.draw.rect(self.screen, (255, 0, 0), (i, j, 1, 1))
                    elif self.map[i][j] == 2:
                        pg.draw.rect(self.screen, (0, 255, 0), (i, j, 1, 1))









if __name__ == '__main__':
    ink = []
    map = Map.Map(map_cell, cell_pixel_length, 4)
    for i in range(600):
        for j in range (600):
            ran =random.randint(0, 1)
            ink.append(Pixcel.Pixcel(ran, time.time(), False, False,i, j, True))
    ink[-1] = Pixcel.Pixcel(0, time.time(), False, False, 599, 599, False)
    map.draw(ink)
    map_temp = map.readWholeMap()
    k = 0


    map_a  = np.zeros((600,600),dtype=int)
    for i in range(600):
        for j in range (600):
            map_a[i][j] = map_temp[0][k]['UID']
            k += 1



    color = (random.randint(0,255),random.randint(0,255),random.randint(0,255))
    app = Painter(map_a)
    app.run()

    # temp = []
    # with open('../yaml_test.yaml','r') as f:
    #     temp = yaml.load(f.read())
    #     print(temp[0])
