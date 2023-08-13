import arrow
from PIL import Image, ImageFont, ImageDraw
from pages.displaypage import DisplayPage
import sys
import os
# sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/rpi-rgb-led-matrix/bindings/python'))

class Clock(DisplayPage):
    
    def __init__(self, dba, matrix, seconds=False):
        super().__init__(dba, matrix)
        if matrix is not None:
            # from rgbmatrix import RGBMatrix
            self.matrix = True
        else:
            self.matrix = False
        self.type = 'Clock'
#         self.clockFont   = ImageFont.load(r'/home/pi/fonts/t0-22-i01.pil')
#         self.ampmFont    = ImageFont.load(r'/home/pi/fonts/6x10.pil')
#         self.dateFont    = ImageFont.load(r'/home/pi/fonts/9x15.pil')
        self.clockFont   = ImageFont.truetype(r'fonts/DejaVuSans.ttf', 24)
        self.ampmFont    = ImageFont.truetype(r'fonts/DejaVuSans.ttf', 10)
        self.dateFont    = ImageFont.truetype(r'fonts/DejaVuSans.ttf', 16)
        self.seconds     = seconds

    def update(self):
        self.nextUpdate = arrow.now().shift(hours=+1)
        
    def display(self):
        if self.data_dirty:
            self.icon = Image.new("RGB", (128,64))
            draw = ImageDraw.Draw(self.icon)
            
            t = arrow.now()
    #         print(t.format("ZZ"))
            dateString = t.format("ddd D MMM").upper()
            if self.seconds:
                clockString = t.format("hh:mm:ss")
            else:
                clockString = t.format("hh:mm")
            ampm        = t.format("a")
            length = draw.textlength(clockString, font = self.clockFont)
            aplen = draw.textlength(ampm, font = self.ampmFont)
            cloff = (128 - (length + 3 + aplen))/2
            draw.text((cloff,1), clockString, fill = 'white', font = self.clockFont)
            draw.text((cloff+length+3,3), ampm, fill = 'white', font = self.ampmFont)
            offset = (128 - draw.textlength(dateString, font = self.dateFont))/2
            draw.text((offset,33), dateString, fill = 'white', font = self.dateFont)
            if self.is_paused:
                draw.line(((125,0),(125,2)), fill='White', width=1)
                draw.line(((127,0),(127,2)), fill='White', width=1)
            self.icon.save("static/clock.bmp", "BMP")
        if self.matrix:
            self.my_canvas.Clear()
            self.my_canvas.SetImage(self.icon,0,0)
            return self.my_canvas