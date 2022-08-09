import time

class Pixcel(dict):
    def __init__(self, UID = 0,
                receive_time = time.time(),
                lock_flag = False,
                occupied = False,
                row = None,
                col = None,
                more = True
                ):
        self["UID"] = UID
        self["receive_time"]= receive_time 
        self["lock_flag"] = lock_flag
        self["occupied"] = occupied
        self.col = col
        self.row = row
        self["more"] = more

    def setUID(self, UID):
        self["UID"] = UID

    def getUID(self):
        return self["UID"]

    def getTimestamp(self):
        return self["receive_time"]

    def setTimestamp(self,timestamp):
        self["receive_time"] = timestamp
    
    def frashTimestamp(self):
        self["receive_time"] = time.time()
    
    def lockPixcel(self):
        self["lock_flag"] = True

    def unlockPixcel(self):
        self["lock_flag"] = False

    def getLock(self):
        return self["lock_flag"]

    def getCoordinate(self):
        return (self.row,self.col)

    def setCoordinate(self,row,col):
        self.row = row
        self.col = col
    
    def getRow(self):
        return self.row

    def getCol(self):
        return self.col

    def getMoreFlag(self):
        return self["more"]

    def setNoMore(self):
        self.more = False

    def setHaveMore(self):
        self.more = True

    def setAsEndDrawing(self,uid):
        self.more = False
        self.setUID(uid)


