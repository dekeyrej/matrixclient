from PIL import Image, ImageFont, ImageDraw
from plain_pages.displaypage import DisplayPage
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/rpi-rgb-led-matrix/bindings/python'))

class HourlyWeather(DisplayPage):
    def __init__(self, dba, matrix=None):
        super().__init__(dba, matrix)
        if matrix is not None:
            from rgbmatrix import RGBMatrix
            self.matrix = True
        else:
            self.matrix = False
        # self.event = 'weather_event'
        # self.no_event = 'no_weather_event'
        # self.values = None
        self.type = 'Weather'
        self.font = ImageFont.load(r'fonts/5x7.pil')
        self.weatherfont = ImageFont.truetype(r'fonts/owfont-regular.ttf', 20)
        self.icon = None
        
    # def update(self,data):
    #     self.values = data["hourly"]

    def display(self):
        if self.data_dirty:
            self.icon = Image.new("RGB", (128,64))
            draw = ImageDraw.Draw(self.icon)
            if self.values is not None:
                # draw the weather icons
                for i in range (0,3):
                    if self.values['values']['hourly'][i]["nwid"] == 60800:
                        draw.text((25,(21*i)+1), chr(self.values['values']['hourly'][i]["nwid"]), font=self.weatherfont, fill='yellow')
                    else:
                        draw.text((25,(21*i)+1), chr(self.values['values']['hourly'][i]["nwid"]), font=self.weatherfont, fill='white')
                # separator lines
                for i in range (0,2):
                    draw.line([(0, 21 + i * 21), (98, 21 + i * 21)], fill='white', width=1)
                # draw the DoWs and temps
                for i in range(0,3):
                    draw.text(( 1,  2 + (21 * i)), "{}".format(self.values['values']['hourly'][i]["hour"]),         font = self.font, fill='white')
                    draw.text((45,  2 + (21 * i)), "TEMP: {:>3.0f}°F".format(self.values['values']['hourly'][i]["temp"]), font = self.font, fill='white')
                    draw.text((45, 11 + (21 * i)), "FEEL: {:>3.0f}°F".format(self.values['values']['hourly'][i]["feel"]), font = self.font, fill='white')
            else: # no weather data received
                draw.text(( 1,  2), "No weather data received.", font = self.font, fill='white')
            if self.is_paused:
                draw.line(((125,0),(125,2)), fill='White', width=1)
                draw.line(((127,0),(127,2)), fill='White', width=1)
            self.icon.save("static/hw.bmp", "BMP")
            self.dirty = True
            self.data_dirty = False
        if self.matrix:
            self.my_canvas.Clear()
            self.my_canvas.SetImage(self.icon,0,0)
            return self.my_canvas