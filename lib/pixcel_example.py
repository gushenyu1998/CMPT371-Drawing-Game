import Pixcel
import time



# create new pixcel
px = Pixcel.Pixcel()

#  setCoordinate(self,row,col):
px.setCoordinate(1,1)

# getCoordinate
print(px.getCoordinate)

#stop drawing sign
uid = 6
px.setAsEndDrawing(uid)

'''
class Pixcel(dict):
    def __init__(self, UID = 0,
                receive_time = time.time(),
                lock_flag = False,
                occupied = False,
                row = None,
                col = None,
                more = True
                ):
'''
row = 1
col = 1
more_flag = True

px2 = Pixcel.Pixcel(uid, time.time(), False, False, row, col, more_flag)
