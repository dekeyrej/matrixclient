#!/usr/bin/env python
# clientdisplay.py
#    Vision: Refactor matrix display into a websocket connected client that consumes all of the data for:
#       - 'Realtime' clock - complete (no server required)
#       - Google Calendar Events - complete
#       - Family event display - complete (no server required)
#       - Current Weather (all weather displays share one server feed) - complete
#       - Hourly Weather  - complete
#       - Forecast Weather  - complete
#       - Moon/Sun display - complete
#       - Major League Baseball (ESPN-hosted data feed) - complete
#       - National Football League (ESPN-hosted data feed) - <to be redone next season>
#       - World Cup 2022 - <to be redone in 4 years>
#    Udpates all of the internet-driven datasets for the matrix display. Optimizes update frequency,
#    converts/reformats all incoming data to be 'display ready', broadcasts the display-ready data via Websockets.

# Todo: add back in the webpage display/configuration of displays, etc.

import argparse
import json
import time
import arrow
import sys
import os

import dotenv
import redis

from datasourcelib   import Database          # wrapper for postgres/cockroach/sqlite/mongodb

from clock           import Clock
from calevent        import CalendarEvent
from nextevent       import NextEvent
from currentweather  import CurrentWeather
from hourlyweather   import HourlyWeather
from forecastweather import ForecastWeather
from moondisplay     import MoonDisplay
from mlbdisplay      import MLBDisplay
from tracker         import GarminDisplay
from uptime          import Uptime
from wifi            import WiFi
# from nfl             import NFLDisplay
# from wcdisplay       import WorldCupDisplay

