import json
import math
import os
import socket
import threading
import time
from fnmatch import fnmatch
import numpy as np
import pygame as pg
from pygame.locals import *

Client_UID = 1
color = (255, 0, 0)
map_cell = 10
cell_pixel_length = 75
color_list = [(255, 255, 255, 255), (255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255), (255, 255, 0, 255)]

TCP_Port = 9006
server_host = 'localhost'

draw_data = []
UID_list = [0, 1, 2, 3, 4]
current_map = np.zeros((40, 40), dtype=int)
lock_list = np.zeros((8, 8), dtype=int)

max_client = 1
player1 = "First player is: Player{}, {}"
player2 = "Second player is: Player{}, {}"
player3 = "Third player is: Player{}, {}"
player4 = "Last player is: Player{}, {}"

Painter_end_flag = False


def connection_setter(host, port):  # sets the port and host
    global TCP_Port
    global server_host
    TCP_Port = int(port)
    server_host = str(host)


def delete_list_duplicate():
    global draw_data
    if draw_data is None:
        draw_data = []
    draw_data = [dict(t) for t in set([tuple(d.items()) for d in draw_data])]


def client_update(pixel=None, UID=0):  # updates the game board on the client end
    if pixel is not None:
        x_axis = pixel[0]
        y_axis = pixel[1]
        current_map[x_axis][y_axis] = UID


def client_update_cell(pixel=None, UID=0):
    if pixel is not None:
        x_axis = pixel[0]
        y_axis = pixel[1]
        for i in range(5):
            for j in range(5):
                current_map[x_axis + i][y_axis + j] = UID


def game_check():  # checks the score
    Players = []
    for UID in UID_list:
        if UID == 0:
            continue
        temp = (np.sum(current_map == UID)) / 1600
        Players.append({'UID': UID, 'percentage': temp})
    new = sorted(Players, key=lambda k: k.__getitem__('percentage'))
    new.reverse()
    return new


def check_win():  # checks the win condition
    p = game_check()
    nth_player = 0
    for temp in p:
        if temp['percentage'] >= 0.5:
            return True, nth_player
        nth_player += 1
    return False, 0


class Brush(object):  # class for the user brush to paint the cells
    def __init__(self, screen):
        global color
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

    def Draw(self, position):  # Draw the board state
        if self.drawing:
            for p in self.get_line(position):
                if p[0] < 0 or p[0] >= 600 or p[1] < 0 or p[1] >= 600:
                    continue
                x_axis_lock = min(int(p[0] / 75), 7)
                y_axis_lock = min(int(p[1] / 75), 7)
                x_axis = int(p[0] / 15) * 15
                y_axis = int(p[1] / 15) * 15

                if lock_list[x_axis_lock][y_axis_lock] == 0 or \
                        lock_list[x_axis_lock][y_axis_lock] == Client_UID:
                    message = {'UID': Client_UID, 'draw_record': (int(p[0] / 15), int(p[1] / 15)), 'more': True}
                    draw_data.append(message)
                    pg.draw.rect(self.screen, color, (x_axis, y_axis, 15, 15))
            delete_list_duplicate()
        self.last_position = position


