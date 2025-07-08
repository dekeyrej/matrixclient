import arrow
import logging
import json

class RGBLEDDisplay:
    """ base class for each display """
    def __init__(self, matrix=None):
        if matrix is not None:
            self.my_matrix = matrix
            self.my_canvas = matrix.CreateFrameCanvas()
        self.values = None
        # self.nextUpdate = None
        # self.offsetCounter = 1
        self.is_paused = False
        self.data_dirty = True # only redraw on new data

    def update(self, update_data): # implements a back off mechanism for stale messages
        if update_data['type'] == self.type:
            self.values = update_data
        else:
            logging.warning(f"Update data type {update_data['type']} does not match display type {self.type}")
        self.values = update_data
        self.data_dirty = True  # set to true so we redraw the display

    def display(self): # override this
        """ virtual function """
        # if self.data_dirty:
        #     draw new stuff
        # else:
        #     just throw up the old self.icon
        pass
    
    def justify(self, text, font, x=0, y=0, anchor='TL'):
        """ routine to logically position text """
        # width, height = font.getsize(text) # getsize went away at some version of Pillow
        # left, top, right, bottom = font.getbbox(text) # kinda goofy, left and top = 0??? 
        # width = right - left
        # height = bottom - top
        left, top, width, height = font.getbbox(text) 
        # Calculate the 'Y'
        if anchor[0] == 'T':   # Top
            yout = y   # previous bug?!?
        elif anchor[0] == 'M': # Middle (vertical)
            yout = y - height/2
        else:                  # Bottom
            yout = y + height
        # Calculate the 'X'    
        if anchor[1] == 'R':   # Right
            xout = x - width
        elif anchor[1] == 'C': # Center (horizontal)
            xout = x - width/2
        else:                  # Left
            xout = x
        return (xout, yout)
    
    def stringToDateTime(self, isostring):  # formerly 'stringToTime'
        #accepts an ISO date/time string and returns a time object based on the hour and minute (sets seconds to 0)
        return arrow.get(isostring).floor('second')
    
    def shortentime(self, timestr):
        return arrow.get(timestr,'M/D/YYYY h:mm:ss A').format('M/D/YYYY h:mmA')

    def string_to_tuple(self, input_str):
        tuplestr = input_str.replace('(','').replace(')','').split(',')
        return (int(tuplestr[0]), int(tuplestr[1]), int(tuplestr[2]))

    def hexToTuple(self, input_hex):
        return (int(input_hex[0:2], 16), int(input_hex[2:4], 16), int(input_hex[4:6], 16))

    def suffix(self, num):
        if num == 1:
            return 'st'
        elif num == 2:
            return 'nd'
        elif num == 3:
            return 'rd'
        else:
            return 'th'
        
    # def fix_edt(self,timestr):
    #     """" Fix non-uniqueness of the 'EDT' timezone abbreviation :-/ """
    #     if 'EDT' not in timestr:
    #         return timestr
    #     else:
    #         # replace EDT with US/Eastern
    #         # this is a hack to fix the non-uniqueness of the EDT timezone abbreviation
    #         # which is used in the US and Canada, but not in Europe
    #         # see
    #         return timestr.replace('EDT','US/Eastern')

    # def humanlat(self, latstr):
    #     lat = float(latstr)
    #     if lat > 0:
    #         ns = 'N'
    #     elif lat < 0:
    #         ns = 'S'
    #     else:
    #         ns = ' '
    #     return ' {:>7.3f} {}'.format(lat, ns)

    # def humanlon(self, lonstr):
    #     lon = float(lonstr)
    #     if lon > 0:
    #         ew = 'E'
    #     elif lon < 0:
    #         ew = 'W'
    #         lon = -1 * lon
    #     else:
    #         ew = ' '
    #     return '{:>8.3f} {}'.format(lon, ew)

    # def uptime_color(self, now, then):
    #     # print(int(float(tnow.format('X')) - float(client_start_time.format('X'))))
    #     time = int(float(now.format('X')) - float(then.format('X')))
    #     if   time < 60 * 15:      # 15 minutes
    #         return "Orange"
    #     elif time < 60 * 30:      # 30 minutes
    #         return "Yellow"
    #     elif time < 60 * 60 * 1:  #  1 hour
    #         return "Green"
    #     elif time < 60 * 60 * 6:  #  6 hours
    #         return "Turquoise"
    #     else:
    #         return "Blue"