from pyexpat.errors import XML_ERROR_INCORRECT_ENCODING
from xml.etree.ElementTree import tostring
import Pixcel
import time


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

        self.map_data = []                                                  # a list of pixcel store the map information
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

    #[Abandoned]
    def getCellLock(self, row, col):
        coor = self.coordinate2Index(row, col)
        return self.cell_map[coor].getLock()
    
    #[Abandoned]
    def lockCell(self, cell_row, cell_col):
        coor = self.coordinate2Index(cell_row, cell_col)
        self.cell_map[coor].lockPixcel()

    #[Abandoned]
    def unlockCell(self, cell_row, cell_col):
        coor = self.coordinate2Index(cell_row, cell_col)
        self.cell_map[coor].unlockPixcel()


    """
    Function:   getter of inner pixcel of the map

    input:      pixcel_row, pixcel_col
    """
    def getPixcel(self, pixcel_row, pixcel_col):
        return self.map_data[self.coordinate2Index(pixcel_row, pixcel_col)]


    """
    Function:   receive the pixcel list and wrrite in to the map if the cell is not 
                locked or occupied, than put this cell in to adjudication_queue for checking

    input:      pixcel row, pixcel col
    output:     cell index
    """
    def draw(self, ink):
        # prevent the ink list is empty
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
            cell_index = self.pixcelCoordinate2CellIndex(pixcel_row, pixcel_col)

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
            # map.getPixcel(pixcel_row, pixcel_col).setUID(ink[i].lockPixcel())   

            # add this cell to adjudication_queue for checking if reach 50%
            if (cell_index) not in self.adjudication_queue[uid]:                
                self.adjudication_queue[uid].append(cell_index)

        return self.checkWin()



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
                    row_iter, col_iter)].unlockPixcel() # may remove later
                col_iter += 1
            row_iter += 1

        self.locked_cell_dict.pop(
            str(self.cellCoordinate2Index(cell_row, cell_col)))

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
                    row_iter, col_iter)].lockPixcel() # may remove later

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
    Function:   get the whole map data whith the format of (map_data, (winner_ID, True is game is end))

    return: (map_data, winner_info)
            map_data is a list a pixcel
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
