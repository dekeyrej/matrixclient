from PIL import Image, ImageFont, ImageDraw
import json
import arrow
from pages import DisplayPage

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/rpi-rgb-led-matrix/bindings/python'))

class NextEvent(DisplayPage):
    
    def __init__(self, dba, matrix=None):
        super().__init__(dba, matrix)
        if matrix is not None:
            from rgbmatrix import RGBMatrix
            self.matrix = True
        else:
            self.matrix = False
        self.font    = ImageFont.load(r'fonts/7x13B.pil')
        self.line = list(("","","",""))
        self.icon = None
        self.type = 'Family'
        # f = open("events.txt")
        # self.events = json.loads(f.read())
        # f.close()
        
    def display(self):
        self.icon = Image.new("RGB", (128,64))
        # today = arrow.now().shift(days=+2)  # to forward test
        today = arrow.now()
        self.tz = today.format('ZZZ') # extract local timezone
        for e in self.values['values']:
            days, nextYear = self.daysToNext(e["month"],e["day"],today)
            e.update({'days'  : days})
            e.update({'nyear' : nextYear})
        
        def key(e):
            return e['days']      
        self.values['values'].sort(reverse=False, key=key)
         
        count = self.values['values'][0]["nyear"] - self.values['values'][0]["year"]
        suffix = self.suffix(count % 10)
        
        self.line[0] = "{}'s".format(self.values['values'][0]['name'])
        self.line[1] = "{}{} {}".format(count, suffix, self.values['values'][0]['event'])
        if self.values['values'][0]['days'] == 0:
            self.line[2] = "is TODAY!!!"
        else:
            self.line[2] = "in {} days".format(self.values['values'][0]['days'])
        self.line[3] = arrow.get(self.values['values'][0]['nyear'],self.values['values'][0]['month'],self.values['values'][0]['day']).format('MM/DD/YYYY')
        draw = ImageDraw.Draw(self.icon)
        for i in range(4):
            length = draw.textlength(self.line[i], font=self.font)
            off = (128 - length)/2
            draw.text((off,i * 15 + 2), self.line[i], fill = 'white', font = self.font)
        if self.is_paused:
            draw.line(((125,0),(125,2)), fill='White', width=1)
            draw.line(((127,0),(127,2)), fill='White', width=1)
        #----------------------------------
        self.icon.save("static/thumb.bmp", "BMP")
        self.dirty = True
        if self.matrix:
            self.my_canvas.Clear()
            self.my_canvas.SetImage(self.icon,0,0)
            return self.my_canvas
    
    def suffix(self,num):
        if num == 1:
            return 'st'
        elif num == 2:
            return 'nd'
        elif num ==3:
            return 'rd'
        else:
            return 'th'
        
    def daysToNext(self,mon,day,today):
        year = today.year
        eday = arrow.get(year,mon,day,tzinfo=self.tz) # create event day in local timezone (#$@!@$$ default is UTC)
#         print('today = {}, next day = {}'.format(today,eday))
        days = (eday - today).days
        if days < -1:
            year += 1
            eday = eday.replace(year=year)
            days = (eday - today).days
        return days + 1, year