from pyexpat.errors import XML_ERROR_INCORRECT_ENCODING
from xml.etree.ElementTree import tostring
import Pixcel
import time
import json


class Map:
    def __init__(self, map_length, cell_length, max_uid):
        self.MAP_LENGTH = map_length                                        # map length in cells
        self.CELL_LENGTH = cell_length                                      # cell length in pixcels
        self.MAX_UID = max_uid                                              # max uid, uid = 0 will be reserve for internal use only!
        self.MAP_LENGTH_IN_PIXCEL = self.MAP_LENGTH * self.CELL_LENGTH      # map length in pixcels
        self.MAP_SIZE = pow(self.MAP_LENGTH_IN_PIXCEL, 2)                   # how many pixcel in this map            
        self.TOTAL_CELL = pow(self.MAP_LENGTH, 2)                           # how many cells in this map
        self.OCCUPIED_BASE_LINE = 0.5 * pow(self.CELL_LENGTH, 2)            # how many pixcel in one cell that will mark as occupied

        self.occupiedDict = {}                                              # a dict store the occupid information
                                                                            # key = cell index, value = uid
        
        self.locked_cell_dict = {}                                          # a dict store which cell is locked
                                                                            # key = cell index, value = True if locked

        self.adjudication_queue = []                                        # a queue store the cells that need to be check
        for i in range(self.MAX_UID + 1):                                   # checkAdjudicationQueue() will check when stop drawing
            self.adjudication_queue.append([])                              # empty each call after checkAdjudicationQueue()
                                                                            # each user will will it own queue nester in the adjudication_queue
                                                                            # adjudication_queue is like[[UID 1],[ UID 2],[ UID 3],[...]]

        self.map_data = []                                                  # a temp_list of pixcel store the map information
        for i in range(self.MAP_SIZE):
            self.map_data.append(Pixcel.Pixcel())

        self.cell_map = []                                                  # [Abandoned] may remove later
        for i in range(pow(map_length, 2)):
            self.cell_map.append(Pixcel.Pixcel())

    """
    Function:   convert pixcel coordinate in to the index in map_data

    input:      pixcel row, pixcel col
    output:     index in map_data
    """
    def coordinate2Index(self, row, col):
        return row * self.MAP_LENGTH_IN_PIXCEL + col

    def pixcelIndex2Coordinate(self, pixcel_index):
        pixcel_row = int(int(pixcel_index) / int(self.MAP_LENGTH_IN_PIXCEL))
        pixcel_col = int(int(pixcel_index) % int(self.MAP_LENGTH_IN_PIXCEL))
        return (pixcel_row, pixcel_col)

    """
    Function:   convert cell coordinate in to the index in map_data

    input:      cell row, cell col
    output:     index in map_data
    """
    def cellCoordinate2Index(self, cell_row, cell_col):
        return cell_row * self.MAP_LENGTH + cell_col

    """
    Function:   convert  cell index in to the coordinate

    input:      index in map_data 
    output:     (cell row, cell col)
    """
    def cellIndex2Coordinate(self, index):
        cell_row = int(int(index) / int(self.MAP_LENGTH))
        cell_col = int(int(index) % int(self.MAP_LENGTH))
        return (cell_row, cell_col)

    """
    Function:   convert  pixcel Coordinate in to the index of cell

    input:      pixcel row, pixcel col
    output:     cell index
    """
    def pixcelCoordinate2CellIndex(self, row, col):
        cell_row = int(int(row) / int(self.CELL_LENGTH))
        cell_col = int(int(col) / int(self.CELL_LENGTH))

        cell_index = cell_row * self.MAP_LENGTH + cell_col
        return cell_index

    """
    Function:   find the winner by using the occupiedDict
    Notes:      should only used by checkWin()!

    output:     (number of cell take by the winner, winnwe UID)
    """
    def findWinner(self):
        cells = []

        for key in self.occupiedDict:
            cells.append(self.occupiedDict[key])

        most = 0
        most_uid = 0
        for i in range(self.MAX_UID+1):
            counter = cells.count(i)
            if counter > most:
                most = counter
                most_uid = i

        return (most, most_uid)


    """
    Function:   check if the map is full by check the occupiedDict length == max number of cells in the map

    output:     (winner UID, True) if the game is end, (0, False) if the game is not end
    """
    def checkWin(self):

        if len(self.occupiedDict) == self.TOTAL_CELL:
            winner_info = self.findWinner()
            return (winner_info[1], True)
        else:
            return (0, False)


    def getCellLock(self, row, col):
        coor = self.coordinate2Index(row, col)
        if str(coor) in self.locked_cell_dict:
            return True
        return False
    
    
    def lockPixceslInCell(self, cell_row, cell_col):
        pixcel_x_min = cell_col*self.CELL_LENGTH
        pixcel_x_max = cell_col*(self.CELL_LENGTH) + self.CELL_LENGTH

        pixcel_y_min = cell_row*self.CELL_LENGTH
        pixcel_y_max = cell_row*(self.CELL_LENGTH) + self.CELL_LENGTH

        row_iter = pixcel_y_min
        while(row_iter < pixcel_y_max):
            col_iter = pixcel_x_min
            while(col_iter < pixcel_x_max):
                self.map_data[self.coordinate2Index(
                    row_iter, col_iter)].lockPixcel()

                col_iter += 1
            row_iter += 1


    def unlockPixceslinCell(self, cell_row, cell_col):
        pixcel_x_min = cell_col*self.CELL_LENGTH
        pixcel_x_max = cell_col*(self.CELL_LENGTH) + self.CELL_LENGTH

        pixcel_y_min = cell_row*self.CELL_LENGTH
        pixcel_y_max = cell_row*(self.CELL_LENGTH) + self.CELL_LENGTH

        row_iter = pixcel_y_min
        while(row_iter < pixcel_y_max):
            col_iter = pixcel_x_min
            while(col_iter < pixcel_x_max):
                self.map_data[self.coordinate2Index(
                    row_iter, col_iter)].unlockPixcel()

                col_iter += 1
            row_iter += 1


    """
    Function:   getter of inner pixcel of the map

    input:      pixcel_row, pixcel_col
    """
    def getPixcel(self, pixcel_row, pixcel_col):
        return self.map_data[self.coordinate2Index(pixcel_row, pixcel_col)]


    """
    Function:   receive the pixcel temp_list and wrrite in to the map if the cell is not 
                locked or occupied, than put this cell in to adjudication_queue for checking

    input:      pixcel row, pixcel col
    output:     cell index
    """
    def draw(self, ink):
        # prevent the ink temp_list is empty
        if len(ink) == 0:
            return self.checkWin()

        uid = ink[0].getUID()
        for i in range(len(ink)):

            # receive stop drawing signal
            if (ink[i].getMoreFlag() == False):

                # call checkAdjudicationQueue(uid) to check if each cell reach 50%
                self.checkAdjudicationQueue(uid)

                #check if the map is full, and return the winner information if the map is full
                return self.checkWin()

            pixcel_row = ink[i].getRow()
            pixcel_col = ink[i].getCol()

            pixcel_index = self.pixcelCoordinate2CellIndex(pixcel_row,pixcel_col)

            if pixcel_index >= self.MAP_SIZE :
                continue

            cell_index = self.pixcelCoordinate2CellIndex(pixcel_row, pixcel_col)

            cell_row = self.cellIndex2Coordinate(cell_index)[0]
            cell_col = self.cellIndex2Coordinate(cell_index)[1]

            #case of this cell is already taken by any user
            if str(cell_index) in self.occupiedDict:
                # print("CELL already occupied")
                # not write in to the map
                continue

            # case of the cell is locked by other user
            if str(cell_index) in self.locked_cell_dict:
                # print("CELL locked")
                # not write in to the map
                if (self.locked_cell_dict[str(cell_index)] != uid):
                    continue

            # case of cell is not locked
            self.locked_cell_dict[str(cell_index)] = uid                       # add this cell to locked_cell_dict
            self.getPixcel(pixcel_row, pixcel_col).setUID(ink[i].getUID())       # write in to the map
            self.getPixcel(pixcel_row, pixcel_col).lockPixcel()
            self.lockPixceslInCell(cell_row,cell_col)
            # map.getPixcel(pixcel_row, pixcel_col).setUID(ink[i].lockPixcel())   

            # add this cell to adjudication_queue for checking if reach 50%
            if (cell_index) not in self.adjudication_queue[uid]:                
                self.adjudication_queue[uid].append(cell_index)

        return self.checkWin()


    """
    Function:   receive json string and call draw()
    """
    def drawJSON(self, ink_json):
        ink_json = str(ink_json).replace("'",'"')
        ink_json = str(ink_json).replace("True",'"True"')
        ink_json = str(ink_json).replace("False",'"False"')
        # print(ink_json)
        # print("\n\n\n")
        # print(json.loads(ink_json))
        json_data = json.loads(ink_json)
        # print("\n\njsdata:\n")
        # print(json_data)


        # print(json_data["UID"])
        # print(json_data["draw_record"])
        # print(json_data["more"])

        ink = []

        for i in range(len(json_data)):
            # print(json_data[i]["UID"])
            # print(json_data[i]["draw_record"])
            # print(json_data[i]["more"])
            ink.append(Pixcel.Pixcel(json_data[i]["UID"], time.time(), False, False, json_data[i]["draw_record"][0], json_data[i]["draw_record"][1], json_data[i]["more"] == "True"))


        # print(ink)

        self.draw(ink)


    """
    Function:   unlock the cell and set all pixcel's uid to 0
    Notes:      should only used by adjudicationCell()!
    """
    def freeCell(self, cell_col, cell_row):
        # self.lockCell(self, cell_row, cell_col)
        pixcel_x_min = cell_col*self.CELL_LENGTH
        pixcel_x_max = cell_col*(self.CELL_LENGTH) + self.CELL_LENGTH

        pixcel_y_min = cell_row*self.CELL_LENGTH
        pixcel_y_max = cell_row*(self.CELL_LENGTH) + self.CELL_LENGTH

        row_iter = pixcel_y_min
        while(row_iter < pixcel_y_max):
            col_iter = pixcel_x_min
            while(col_iter < pixcel_x_max):
                self.map_data[self.coordinate2Index(
                    row_iter, col_iter)].setUID(0)
                self.map_data[self.coordinate2Index(
                    row_iter, col_iter)].unlockPixcel()
                col_iter += 1
            row_iter += 1

        self.locked_cell_dict.pop(
            str(self.cellCoordinate2Index(cell_row, cell_col)))

    """
    Function:   get the cell content and return a uid list
    Return:     put all the uid inside the cell in a list and return it 
    """
    def getCellContent(self, cell_col, cell_row):
        pixcel_x_min = cell_col*self.CELL_LENGTH
        pixcel_x_max = cell_col*(self.CELL_LENGTH) + self.CELL_LENGTH

        pixcel_y_min = cell_row*self.CELL_LENGTH
        pixcel_y_max = cell_row*(self.CELL_LENGTH) + self.CELL_LENGTH

        uid_list = []

        row_iter = pixcel_y_min
        while(row_iter < pixcel_y_max):
            col_iter = pixcel_x_min
            while(col_iter < pixcel_x_max):
                uid_list.append(self.map_data[self.coordinate2Index(
                    row_iter, col_iter)].getUID())
                col_iter += 1
            row_iter += 1

        return uid_list
  

    """
    Function:   lock the cell, put cell in to occupiedDict and set all pixcel's uid to occupier's UID
    Notes:      should only used by adjudicationCell()!
    """
    def setOccupied(self, cell_col, cell_row, occupier_uid):
        pixcel_x_min = cell_col*self.CELL_LENGTH
        pixcel_x_max = cell_col*(self.CELL_LENGTH) + self.CELL_LENGTH

        pixcel_y_min = cell_row*self.CELL_LENGTH
        pixcel_y_max = cell_row*(self.CELL_LENGTH) + self.CELL_LENGTH

        row_iter = pixcel_y_min
        while(row_iter < pixcel_y_max):
            col_iter = pixcel_x_min
            while(col_iter < pixcel_x_max):
                self.map_data[self.coordinate2Index(
                    row_iter, col_iter)].setUID(occupier_uid)
                self.map_data[self.coordinate2Index(
                    row_iter, col_iter)].lockPixcel()

                col_iter += 1
            row_iter += 1
            

        self.locked_cell_dict[str(self.cellCoordinate2Index(
            cell_row, cell_col))] = occupier_uid
        self.occupiedDict[str(self.cellCoordinate2Index(
            cell_row, cell_col))] = occupier_uid


    """
    Function:   read adjudication_queue and run the adjudicationCell() for the user with this UID

    input:      UID
    """
    def checkAdjudicationQueue(self, uid):
        length = len(self.adjudication_queue[uid])

        for i in range(length):
            cell_coordinate = self.cellIndex2Coordinate(self.adjudication_queue[uid][i])
            self.adjudicationCell(cell_coordinate[1], cell_coordinate[0])

        self.adjudication_queue[uid] = []


    """
    Function:   check the cell if reach 50% and free this cell or mark as occupied

    input:      cell_col, cell_row
    """
    def adjudicationCell(self, cell_col, cell_row):
        pixcel_x_min = cell_col*self.CELL_LENGTH
        pixcel_x_max = cell_col*(self.CELL_LENGTH) + self.CELL_LENGTH

        pixcel_y_min = cell_row*self.CELL_LENGTH
        pixcel_y_max = cell_row*(self.CELL_LENGTH) + self.CELL_LENGTH

        count_table = [] * (self.MAX_UID + 1)

        row_iter = pixcel_y_min
        while(row_iter < pixcel_y_max):

            col_iter = pixcel_x_min
            while(col_iter < pixcel_x_max):
                count_table.append(
                    self.map_data[self.coordinate2Index(row_iter, col_iter)].getUID())
                col_iter += 1
            row_iter += 1

        most = 0
        most_uid = 0
        for i in range(self.MAX_UID+1):
            counter = count_table.count(i)
            if counter > most:
                most = counter
                most_uid = i


        if most >= self.OCCUPIED_BASE_LINE and most_uid != 0:
            self.setOccupied(cell_col, cell_row, most_uid)
        else:
            self.freeCell(cell_col, cell_row)

    """
    Function:   run adjudicationCell for all the map
    """
    def adjudicationMap(self):
        for i in range(self.TOTAL_CELL):
            cell_row = self.cellIndex2Coordinate(i)[0]
            cell_col = self.cellIndex2Coordinate(i)[1]

            self.adjudicationCell(cell_col, cell_row)


    """
    Function:   read the map data and return a temp_list in [(UID)] format
    Return:      [(UID)]
    """
    def readMapInUidList(self):
        uid_list = []

        for i in range(len(self.map_data)):
            uid_list.append(self.map_data[i].getUID())
            # print(self.map_data[i].getUID())
        
        return uid_list

    """
    Function:   read the map data and return a temp_list in [(UID, lock)] format
    Return:      [(UID, lock)]
    """
    def readMapInUidLockList(self):
        map_list = []

        for i in range(len(self.map_data)):
            map_list.append((self.map_data[i].getUID(),self.map_data[i].getLock()))
            # print(self.map_data[i].getUID())
        
        return map_list

    def readMapInUidLockListJSON(self):
        map_list = []

        for i in range(len(self.map_data)):
            map_list.append((self.map_data[i].getUID(),self.map_data[i].getLock()))
            # print(self.map_data[i].getUID())

        json_map_data = json.dumps(map_list)
        
        return json_map_data

    """
    Function:   read the map data and return a json string
    Return:     {'index': cell_index, 'islock': islock, 'loc': uid_list}
    """
    def readMapInCellJSON(self):

        map_data = "[;;"

        for cell_index in range(self.TOTAL_CELL):

            cood = self.cellIndex2Coordinate(cell_index)
            cell_row = cood[0]
            cell_col = cood[1]


            islock = self.getCellLock(cell_row,cell_col)

            uid_list = self.getCellContent(cell_col, cell_row)

            # cell_data_str = {'index': cell_index, 'islock': islock, 'loc': uid_list}

            cell_data_str = '{"index": ' + str(cell_index) + ', "islock": ' + str(islock) + ', "loc": ' + str(uid_list) + '};;'

            map_data +=cell_data_str

        # map_data = map_data.strip(',')
        map_data += ']'
        return map_data

    """
    Function:   read the map data and return a json string
    Return:     {'index': pixcel_index, 'islock': islock, 'loc': [uid]}
    """
    def readMapInPixcelJSON(self):

        map_data = "[;;"

        for pixcel_index in range(self.MAP_SIZE):

            pixcel_row = self.pixcelIndex2Coordinate(pixcel_index)[0]
            pixcel_col = self.pixcelIndex2Coordinate(pixcel_index)[1]

            islock = self.getPixcel(pixcel_row,pixcel_col).getLock()
            uid_list = []

            uid_list.append(self.getPixcel(pixcel_row,pixcel_col).getUID())
            # cell_data_str = {'index': cell_index, 'islock': islock, 'loc': uid_list}

            pixcel_data_str = '{"index": ' + str(pixcel_index) +', "loc": ' + str(uid_list) + '};;'

            map_data +=pixcel_data_str

        # map_data = map_data.strip(',')
        map_data += ']'
        return map_data


    """
    Function:   read the map data and return a json string
    Return:     {'index': cell_index, 'islock': islock, 'loc': [uid]}
    """
    def readMapInCellLockJSON(self):

        map_data = "[;;"

        for cell_index in range(self.TOTAL_CELL):

            cood = self.cellIndex2Coordinate(cell_index)
            cell_row = cood[0]
            cell_col = cood[1]


            islock = self.getCellLock(cell_row,cell_col)


            # cell_data_str = {'index': cell_index, 'islock': islock, 'loc': uid_list}

            cell_data_str = '{"index": ' + str(cell_index) + ', "islock": ' + str(islock) + '};;'

            map_data +=cell_data_str
        # map_data = map_data.strip(',')
        map_data += ']'
        return map_data

    """
    Function:   get the whole map data whith the format of (map_data, (winner_ID, True is game is end))

    return: (map_data, winner_info)
            map_data is a temp_list a pixcel
            winner_info is (winner_id, True) if the gam is end
                        or (0, false) if the game is not ended
    """
    def readWholeMap(self):
        return self.map_data

    #test function
    def printMap(self):
        for y in range(self.MAP_LENGTH_IN_PIXCEL):
            for x in range(self.MAP_LENGTH_IN_PIXCEL):
                print('_', end="")
                print(self.map_data[self.coordinate2Index(
                    y, x)].getUID(), end="")
                print('_', end="")
            print('\n', end="")

    #test function 
    def printArray(self):
        for i in range(self.num):
            print(self.map_data[i].getUID(), end="")