class Painter:  # Paints the user input on the board and draws the board
    def __init__(self, Sock):
        pg.display.set_caption("Player " + str(Client_UID))
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
        global Painter_end_flag
        while True:
            self.clock.tick(600)
            for event in pg.event.get():
                if event.type == QUIT or Painter_end_flag:
                    pg.display.quit()
                    pg.quit()
                    return
                elif event.type == MOUSEBUTTONDOWN or \
                        event.type == MOUSEMOTION or \
                        event.type == MOUSEBUTTONUP:
                    self.paint_judgement(position=event.pos, event_type=event.type)
            self.text_update()
            delete_list_duplicate()
            self.sending_data()
            pg.display.update()

    def draw_game_line(self):  # draws the grid
        block_x = 75
        block_y = 75
        for i in range(9):
            pg.draw.line(self.screen, (0, 0, 0), (i * block_y, 0), (i * block_y, 600), 3)
        for j in range(9):
            pg.draw.line(self.screen, (0, 0, 0), (0, j * block_x), (600, j * block_x), 3)

    def Draw_update(self, pxiel=None, UID=0):
        if pxiel is not None:
            x_axis = pxiel[0]
            y_axis = pxiel[1]
            pg.draw.rect(self.screen, color_list[UID], (x_axis * 15, y_axis * 15, 15, 15))
            self.draw_game_line()

    def Cell_update(self, pxiel=None, UID=0):
        if pxiel is not None:
            x_axis = pxiel[0]
            y_axis = pxiel[1]
            pg.draw.rect(self.screen, color_list[UID], (x_axis * 15, y_axis * 15, 75, 75))
            self.draw_game_line()

    # makes decision to conquer the cell based on the portion of cell painted
    def paint_judgement(self, position, event_type):
        x = int(position[0] / 15)
        y = int(position[1] / 15)
        if position[0] <= 600 or position[1] <= 600:
            if event_type == MOUSEBUTTONDOWN:
                self.brush.start(position)
                message = {'UID': Client_UID, 'draw_record': (x, y), 'more': True}
                draw_data.append(message)
            elif event_type == MOUSEMOTION:
                self.brush.Draw(position)
                self.draw_game_line()
            elif event_type == MOUSEBUTTONUP:
                self.brush.close()
                message = {'UID': Client_UID, 'draw_record': (4, 5), 'more': False}
                delete_list_duplicate()
                for i in range(3):
                    draw_data.append(message)
                self.sending_data()

    def sending_data(self):  # sends updates to the server
        while len(draw_data) != 0:
            message = draw_data.pop()
            sending = json.dumps(message)
            string = str(sending) + ';'
            self.sock.send(string.encode())
        return

    def text_update(self):  # updates the user score on the screen
        rect = pg.Surface((600, 200))
        rect.fill((255, 255, 255))
        self.screen.blit(rect, (0, 600))
        game_proccess = game_check()

        game_text1 = player1.format(game_proccess[0]['UID'], "%.2f%%" % (game_proccess[0]['percentage'] * 100))
        font_t = pg.font.SysFont('arial', 30)
        text = font_t.render(game_text1, True, (0, 0, 0))
        self.screen.blit(text, (20, 620))
        pg.draw.rect(self.screen, color_list[game_proccess[0]['UID']], ((450, 620), (30, 30)))

        if max_client < 2:
            return
        game_text2 = player2.format(game_proccess[1]['UID'], "%.2f%%" % (game_proccess[1]['percentage'] * 100))
        font_t = pg.font.SysFont('arial', 30)
        text = font_t.render(game_text2, True, (0, 0, 0))
        self.screen.blit(text, (20, 660))
        pg.draw.rect(self.screen, color_list[game_proccess[1]['UID']], ((450, 660), (30, 30)))

        if max_client < 3:
            return
        game_text3 = player3.format(game_proccess[2]['UID'], "%.2f%%" % (game_proccess[2]['percentage'] * 100))
        font_t = pg.font.SysFont('arial', 30)
        text = font_t.render(game_text3, True, (0, 0, 0))
        self.screen.blit(text, (20, 700))
        pg.draw.rect(self.screen, color_list[game_proccess[2]['UID']], ((450, 700), (30, 30)))

        if max_client < 4:
            return
        game_text4 = player4.format(game_proccess[3]['UID'], "%.2f%%" % (game_proccess[3]['percentage'] * 100))
        font_t = pg.font.SysFont('arial', 30)
        text = font_t.render(game_text4, True, (0, 0, 0))
        self.screen.blit(text, (20, 740))
        pg.draw.rect(self.screen, color_list[game_proccess[3]['UID']], ((450, 700), (30, 30)))


