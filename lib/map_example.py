import Map
import Pixcel
import time


map_length_measure_in_cells = 2
cell_length_measure_in_pixcels = 4
max_uid = 10


# create a map object
map = Map.Map(map_length_measure_in_cells,
              cell_length_measure_in_pixcels, 
              max_uid)

# print the map
print("empty map:")
map.printMap()


# use draw() to write
    #draw receive a list of pixcel

ink = []
ink.append(Pixcel.Pixcel(6, time.time(), False, False, 0, 0, True))
ink.append(Pixcel.Pixcel(6, time.time(), False, False, 0, 1, True))
ink.append(Pixcel.Pixcel(6, time.time(), False, False, 0, 2, True))
ink.append(Pixcel.Pixcel(6, time.time(), False, False, 0, 3, True))
ink.append(Pixcel.Pixcel(6, time.time(), False, False, 0, 4, True))
ink.append(Pixcel.Pixcel(6, time.time(), False, False, 0, 5, True))
ink.append(Pixcel.Pixcel(6, time.time(), False, False, 0, 6, True))

map.draw(ink)
print("draw(ink):")
map.printMap()
print(map.readMapInUidLockList())
print("because we don't set stop drowing, the cell not reach 50% will not be cleared")

ink2 = []
ink2.append(Pixcel.Pixcel(6, time.time(), False, False, 1, 0, True))
ink2.append(Pixcel.Pixcel(6, time.time(), False, False, 1, 1, True))
ink2.append(Pixcel.Pixcel(6, time.time(), False, False, 1, 2, True))
ink2.append(Pixcel.Pixcel(6, time.time(), False, False, 1, 3, True))
ink2.append(Pixcel.Pixcel(6, time.time(), False, False, 1, 4, True))
ink2.append(Pixcel.Pixcel(6, time.time(), False, False, 1, 5, True))

#if you set the laset parameter as false, draw will know user is stopped drawing
#you must contain the UID in the first parameter
ink2.append(Pixcel.Pixcel(6, time.time(), False, False, 0, 6, False))

map.draw(ink2)
print("draw(ink2):")
map.printMap()
print("because it didn't reach 50%, the first and second cell will be clear")


ink3 = []
ink3.append(Pixcel.Pixcel(7, time.time(), False, False, 0, 0, True))
ink3.append(Pixcel.Pixcel(7, time.time(), False, False, 0, 1, True))
ink3.append(Pixcel.Pixcel(7, time.time(), False, False, 0, 2, True))
ink3.append(Pixcel.Pixcel(7, time.time(), False, False, 0, 3, True))
ink3.append(Pixcel.Pixcel(7, time.time(), False, False, 1, 0, True))
ink3.append(Pixcel.Pixcel(7, time.time(), False, False, 1, 1, True))
ink3.append(Pixcel.Pixcel(7, time.time(), False, False, 1, 2, True))
ink3.append(Pixcel.Pixcel(7, time.time(), False, False, 1, 3, True))
ink3.append(Pixcel.Pixcel(7, time.time(), False, False, 2, 0, True))

# end drowing
ink3.append(Pixcel.Pixcel(7, time.time(), False, False, 0, 0, False))

map.draw(ink3)
print("draw(ink3):")
map.printMap()
print("because it reach 50%, the first cell will be set as occupied")


ink4 = []
for i in range(map_length_measure_in_cells * cell_length_measure_in_pixcels):
    for j in range (map_length_measure_in_cells * cell_length_measure_in_pixcels):
        ink4.append(Pixcel.Pixcel(8, time.time(), False, False, i, j, True))

ink4.append(Pixcel.Pixcel(8, time.time(), False, False, 0, 0, False))

print("return of drawing")
print(map.draw(ink4))
print("True means the game is end, 8 means the winnwer's uid is 8")


print("draw(ink4):")
map.printMap()

print("\n or you can use checkWin()")
print(map.checkWin())


print("\n\n\n")
#use readWholeMap() to read the map

# uncomment it to see
# print(map.readWholeMap())
# print(map.readMapInUidLockList())
print(map.readMapInUidLockListJSON())

# it will return (pixcel_list[], winner_info)
#pixcel_list is a list of pixcel
#winner info have the same same with checkWin()

print("\n\n\n")
json_str = "[{'UID': 1, 'draw_record': [1, 2], 'more': True}, {'UID': 1, 'draw_record': [2, 2], 'more': True}]"

map.drawJSON(json_str)