import arrow
import json
from PIL import Image, ImageFont, ImageDraw
import re
from rgbleddisplay import RGBLEDDisplay
import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/rpi-rgb-led-matrix/bindings/python'))

class Uptime(RGBLEDDisplay):
    def __init__(self, matrix=None):
        super().__init__(matrix=matrix)
        if matrix is not None:
            from rgbmatrix import RGBMatrix
            self.matrix = True
        else:
            self.matrix = False
        self.type = 'Client'
        self.server_stats = {}
        self.icon = None
        self.font = ImageFont.load(r'fonts/5x7.pil')
        tnow = arrow.now()
        self.values = {
            'type': 'Client', 
            'updated': f"{tnow.to('America/New_York').format('MM/DD/YYYY h:mm A Z')}", 
            'valid': f"{tnow.to('America/New_York').format('MM/DD/YYYY h:mm A Z')}", 
            'values': {'some':'stuff'}}

    def check(self, now):
        pass

    # maybe switch these two? using update_server for the bulk upload and update for the single updates?
    # would but Client in the key_map, simplifying the update logic
    def update_server(self, update_data):
        logging.info(f"Update received for {update_data['type']}: {update_data}")
        if update_data['type'] == self.type:
            self.values = update_data
        elif re.search('-Server', update_data['type']):
            key = re.sub('-Server', '', update_data['type'])
            self.server_stats[key] = update_data['updated']
            logging.info(f"Update for {key} received: {self.server_stats[key]}")
        else:
            logging.warning(f"Update data type {update_data['type']} does not match display type {self.type}")
        self.data_dirty = True  # set to true so we redraw the display

    def update(self, update_data):
        """ Bulk upload of current server uptime data. """
        logging.debug(f"Bulk update received for server uptime: {update_data}")
        for update in update_data:
            self.server_stats[update] = update_data[update]

    def display(self):
        self.icon = Image.new("RGB", (128,64))
        draw = ImageDraw.Draw(self.icon)
        tnow = arrow.now()
        dateStr    = tnow.format("MMM DD - hh:mm A").upper()
        
        # Client data
        first_line   = "Client has been up for"
        # self.values = self.dba.read('Client')
        if self.values is not None:
            client_start_time = arrow.get(self.values['updated'],'MM/DD/YYYY h:mm A Z')
            second_line = f"{client_start_time.humanize(only_distance=True, granularity=['hour','minute'])}"
            # TODO: color proportional to magnitude of uptime
            # print(int(float(tnow.format('X')) - float(client_start_time.format('X'))))
            top_color = self.uptime_color(tnow, client_start_time) #"Green" # Red, Orange, Yellow, Turquise, Blue
        else:
            top_color = "Red"
            second_line = "No data received."
        
        # # Server data
        # third_line = "Server has been up for"
        # self.values = self.dba.read('Server')
        # if self.values is not None:
        #     server_start_time = arrow.get(self.fix_edt(self.values['updated']),'MM/DD/YYYY h:mm A ZZZ')
        #     fourth_line = f"{server_start_time.humanize(only_distance=True, granularity=['hour','minute'])}"
        #     # TODO: color proportional to magnitude of uptime
        #     bottom_color = self.uptime_color(tnow, server_start_time) # "Green" # Red, Orange, Yellow, Turquise, Blue
        # else:
        #     bottom_color = "Red"
        #     fourth_line = "No data received."

        # Microservice data
        # server_stats = self.dba.read_where()
        # print(json.dumps(server_stats, indent=2))
        i = 0
        for s in self.server_stats:
            row = i % 4
            if i < 4:
                col = 0
            else:
                col = 1
            # print(self.server_stats[s])
            server_start_time = arrow.get(self.server_stats[s],'MM/DD/YYYY h:mm A Z')
            color = self.uptime_color(tnow, server_start_time)
            # print(f'{s}: {color} -- row: {row}, col: {col} -- top left x, y: {(col * 64) + 10}, {(row * 8) + 33}')
            draw.rectangle([((col * 64) + 1,(row * 8) + 33),((col * 64) + 7,(row * 8) + 39)],fill=color,outline=color,width=1)
            x, y = self.justify(s, self.font, (col * 64) + 10, (row * 8) + 33, 'TL')
            # print(f'Bottom left x, y: {x}, {y}')
            draw.text((x, y), s, font = self.font, fill='white')
            i += 1
        # Draw the display
        draw.rectangle([(0,12),(127,31)],fill=top_color, outline=top_color,width=1)
        # draw.rectangle([(0,49),(127,63)],fill=bottom_color, outline=bottom_color,width=1)
        draw.text((17, 3), dateStr,     font = self.font, fill='white')
        x, y = self.justify(first_line, self.font, 64, 18, 'MC')
        draw.text((x, y), first_line,    font = self.font, fill='white')
        x, y = self.justify(second_line.upper(), self.font, 64, 27, 'MC')
        draw.text((x, y), second_line.upper(), font = self.font, fill='black')
        # x, y = self.justify(third_line, self.font, 64, 43, 'MC')
        # draw.text((x, y), third_line,    font = self.font, fill='white')
        # x, y = self.justify(fourth_line.upper(), self.font, 64, 57, 'MC')
        # draw.text((x, y), fourth_line.upper(), font = self.font, fill='black')
        if self.is_paused:
            draw.line(((125,0),(125,2)), fill='White', width=1)
            draw.line(((127,0),(127,2)), fill='White', width=1)
        self.icon.save("static/uptime.bmp", "BMP")
        self.dirty = True
        if self.matrix:
            self.my_canvas.Clear()
            self.my_canvas.SetImage(self.icon,0,0)
            return self.my_canvas
        
    def uptime_color(self, now, then):
        # print(int(float(tnow.format('X')) - float(client_start_time.format('X'))))
        time = int(float(now.format('X')) - float(then.format('X')))
        if time < 60 * 15:        # 15 minutes
            return "Orange"
        elif time < 60 * 30:      # 30 minutes
            return "Yellow"
        elif time < 60 * 60 * 1:  # 1 hour
            return "Green"
        elif time < 60 * 60 *  6: #  6 hours
            return "Turquoise"
        else:
            return "Blue"