class Matrix(object):
    
    def __init__(self):
        dotenv.load_dotenv()
        """
        Expecting the following variables in the environment:
        PROD=2 (prod) or 1 (test) or 0 (dev)
        SECRETS_PATH="secrets.json"
        """
        try:
            PROD = os.environ["PROD"]
            print(PROD)
            if PROD   == '2':
                self.env = 'prod'
            elif PROD == '1':
                self.env = 'test'
            else:
                self.env = 'dev'
            SECRETS_PATH     = os.environ["SECRETS_PATH"]
        except KeyError as err:
            print(f'KeyError: {err}')
            raise

        self.secrets = self.read_secrets(SECRETS_PATH)
        db_params = {"user":      self.secrets['dbuser'], 
                     "pass":      self.secrets['dbpass'], 
                     "host":      self.secrets['dbhost'][self.env], 
                     "port":      self.secrets['dbport'][self.env], 
                     "db_name":  'matrix', 
                     "tbl_name": 'feed'}
        self.dba = Database(self.secrets['dbtype'], db_params)
        if PROD == '2':  # Production
            pass
            # self.write_start_record()
        # setup redis connection
        if self.secrets['rpass'][self.env] == 'None':
            self.r = redis.Redis(host=self.secrets['rhost'][self.env], port=6379, db=0, decode_responses=True)
        else:
            self.r = redis.Redis(host=self.secrets['rhost'][self.env], port=6379, db=0, decode_responses=True, 
                                 password=self.secrets['rpass'][self.env])
        self.p = self.r.pubsub()
        self.p.subscribe('webcontrol', 'update')
        self.running = True
        # list of displays
        self.displays = []
        self.modules = {}
        self.config = []
        self.display = 0
        self.displayCount = 1

    def read_secrets(self,path):
        with open(path) as file:
            newsecrets = json.loads(file.read())
            file.close()
        return newsecrets
        
    def write_start_record(self):
        # Write Startup record to database
        tnow = arrow.now()
        data = {}
        data['type']   = 'Client'
        data['updated'] = tnow.to('US/Eastern').format('MM/DD/YYYY h:mm A ZZZ')
        data['valid']   = tnow.to('US/Eastern').format('MM/DD/YYYY h:mm:ss A ZZZ')
        data['values'] = {'some': 'values'}
        # print(json.dumps(data,indent=2))
        self.dba.write(data)
    
    # start redis command interface
    ## steps backwards 1 display
    def back_step(self):
        if not self.running:
            self.displays[self.display][0].data_dirty = True
            self.displays[self.display][0].is_paused = False
            self.display = (self.display - 1) % self.displayCount
            self.displays[self.display][0].data_dirty = True
            self.displays[self.display][0].is_paused = True
            offscreen_canvas = self.displays[self.display][0].display()
            if self.matrix is not None:
                offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
    
    ## toggles play state (whether to advance the displays)
    def playPause(self):
        # acion to take on redis-delivered command 'pp'
        self.running = not self.running
        self.displays[self.display][0].data_dirty = True
        self.displays[self.display][0].is_paused = not self.running
        offscreen_canvas = self.displays[self.display][0].display()
        if self.matrix is not None:
            offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
    
    ## steps forwards 1 display
    def forward_step(self):
        if not self.running:
            self.displays[self.display][0].data_dirty = True
            self.displays[self.display][0].is_paused = False
            self.display = (self.display + 1) % self.displayCount
            self.displays[self.display][0].data_dirty = True
            self.displays[self.display][0].is_paused = True
            offscreen_canvas = self.displays[self.display][0].display()
            if self.matrix is not None:
                offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)

    ## forces a reload of the display configuration
    def reload_displays(self):
        # action to take on redis-delivered command 'reload'
        self.loadConfig()
        self.buildDisplays()

    ## list of command names and the associated subroutines
    commands = {'reload': reload_displays, 'pp': playPause, 'rew': back_step, 'fwd': forward_step}

    ## find the display(s) concerned with a particular 'rectype'
    def find_displays_by_type(self,tag):
        ret = []
        for i in range(self.displayCount):
            # print(f"{i}: {type(self.displays[i][0])}")
            if self.displays[i][0].type == tag:
                # print('Found it!')
                # return i
                ret.append(i)
        if ret != []:
            return ret
        return None

    ## reads the redis key, matches the command name, and executes the associated subroutine
    def check_redis_command(self):
        # cmd = self.r.getdel('command')
        cmd = self.p.get_message(ignore_subscribe_messages=True, timeout=0.01)
        if cmd is not None:
            # print(cmd)
            if cmd['channel'] == 'webcontrol':
                try:
                    self.commands[cmd['data']](self)
                except KeyError:
                    print(f"Unknown control [{cmd['data']}]")
            elif cmd['channel'] == 'update':
                try:
                    displaylist = self.find_displays_by_type(cmd['data'])
                    if displaylist is not None:
                        for display in displaylist:
                            # print(display)
                            print(f"{cmd['data']}: {type(self.displays[display][0])}")
                            self.displays[display][0].update()
                except KeyError:
                    print(f"Unknown update [{cmd['data']}]")
            else:
                print(f"Unknown message [{cmd}]")

    # end redis commmand interface

    def parseCL(self):
        parser = argparse.ArgumentParser()
         # app arguments
        parser.add_argument("-i", "--init-rgb", action="store", help="Initialize an RGB Matrix Display. Default: 0 (no RGB display)", default=0, type=int)
        # rgbmatrix arguments   
        parser.add_argument("-r", "--led-rows", action="store", help="Display rows. 16 for 16x32, 32 for 32x32. Default: 32", default=32, type=int)
        parser.add_argument("--led-cols", action="store", help="Panel columns. Typically 32 or 64. (Default: 64)", default=64, type=int)
        parser.add_argument("-c", "--led-chain", action="store", help="Daisy-chained boards. Default: 4.", default=4, type=int)
        parser.add_argument("-P", "--led-parallel", action="store", help="For Plus-models or RPi2: parallel chains. 1..3. Default: 1", default=1, type=int)
        parser.add_argument("-b", "--led-brightness", action="store", help="Sets brightness level. Default: 100. Range: 1..100", default=100, type=int)
        parser.add_argument("-m", "--led-gpio-mapping", help="Hardware Mapping: regular, adafruit-hat, adafruit-hat-pwm" , default='adafruit-hat', choices=['regular', 'regular-pi1', 'adafruit-hat', 'adafruit-hat-pwm'], type=str)
        parser.add_argument("--led-pixel-mapper", action="store", help="Apply pixel mappers. e.g \"Rotate:90\"", default="U-mapper", type=str)
        parser.add_argument("--led-show-refresh", action="store", help="Shows the current refresh rate of the LED panel")
        # parser.add_argument("--led-show-refresh", action="store_true", help="Shows the current refresh rate of the LED panel")
        parser.add_argument("--led-slowdown-gpio", action="store", help="Slow down writing to GPIO. Range: 0..4. Default: 4", default=4, type=int) # 2 works pretty well for a pi3A+, 4 for a pi4b
        parser.add_argument("--led-no-hardware-pulse", action="store", help="Don't use hardware pin-pulse generation")
        parser.add_argument("--led-rgb-sequence", action="store", help="Switch if your matrix has led colors swapped. Default: RGB", default="RGB", type=str)
        parser.add_argument("-p", "--led-pwm-bits", action="store", help="Bits used for PWM. Something between 1..11. Default: 11", default=11, type=int)
        parser.add_argument("--led-pwm-lsb-nanoseconds", action="store", help="Base time-unit for the on-time in the lowest significant bit in nanoseconds. Default: 130", default=130, type=int)
        parser.add_argument("--led-scan-mode", action="store", help="Progressive or interlaced scan. 0 Progressive, 1 Interlaced (default)", default=1, choices=range(2), type=int)        
        # mlb arguments
        parser.add_argument("-t", action="store", help="2/3 letter abbreviation for the MLB team to display. BOS, TB, NYY. Befault: BOS", default="BOS", type=str)
        parser.add_argument("--enable-cycle", action="store_true", help="Enable cycling through all daily games when selected team's game is not in progress")
        return parser.parse_args()
           
    def initMatrix(self, clargs):
        sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/rpi-rgb-led-matrix/bindings/python'))
        from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

        # Configuration for the matrix
        options = RGBMatrixOptions()
        options.rows = clargs.led_rows
        options.cols = clargs.led_cols
        options.chain_length = clargs.led_chain
        options.parallel = clargs.led_parallel
        options.brightness = clargs.led_brightness
        options.hardware_mapping = clargs.led_gpio_mapping  # If you have an Adafruit HAT: 'adafruit-hat'
        options.pixel_mapper_config = clargs.led_pixel_mapper # "U-mapper;Rotate:180"
        if clargs.led_show_refresh is not None:
            options.show_refresh_rate = True
        if clargs.led_slowdown_gpio != None:
            options.gpio_slowdown = clargs.led_slowdown_gpio
        if clargs.led_no_hardware_pulse:
            options.disable_hardware_pulsing = True
    #         options.disable_hardware_pulsing = True   # force = True for running inside Thonny (don't have to run as root)
        options.led_rgb_sequence = clargs.led_rgb_sequence
        options.pwm_bits = clargs.led_pwm_bits
        options.pwm_lsb_nanoseconds = clargs.led_pwm_lsb_nanoseconds
        options.scan_mode = clargs.led_scan_mode

        return RGBMatrix(options = options)
    
    def buildDisplays(self):