class TCP_client:  # connects to the server
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((server_host, TCP_Port))
        connection = self.sock.recv(1024).decode()
        self.last_message = ""
        print(connection)
        if len(connection) != 0:
            self.Painter = None
        else:
            print('connection not success')
            return

    def client_draw_panel(self, a=None):
        self.Painter.run()

    def receive_message(self):  # Receives the message and process the map, update client
        '''
        Receve the message and process the map, update client
        :return:
        '''
        while True:
            data_stock = []
            try:
                data = self.sock.recv(1024).decode()
                data_stock = data.split(';;')
            except Exception as e:
                print('receive message error, detail:', repr(e))
                self.sock.close()
            if len(data_stock) > 0:
                temp = data_stock[0] + self.last_message
                data_stock.insert(0, temp)
                self.last_message = data_stock[-1]
            while len(data_stock) != 0:
                data_js = data_stock.pop(0)
                # match the update drawing information
                if fnmatch(str(data_js), '{"UID": *, "loc": *}'):
                    data_json = json.loads(data_js)
                    client_update(data_json['loc'], data_json['UID'])
                    self.Painter.Draw_update(data_json['loc'], data_json['UID'])

                # match the update Lock List information
                if fnmatch(str(data_js), '{"Lock": *, "loc": *}'):
                    data_json = json.loads(data_js)
                    i = data_json['loc']
                    x = i[0]
                    y = i[1]
                    if x >= 8 or y >= 8:
                        return
                    if data_json['Lock']:
                        lock_list[x][y] = data_json["Lock"]
                    else:
                        lock_list[x][y] = 0
                # match the cell update information
                if fnmatch(str(data_js), '{"UID_cell": *, "loc": *}'):
                    data_json = json.loads(data_js)
                    if data_json['loc'][0] >= 40 or data_json['loc'][1] >= 40:
                        return
                    client_update_cell(data_json['loc'], data_json['UID_cell'])
                    self.Painter.Cell_update(data_json['loc'], data_json['UID_cell'])
                if str(data_js) == 'CLOSEGAME':
                    global Painter_end_flag
                    Painter_end_flag = True
                if fnmatch(str(data_js), '{"UID": *, "percentage": *}'):
                    data_json = json.loads(data_js)
                    print("Game is over, the winner is Player" + str(data_json['UID']))
                    print("Thank you for playing, Please close this program")
                    os.system("Pause")
                    exit(1)

    def build_player(self): # makes the player ready after connected
        try:
            loop_time_out = 1000
            global Client_UID
            global color
            break_flag = True
            while loop_time_out >= 0 and break_flag:
                loop_time_out -= 1
                time.sleep(0.1)
                try:
                    data = self.sock.recv(125).decode()
                finally:
                    print("Building Client......")
                data_stock = data.split(';;')
                while len(data_stock) != 0:
                    data_js = data_stock.pop(0)
                    ## ↓↓Get player ID, update client ID in program
                    if fnmatch(str(data_js), '{"PID": *, "MAX": *}'):
                        global max_client
                        global UID_list
                        data_json = json.loads(data_js)
                        Client_UID = data_json['PID']
                        max_client = data_json['MAX']
                        UID_list = UID_list[0:max_client + 1]
                        color = color_list[Client_UID]
                        print("Build Client Success......., ")
                        print("Client UID is {}, color is: {}".format(Client_UID, color))
                        break_flag = False
                        break
            if loop_time_out <= 0:
                return

            while True:
                print("Waiting For other player joins in........")
                try:
                    data = self.sock.recv(125).decode()
                finally:
                    print("Waiting For game start, need about 3 seconds")
                data_stock = data.split(';;')
                while len(data_stock) != 0:
                    data_js = data_stock.pop(0)
                    if fnmatch(str(data_js), 'GAMESTART'):
                        print("Waiting For game start, need about 3 seconds")
                        time.sleep(3)
                        self.Painter = Painter(self.sock)
                        print("Game_start")
                        return


        except:
            print('Build client error')

    def run(self):
        self.build_player()
        th1 = threading.Thread(target=self.receive_message)
        th1.daemon = True
        th1.start()

        th2 = threading.Thread(target=self.Painter.run(), args=(self.Painter,))
        th2.daemon = True
        th2.start()

        th1.join()
        th2.join()


def client_run_proccess(): # runs the client functions
    time.sleep(1)
    app = TCP_client()
    app.run()
