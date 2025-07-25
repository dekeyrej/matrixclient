import arrow
import json
from PIL import Image, ImageFont, ImageDraw
from rgbleddisplay import RGBLEDDisplay
import logging
import sys
import os
cwd = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/rpi-rgb-led-matrix/bindings/python'))

class CalendarEvent(RGBLEDDisplay):
    def __init__(self, matrix=None):
        super().__init__(matrix=matrix)
        if matrix is not None:
            from rgbmatrix import RGBMatrix
            self.matrix = True
        else:
            self.matrix = False
        self.type = 'Calendar'
        # self.values = []
        self.icon = None
        # print(os.getcwd())
        # print(os.listdir())
        layer = 1
        w = os.walk('/home/pi/matrixclient/fonts')
        for (dirpath, dirnames, filenames) in w:
            print(filenames)
            layer += 1
        self.font = ImageFont.load(filename='fonts/5x7.pil',)
        self.calendarico = Image.open("img/calendarico.bmp")
        self.garbage_night = '2' # for Tuesday
        self.is_garbage_out = False
        
    def garbage_out(self, state):
        self.is_garbage_out = state
    
    def display(self):
        # if self.data_dirty:
        self.icon = Image.new("RGB", (128,64))
        draw = ImageDraw.Draw(self.icon)
        if self.values is not None:
            #---------------------------------------------------------------
            t = arrow.now()
#         t = datetime.datetime(2022,10,6,14,0,0)  ## jammed date/time for testing
            dateStr = t.format("MMM DD - hh:mm A").upper()
            fourthLine = ""
            count = len(self.values['values'])
            active = False   # true if a meeting is currently in progress
            upcoming = False # true if there is another meeting upcoming today
            if count > 0 and self.values['values'] != ["No events"]:
                for event in self.values['values']:
                    start = self.stringToTime(event[1])
                    end   = self.stringToTime(event[2])
                    if t > start and t < end:  # in this event
                        if event[0][4:].lower() == "talking": color = "Red"
                        elif event[0][4:].lower() == "some talking": color = "Orange"
                        else: color = "Yellow"
                        top_line =    "MEETING UNTIL {}".format(end.format('hh:mm A'))
                        active = True
                        break
                
                if not active:
                    color = "Turquoise"
                    for event in self.values['values']:
                        start = self.stringToTime(event[1])
                        end   = self.stringToTime(event[2])
                        if t < start:
                            top_line =    "NEXT MEETING AT {}".format(start.format('hh:mm A'))
                            fourthLine = "{} AT {}".format(event[0][4:], start.format('hh:mm A'))
                            upcoming = True
                            break
                else:
                    for event in self.values['values']:
                        start = self.stringToTime(event[1])
                        end   = self.stringToTime(event[2])
                        if t < start:
                            fourthLine =    "{} AT {}".format(event[0][4:], start.format('hh:mm A'))
                            upcoming = True
                            break

                ### arrow.format('d') returns '1','2','3',..'7', where '1' = Monday
                if not upcoming and not active:
                    if t.format('d') != self.garbage_night:
                        self.is_garbage_out = False
                        color = "Green"
                        top_line =     "NO MORE MEETINGS :)"
                    else:
                        if self.is_garbage_out == False:
                            color = "Red"
                            top_line   =     "!!!!!!!!!!!!!!!!!!!!!!!!!"
                            fourthLine =     "GARBAGE NIGHT!!!"
                        else:
                            color = "Green"
                            top_line =     "NO MORE MEETINGS :)"
            else: # count == 0
                if t.format('d') != self.garbage_night:
                    self.is_garbage_out = False
                    color = "Blue"
                    top_line =     "NO MEETINGS TODAY!!"
                else:
                        if self.is_garbage_out == False:
                            color = "Red"
                            top_line   =     "!!!!!!!!!!!!!!!!!!!!!!!!!"
                            fourthLine =     "GARBAGE NIGHT!!!"
                        else:
                            color = "Blue"
                            top_line =     "NO MEETINGS TODAY!!"
            #---------------------------------------------------------------
            draw.rectangle([(0,24),(127,63)],fill=color, outline=color,width=1)
            self.icon.paste(self.calendarico, box=(1,0))
            draw.text((17, 3), dateStr,     font = self.font, fill='white')
            draw.text((1, 14), top_line,    font = self.font, fill='white')
            if fourthLine != "":
                draw.rectangle([(0,37),(127,48)],fill='black', outline='black',width=1)
                x, y = self.justify(fourthLine.upper(), self.font, 64, 44, 'MC')
                draw.text((x, y), fourthLine.upper(), font = self.font, fill='white')
        else:
            draw.text(( 1,  2), "No calendar data received.", font = self.font, fill='white')
        if self.is_paused:
            draw.line(((125,0),(125,2)), fill='White', width=1)
            draw.line(((127,0),(127,2)), fill='White', width=1)
        self.icon.save("static/calendar.bmp", "BMP")
        self.dirty = True
        self.data_dirty = False
        if self.matrix:
            self.my_canvas.Clear()
            self.my_canvas.SetImage(self.icon,0,0)
            return self.my_canvas
        
    def stringToTime(self,isostring):  #accepts an ISO date/time string and returns a time object based on the hour and minute (sets seconds to 0)
        return arrow.get(isostring).floor('second')