#         list of tuples [(display object, how long to display the object befor cycling, how many "frames" it can display), (..)]
#         self.displays = [(clock,5,5), (cal,5,1), (nextevent,5,1),
#                          (cweather,5,1), (hweather,5,1), (fweather,5,1),
#                          (moon,5,5), (mlb,5,1), (nfl,15,5), (wc, 12, 4)]
        displays = []
        try:
            for item in self.config:
                displays.append((self.modules[item['Page']],item['Time'],item['Frames']))
            self.displays = displays
        except:
            print("Exception  in buildDisplays()")
        self.displayCount = len(self.displays)
        self.display = self.displayCount - 1
    
    def saveConfig(self):
        config = {}
        config['type']    = 'Display Config'
        config['updated'] = arrow.now().to('US/Eastern').format('MM/DD/YYYY h:mm A ZZZ')
        config['valid']   = arrow.now().shift(hours=+1).to('US/Eastern').format('MM/DD/YYYY h:mm:ss A ZZZ')
        config['values']  = self.config
        self.dba.write(config)
        
    def loadConfig(self):
        res = self.dba.read('Display Config')
        if res is not None:
            self.config = res['values']
        
    def loadDefaultConfig(self):
        res = self.dba.read('Default Config')
        if res is not None:
            self.config = res['values']

    def run(self):
        db = self.dba
        args = self.parseCL()
        self.matrix = None
        if args.init_rgb > 0:
            self.matrix = self.initMatrix(args)
            offscreen_canvas = self.matrix.CreateFrameCanvas()

        ## Instantiate display classes and add them the event_type dictionary
        # from <source> import <Classname>
        # self.modules['<Config Name>'] = <Classname>(db, self.matrix)
        self.modules['Clock'] = Clock(db, self.matrix, seconds=True)
        self.modules['Weekly Calendar'] = CalendarEvent(db, self.matrix)
        self.modules['Next Family Event'] = NextEvent(db, self.matrix)
        self.modules['Current Weather'] = CurrentWeather(db, self.matrix)
        self.modules['Hourly Weather'] = HourlyWeather(db, self.matrix)
        self.modules['Forecast Weather'] = ForecastWeather(db, self.matrix)
        self.modules['Moon Display'] = MoonDisplay(db, self.matrix)
        self.modules['MLB'] = MLBDisplay(db, self.matrix, team='BOS')
        self.modules['Track'] = GarminDisplay(db, self.matrix)
        self.modules['Uptime'] = Uptime(db, self.matrix)
        self.modules['WiFi'] = WiFi(db, self.matrix, self.secrets['wifi_connect_string'])
        # self.modules['NFL'] = NFLDisplay(db, self.matrix)
        # self.modules['WC'] = WorldCupDisplay(db, self.matrix)
        ## end display classes
        
        self.loadConfig()
        self.buildDisplays()
        self.saveConfig()

        # update the display data once to get started
        for d in self.displays:
            d[0].check(arrow.now().to('US/Eastern'))

        lastds = 0
        dsint = self.displays[self.display][1]
        frame = 0
        lastfs = 0
        framect = self.displays[self.display][2]
        fsint = dsint / framect

        # Main loop which cycles between the displays
        while True:
            now = time.monotonic()
            # anow = arrow.now().to('US/Eastern')
            # check for redis-delivered command
            self.check_redis_command()
            # give the displays a chance to update their data
            # for d in self.displays:
            #      d[0].check(anow)
            if lastds == 0 or now - lastds > dsint:
                if self.running: self.display = (self.display + 1) % self.displayCount
                dsint = self.displays[self.display][1]
                framect = self.displays[self.display][2]
                fsint = dsint / framect
                frame = 0
                lastds = lastfs = now
                offscreen_canvas = self.displays[self.display][0].display()
                if self.matrix is not None:
                    offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
        #         print("Display: {}, Frame {} of {}".format(type(displays[display][0]).__name__,frame+1,framect))
            elif lastfs == 0 or now - lastfs > fsint:
                frame = (frame + 1) % framect
                lastfs = now
                offscreen_canvas = self.displays[self.display][0].display()
                if self.matrix is not None:
                    offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
            time.sleep(0.1)

m = Matrix()
m.run()
