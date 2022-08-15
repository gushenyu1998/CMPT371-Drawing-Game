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

Client_UID = 1  # Default Client ID in game
color = (255, 0, 0)  # Color of this player drawing, default = red
cell_pixel_length = 75 # For every cell in map, the length of the cell is 75 pixel
color_list = [(255, 255, 255, 255), (255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255), (255, 255, 0, 255)]
# User can find its color through this list, in white, read, blue, green, yellow

TCP_Port = 9006  # default port in socket
server_host = 'localhost'  # default ip address of socket

draw_data = []  # buffer of the data created when playing game
UID_list = [0, 1, 2, 3, 4]  # The list of how many player in the game totally
current_map = np.zeros((40, 40), dtype=int)  # The map of game
lock_list = np.zeros((8, 8), dtype=int)  # List of cell this player cannot draw on that

max_client = 1 # max client determined by the server, default in 1
player1 = "First player is: Player{}, {}"
player2 = "Second player is: Player{}, {}"
player3 = "Third player is: Player{}, {}"
player4 = "Last player is: Player{}, {}"
# Text used in show the game proccess

Painter_end_flag = False # Flag for if this game is over


def connection_setter(host, port):
    '''
        Set up the connection properties for TCP
    :param host: host address in TCP link
    :param port: host port in TCP link
    :return:
    '''
    global TCP_Port
    global server_host
    TCP_Port = int(port)
    server_host = str(host)


def delete_list_duplicate():
    '''
    Clean up the duplicate data in the buffer before send data to server
    :return:
    '''
    global draw_data
    if draw_data is None:
        draw_data = []
    draw_data = [dict(t) for t in set([tuple(d.items()) for d in draw_data])]


def client_update(pixel=None, UID=0):
    '''
    Update the user's map by receive pixel data from server
    :param pixel: the location of pixel
    :param UID: the UID who draw this pixel
    :return:
    '''
    if pixel is not None:
        x_axis = pixel[0]
        y_axis = pixel[1]
        current_map[x_axis][y_axis] = UID


def client_update_cell(pixel=None, UID=0):
    '''
    Update the user's map by receive cell data from server
    :param pixel: the location of pixel at the letf-top corner in the cell
    :param UID: the UID who draw this pixel
    :return:
    '''
    if pixel is not None:
        x_axis = pixel[0]
        y_axis = pixel[1]
        for i in range(5):
            for j in range(5):
                current_map[x_axis + i][y_axis + j] = UID


def game_check():
    '''
    Check how much every user draw
    :return: The rank of user and how much each ussr draw
    '''
    Players = []
    for UID in UID_list:
        if UID == 0:
            continue
        temp = (np.sum(current_map == UID)) / 1600
        Players.append({'UID': UID, 'percentage': temp})
    new = sorted(Players, key=lambda k: k.__getitem__('percentage'))
    new.reverse()
    return new


class Brush(object):
    '''
        User's Brush class. Let user be able to draw on screen and fill the data buffer with user's painting
    '''
    def __init__(self, screen):
        '''
        Initialize the Brush
        :param screen: Which screen the brush is drwaing
        '''
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
        '''
        Calculate the line draw by the user
        :param position: Where the user put the pen
        :return: The list of pixels in the line
        '''
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
        '''
        Draw the color on the painting board
        :param position: Where the user put his pen
        :return:
        '''
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
                    # Only unlocked and user-locked cell can be drawn
                    message = {'UID': Client_UID, 'draw_record': (int(p[0] / 15), int(p[1] / 15)), 'more': True}
                    draw_data.append(message)
                    pg.draw.rect(self.screen, color, (x_axis, y_axis, 15, 15))
            delete_list_duplicate()
        self.last_position = position


