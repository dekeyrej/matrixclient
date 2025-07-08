"""
MOON PHASE CLOCK for Adafruit Matrix Portal: displays current time, lunar
phase and time of next moonrise or moonset. Requires WiFi internet access.

Written by Phil 'PaintYourDragon' Burgess for Adafruit Industries.
MIT license, all text above must be included in any redistribution.

BDF fonts from the X.Org project. Startup 'splash' images should not be
included in derivative projects, thanks. Tall splash images licensed from
123RF.com, wide splash images used with permission of artist Lew Lashmit
(viergacht@gmail.com). Rawr!

Adapted to the rpi-rgb-led-matrix python bindings by JSD
"""
# import requests
import json
import arrow

from PIL import Image, ImageFont, ImageDraw
from rgbleddisplay import RGBLEDDisplay
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/rpi-rgb-led-matrix/bindings/python'))

class MoonDisplay(RGBLEDDisplay):
    def __init__(self, matrix=None, twelve=True):
        super().__init__(matrix=matrix)
        if matrix is not None:
            from rgbmatrix import RGBMatrix
            self.matrix = True
        else:
            self.matrix = False
        self.type = 'Moon'
        self.smfont  = ImageFont.load(r'fonts/helvR10.pil')
        self.sm2font = ImageFont.load(r'fonts/6x10.pil')
        self.lgfont  = ImageFont.load(r'fonts/helvB12.pil')
        self.TWELVE_HOUR = twelve
        self.moonPhases = self.loadPhases()
        self.icon = None
       
    def display(self):
        if self.data_dirty:
            self.icon = Image.new("RGB", (128,64))
            draw = ImageDraw.Draw(self.icon)
            if self.values is not None:
                t = arrow.now()
                if self.TWELVE_HOUR:
                    timestr = t.format('h:mm:ss A')
                else:
                    timestr = t.format('HH:mm:ss')
                datestr = t.format('MM-DD-YY')
                self.icon.paste(self.moonPhases[self.values['values']['phase']], box=(1,1))
                
                if len(self.values['values']["illumstr"]) < 5:
                    illoff = 8
                else:
                    illoff = 2
                
                illumstr = self.values['values']["illumstr"]
                draw.text((illoff+1, 10+1), illumstr,              font = self.smfont, fill='black')
                draw.text((illoff+1, 10-1), illumstr,              font = self.smfont, fill='black')
                draw.text((illoff-1, 10+1), illumstr,              font = self.smfont, fill='black')
                draw.text((illoff-1, 10-1), illumstr,              font = self.smfont, fill='black')
                draw.text((illoff  , 10),   illumstr,              font = self.smfont, fill='yellow')
                draw.text((46      , 0),    datestr,               font = self.smfont, fill='white')
                draw.text((46      , 15),   timestr,               font = self.lgfont, fill='white')
                draw.text((15      , 45),   self.values['values']["sunevent"],         font = self.sm2font, fill='orange')
                draw.text((15      , 55),   self.values['values']["moonevent"],        font = self.sm2font, fill='silver')
            else: # no moon data received
                draw.text(( 1,  2), "No moon data received.", font = self.font, fill='white')
            if self.is_paused:
                draw.line(((125,0),(125,2)), fill='White', width=1)
                draw.line(((127,0),(127,2)), fill='White', width=1)
            self.icon.save("static/moon.bmp", "BMP")
            self.dirty = True
            self.data_dirty = True  # updates the display 1/second
        if self.matrix:
            self.my_canvas.Clear()
            self.my_canvas.SetImage(self.icon,0,0)
            return self.my_canvas

    def loadPhases(self):
        moonPhases = []
        for i in range(0,100):
            moonPhases.append(Image.open("img/moon/moon" + '{:02}'.format(i) + ".bmp"))
        return moonPhases

