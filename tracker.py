import arrow
from PIL import Image, ImageFont, ImageDraw
from plain_pages.displaypage import DisplayPage

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/rpi-rgb-led-matrix/bindings/python'))

class GarminDisplay(DisplayPage):
    def __init__(self, dba, matrix=None):
        super().__init__(dba, matrix)
        if matrix is not None:
            from rgbmatrix import RGBMatrix
            self.matrix = True
        else:
            self.matrix = False
        self.type = 'Track'
        self.font    = ImageFont.load(r'fonts/5x7.pil')
        self.smfont  = ImageFont.load(r'fonts/4x6.pil')
        self.bgfont  = ImageFont.load(r'fonts/6x10.pil')
        self.icon = None

    def display(self):
        if self.data_dirty:
            self.icon = Image.new("RGB", (128,64))
            draw = ImageDraw.Draw(self.icon)
            if self.values is not None:
                self.udateTime = arrow.get(self.values['values']['Time'],'M/D/YYYY h:mm:ss A').shift(minutes=+10)
                lines = []
                lines.append('{:>18}'.format(self.shortentime(self.values['values']['Time'])))
                lines.append(" {}'s location -".format(self.values['values']['Name'].split()[0]))
                lines.append('   Lat: {}'.format(self.humanlat(self.values['values']['Latitude'])))
                lines.append('   Lon: {}'.format(self.humanlon(self.values['values']['Longitude'])))
                lines.append('   {:>3} @ {:>5.2f} kts'.format(self.values['values']['Course'], self.values['values']['Velocity']))
                
                for i in range(len(lines)):
                    # print(lines[i])
                    draw.text((1,5+ i*11), lines[i], font = self.bgfont)
            if self.is_paused:
                draw.line(((125,0),(125,2)), fill='White', width=1)
                draw.line(((127,0),(127,2)), fill='White', width=1)
            self.icon.save("static/garmin.bmp", "BMP")
            self.data_dirty = False
        if self.matrix:
            self.my_canvas.Clear()
            self.my_canvas.SetImage(self.icon,0,0)
            return self.my_canvas

    def humanlat(self, latstr):
        lat = float(latstr)
        if lat > 0:
            ns = 'N'
        elif lat < 0:
            ns = 'S'
        else:
            ns = ' '
        return ' {:>7.3f} {}'.format(lat, ns)

    def humanlon(self, lonstr):
        lon = float(lonstr)
        if lon > 0:
            ew = 'E'
        elif lon < 0:
            ew = 'W'
            lon = -1 * lon
        else:
            ew = ' '
        return '{:>8.3f} {}'.format(lon, ew)

    def shortentime(self, timestr):
        return arrow.get(timestr,'M/D/YYYY h:mm:ss A').format('M/D/YYYY h:mmA')