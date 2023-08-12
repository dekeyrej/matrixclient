import arrow
from PIL import Image, ImageFont, ImageDraw
from pages import DisplayPage
import textwrap

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/rpi-rgb-led-matrix/bindings/python'))

class CurrentWeather(DisplayPage):
    def __init__(self,dba, matrix=None):
        super().__init__(dba, matrix)
        if matrix is not None:
            from rgbmatrix import RGBMatrix
            self.matrix = True
        else:
            self.matrix = False
        # self.event = 'weather_event'
        # self.no_event = 'no_weather_event'
        self.aqi_values = None
        self.type = 'Weather'
        self.font    = ImageFont.load(r'fonts/5x7.pil')
        self.smfont  = ImageFont.load(r'fonts/4x6.pil')
        self.bgfont  = ImageFont.load(r'fonts/6x10.pil')
        self.weatherfont = ImageFont.truetype(r'fonts/owfont-regular.ttf', 32)
        self.icon = None

    def update(self): # implements a back off mechanism for stale messages
        """ Reads a record of self.type, 
            if it returns a new record (Happy)
            else backs off and tries again
            !!! Back off doesn't work right ;-/ !!!
        """
        self.values = self.dba.read(self.type)
        self.aqi_values = self.dba.read('AQI')['values']
        # print(self.aqi_values)
        if self.values is not None: # got good data
            self.values['valid'] = self.fix_edt(self.values['valid'])
            next = arrow.get(self.values['valid'],'MM/DD/YYYY h:mm:ss A ZZZ') # next holds the new validity date
            if self.nextUpdate == next.shift(minutes=+self.offsetCounter): # we got a stale message
                self.offsetCounter += 1
                self.nextUpdate = next.shift(minutes=+self.offsetCounter) #check again in 1 minute
            else: # we got a new message/validty time
                self.nextUpdate = next # update the next update to the new time
                self.offsetCounter = 1

    def string_to_tuple(self, str):
        tuplestr = str.replace('(','').replace(')','').split(',')
        return (int(tuplestr[0]), int(tuplestr[1]), int(tuplestr[2]))

    def display(self):
        self.icon = Image.new("RGB", (128,64))
        draw = ImageDraw.Draw(self.icon)
        if self.values is not None:
            if self.values['values']['current']['nwid'] == 60800:
                draw.text((0,16), chr(self.values['values']['current']["nwid"]), font = self.weatherfont, embedded_color=True, fill='yellow')
            else:
                draw.text((0,16), chr(self.values['values']['current']["nwid"]), font = self.weatherfont, embedded_color=True)
            draw.text((1,1), "Wind:{:3.0f} {}".format(self.values['values']['current']["windSpeed"], self.values['values']['current']["windDir"]), font = self.font)
            if self.values['values']['current']["windGust"] != 0: draw.text((1,8), "Gusts:{:>2.0f}".format(self.values['values']['current']["windGust"]), font = self.font)
            draw.text((29, 18), "{:>3.0f}°F".format(self.values['values']['current']["temp"]), font = self.bgfont)
            draw.text((29, 31), "{:>3}%".format(self.values['values']['current']["humid"]), font = self.bgfont)
            draw.text(( 7, 47), "Feels", font = self.smfont)
            draw.text(( 7, 54), "like:", font = self.smfont)
            draw.text((29, 49), "{:>3.0f}°F".format(self.values['values']['current']["fl"]), font = self.bgfont)
            # AQI Stuff
            aqi_colors = [(0,228,0), (255,255,0), (255,126,0), (255,0,0), (143,63,151), (126,0,35)]
            color = self.string_to_tuple(self.aqi_values['color'])
            # print(color)
            score = self.aqi_values['aqi_score']
            adjective = self.aqi_values['aqi_adjective']
            pollutant = self.aqi_values['main_pollutant']
            if adjective != 'Good':
                adjective = f'{adjective} - {pollutant}'
            # draw scale bar
            j = 0
            for ac in aqi_colors:
                draw.rectangle([(65+j*10,0),(75+j*10,3)], fill=ac, outline=ac, width=1)
                j += 1
            draw.ellipse([(85,7),(105,27)], fill=color, outline=color)
            xout, yout = self.justify(str(score),self.bgfont, 96, 18, 'MC')
            draw.text((xout, yout), str(score), font=self.bgfont)
            i = 0
            for line in textwrap.wrap(adjective, width=12, max_lines=4):
                xout, yout = self.justify(line,self.font, 95, 34 + i * 9, 'MC')
                draw.text((xout, yout), line, font=self.font)
                i += 1
            # end AQI stuff
        else: # no weather data received
            draw.text(( 1,  2), "No weather data received.", font = self.font, fill='white')
        if self.is_paused:
            draw.line(((125,0),(125,2)), fill='White', width=1)
            draw.line(((127,0),(127,2)), fill='White', width=1)
        self.icon.save("static/thumb.bmp", "BMP")
        self.dirty = True
        if self.matrix:
            self.my_canvas.Clear()
            self.my_canvas.SetImage(self.icon,0,0)
            return self.my_canvas