class Painter:
    def __init__(self, Sock):
        '''
        Painter class to let user draw
        :param Sock: the socket which used to send drawing data to client
        '''
        pg.display.set_caption("Player " + str(Client_UID))
        self.window = (600, 800)  # the size of painting board
        self.clock = pg.time.Clock()
        self.screen = pg.display.set_mode(self.window, 0, 32) # create board for painting
        self.brush = Brush(self.screen)
        self.paint_size = 10
        self.sock = Sock

    def run(self):
        '''
        Collect user's behaver every 0.1 seconds, and paint on the board
        :return:
        '''
        pg.init()
        self.screen.fill((255, 255, 255))
        self.draw_game_line()
        global Painter_end_flag
        while True:
            self.clock.tick(600)
            for event in pg.event.get():
                # collect the event created by mouse, do the painting
                if event.type == QUIT or Painter_end_flag:
                    # end the game when game over
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

    def draw_game_line(self):
        '''
        Paint the background blocks on the board
        :return:
        '''
        block_x = 75
        block_y = 75
        for i in range(9):
            pg.draw.line(self.screen, (0, 0, 0), (i * block_y, 0), (i * block_y, 600), 3)
        for j in range(9):
            pg.draw.line(self.screen, (0, 0, 0), (0, j * block_x), (600, j * block_x), 3)

    def Draw_update(self, pxiel=None, UID=0):
        """
        Update the user's paint board by receive pixel data from server
        :param pixel: the location of pixel
        :param UID: the UID who draw this pixel
        return:
        """
        if pxiel is not None:
            x_axis = pxiel[0]
            y_axis = pxiel[1]
            pg.draw.rect(self.screen, color_list[UID], (x_axis * 15, y_axis * 15, 15, 15))
            self.draw_game_line()

    def Cell_update(self, pxiel=None, UID=0):
        '''
        Update the user's paint board by receive pixel data from server
        :param pixel: the location of pixel
        :param UID: the UID who draw this pixel
        :return:
        '''
        if pxiel is not None:
            x_axis = pxiel[0]
            y_axis = pxiel[1]
            pg.draw.rect(self.screen, color_list[UID], (x_axis * 15, y_axis * 15, 75, 75))
            self.draw_game_line()

    def paint_judgement(self, position, event_type):
        '''
        Paint the pxiel to the paint board with some limitions
        :param position: Where the user is drawing
        :param event_type: The user's action
        :return:
        '''
        x = int(position[0] / 15)
        y = int(position[1] / 15)
        if position[0] <= 600 or position[1] <= 600:
            if event_type == MOUSEBUTTONDOWN:
                # user put down the mouse button, start drawing
                self.brush.start(position)
                message = {'UID': Client_UID, 'draw_record': (x, y), 'more': True}
                draw_data.append(message)
            elif event_type == MOUSEMOTION:
                # user drag the mouse to paining
                self.brush.Draw(position)
                self.draw_game_line()
            elif event_type == MOUSEBUTTONUP:
                # user put up the mouse button, let server clean up the unfilled cells
                self.brush.close()
                message = {'UID': Client_UID, 'draw_record': (4, 5), 'more': False}
                delete_list_duplicate()
                for i in range(3):
                    draw_data.append(message)
                self.sending_data()

    def sending_data(self):
        '''
        Send data in buffer to the server
        :return:
        '''
        while len(draw_data) != 0:
            message = draw_data.pop()
            sending = json.dumps(message)
            string = str(sending) + ';'
            self.sock.send(string.encode())
        return

    def text_update(self):
        '''
        Update the ranking of each player and how much they draw
        :return:
        '''
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


class TCP_client:
    def __init__(self):
        """
        Initialize the connection to the server
        """
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

    def receive_message(self):
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

    def build_player(self):
        '''
        Nigociate with server, get the id in gamem and know how many player in game
        :return:
        '''
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
                    ## Get player ID, update client ID in program
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
        '''
        Run the game with multiple threads
        :return:
        '''
        self.build_player()
        th1 = threading.Thread(target=self.receive_message)
        th1.daemon = True
        th1.start()

        th2 = threading.Thread(target=self.Painter.run(), args=(self.Painter,))
        th2.daemon = True
        th2.start()

        th1.join()
        th2.join()


def client_run_proccess():
    '''
    Game start entrance
    :return:
    '''
    time.sleep(1)
    app = TCP_client()
    app.run()