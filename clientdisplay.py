"""
step 4 of the Redis-first chain. This process requests the initial state from api.py,
estblishes an SSE connection to api.py, and listens for updates - dumping them as they come in.
"""
import json
import logging
import asyncio
import aiohttp
import requests

from clock           import Clock
from wifi            import WiFi
from calevent        import CalendarEvent
from nextevent       import NextEvent
from currentweather  import CurrentWeather
from hourlyweather   import HourlyWeather
from forecastweather import ForecastWeather
from moondisplay     import MoonDisplay
from mlbdisplay      import MLBDisplay
from nfl             import NFLDisplay
from tracker         import GarminDisplay   # working, I think, but no data available on the feed
from uptime          import Uptime

from config          import Config

logging.basicConfig(level=Config.get('LOG_LEVEL', 'INFO'), format='%(asctime)s - %(levelname)s - %(message)s')

class ClientDisplay:
    def __init__(self):
        self.keys = ["AQI", "Events", "Track", "MLB", "Moon", "Calendar", "NFL", "Weather"] # , "GitHub", "WC"
        self.uptime_keys = ["AQI-Server", "Events-Server", "Track-Server", "MLB-Server", 
                "Moon-Server", "Calendar-Server", "NFL-Server", "Weather-Server"] #  ,"GitHub-Server", "WC-Server"]
        self.modules = {}
        self.display_config = []
        self.displays = []
        self.displayCount = 0
        self.display = 0
        self.running = True
        self.key_map = {}
        self.matrix = None

    def load_display_config(self):
        return [
            { "Page": "Clock", "Time": 5, "Frames": 5 },
            { "Page": "WiFi", "Time": 5, "Frames": 1 },
            { "Page": "Weekly Calendar", "Time": 5, "Frames": 1 },
            { "Page": "Next Family Event", "Time": 5, "Frames": 1 },
            { "Page": "Current Weather", "Time": 6, "Frames": 1 },
            { "Page": "Hourly Weather", "Time": 6, "Frames": 1 },
            { "Page": "Forecast Weather", "Time": 6, "Frames": 1 },
            { "Page": "Moon Display", "Time": 5, "Frames": 5 },
            { "Page": "MLB", "Time": 6, "Frames": 3 },
            { "Page": "Uptime", "Time": 6, "Frames": 1 }
            ]

    def buildModules(self):
        """
        Build the modules for the microclient display.
        """
        modules = {}
        try:
            modules['Clock'] = Clock(self.matrix, seconds=True)
            modules['WiFi'] = WiFi(self.matrix, connect_str=Config['WIFI_STR'])
            modules['Weekly Calendar'] = CalendarEvent(self.matrix)
            modules['Next Family Event'] = NextEvent(self.matrix)
            modules['Current Weather'] = CurrentWeather(self.matrix)
            modules['Hourly Weather'] = HourlyWeather(self.matrix)
            modules['Forecast Weather'] = ForecastWeather(self.matrix)
            modules['Moon Display'] = MoonDisplay(self.matrix)
            modules['MLB'] = MLBDisplay(self.matrix, team=Config.get('MLB_TEAM', 'BOS'))
            modules['NFL'] = NFLDisplay(self.matrix, team=Config.get('NFL_TEAM', ''))
            modules['Garmin'] = GarminDisplay(self.matrix)
            modules['Uptime'] = Uptime(self.matrix)
        except Exception as e:
            logging.error(f"Error building modules: {e}")
        return modules

    def buildDisplays(self):
    #         list of tuples [(display object, how long to display the object befor cycling, how many "frames" it can display), (..)]
    #         self.displays = [(clock,5,5), (cal,5,1), (nextevent,5,1),
    #                          (cweather,5,1), (hweather,5,1), (fweather,5,1),
    #                          (moon,5,5), (mlb,5,1), (nfl,15,5), (wc, 12, 4)]
            displays = []
            displayCount = 0
            display = 0
            try:
                for item in self.display_config:
                    logging.debug(f"Building display for {item['Page']} with time {item['Time']} and frames {item['Frames']}")
                    displays.append((self.modules[item['Page']],item['Time'],item['Frames']))
                displayCount = len(displays)
                logging.debug(f"Total displays: {displayCount}")
                display = displayCount - 1 if displayCount > 0 else 0
                logging.debug(f"Starting display index: {display}")
            except Exception as e:
                logging.error(f"Exception in buildDisplays(): {e}")
            return displays, displayCount, display

    def buildKeyMap(self):
        """
        Build a mapping of keys to modules.
        This is used to determine which modules to update based on the key received from the API.
        """
        return {
            "AQI": [self.modules['Current Weather']],
            "Events": [self.modules['Next Family Event']],
            "Track": [self.modules['Garmin']],
            "MLB": [self.modules['MLB']],
            "Moon": [self.modules['Moon Display']],
            "Calendar": [self.modules['Weekly Calendar']],
            "NFL": [self.modules['NFL']],
            "Weather": [self.modules['Current Weather'], self.modules['Hourly Weather'], self.modules['Forecast Weather']]
        }

    def fetch_initial_state(self) -> None:
        """
        Fetch the initial state from the API.
        """
        for key in self.keys:
            response = requests.get(f"{Config['API_URL']}/{key}")
            if response.status_code == 200:
                initial_state = response.json()
                update = {
                    'type': key,
                    'updated': initial_state.get('updated'),
                    'valid': initial_state.get('valid'),
                    'values': initial_state.get('values')
                }
                for module in self.key_map.get(key, []):
                    if hasattr(module, 'update'):
                        module.update(update)
                logging.debug(f"Initial state for {key}:", update)
            else:
                logging.error(f"Failed to fetch initial state for {key}.")
        """
        Assemble the initial state for uptime keys.
        """
        server_update = {}
        for key in self.uptime_keys:
            response = requests.get(f"{Config['API_URL']}/{key}")
            if response.status_code == 200:
                initial_state = response.json()
                if initial_state is not None and 'updated' in initial_state:
                    new_key = key.removesuffix('-Server')
                    server_update[new_key] = initial_state.get('updated')
                    logging.debug(f"Initial state for {key}:", server_update[new_key])
            else:
                logging.error(f"Failed to fetch initial state for {key}.")
        logging.debug(f"uptime_keys: {json.dumps(server_update, indent=2)}")
        self.modules['Uptime'].update(server_update)
        self.modules['Uptime'].display()

    def playPause(self):
            # acion to take on redis-delivered command 'pp'
            self.running = not self.running
            self.displays[self.display][0].data_dirty = True
            # displays[display][0].is_paused = not running
            offscreen_canvas = self.displays[self.display][0].display()
            if self.matrix is not None:
                offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)

    async def listen_forever(self):
        """
        Listen for updates from the API.
        This function is called in the main loop to keep the connection alive.
        """
        while True:
            try:
                await self.listen_for_updates()
            except Exception as e:
                logging.error(f"Error in listen_forever: {e}")
                await asyncio.sleep(5)

    async def listen_for_updates(self):
        timeout = aiohttp.ClientTimeout(connect=10, sock_read=None)
        async with aiohttp.ClientSession() as session:
            async with session.get(Config['EVENTS_URL'], timeout=timeout) as response:
                if response.status == 200:
                    async for line in response.content:
                        if line.decode("utf-8").strip().startswith("data:"):
                            update = json.loads(line.decode("utf-8").split("data: ")[1])
                            await self.handle_update(update)
                else:
                    logging.error(f"Failed to connect to {Config['EVENTS_URL']}. Status: {response.status}")

    async def handle_update(self, update):
        updatetype = update.get("type")
        if updatetype in self.keys:
            for module in self.key_map.get(update['type'], []):
                logging.debug(f"Updating module {module} with update: {update}")
                module.update(update)
                module.display()
            logging.info(f"Update for {updatetype} received:") 
            logging.debug(f"Update received: {update}")
        elif updatetype in self.uptime_keys:
            self.modules['Uptime'].update_server(update)
            self.modules['Uptime'].display()
        elif updatetype == "webcontrol":
            logging.info(f"Web control command ({update.get('command')}) received.")
            self.handle_webcontrol(update.get('command'))
        else:
            logging.warning(f"Unknown update type: {updatetype}")

    def handle_webcontrol(self, command):
        """
        Handle web control commands.
        """
        if command == "pp":
            logging.info("Play/Pause command received.")
            self.running = not self.running
            self.displays[self.display][0].data_dirty = True
            self.displays[self.display][0].is_paused = not self.running
            offscreen_canvas = self.displays[self.display][0].display()
            if self.matrix is not None:
                offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
        elif command == "fwd":
            logging.info("Forward display command received.")
            self.running = False
            self.displays[self.display][0].data_dirty = True
            self.displays[self.display][0].is_paused = False
            self.display = (self.display + 1) % self.displayCount
            self.displays[self.display][0].data_dirty = True
            self.displays[self.display][0].is_paused = True
            offscreen_canvas = self.displays[self.display][0].display()
            if self.matrix is not None:
                offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
        elif command == "rew":
            logging.info("Rewind display command received.")
            self.running = False
            self.displays[self.display][0].data_dirty = True
            self.displays[self.display][0].is_paused = False
            self.display = (self.display - 1) % self.displayCount
            self.displays[self.display][0].data_dirty = True
            self.displays[self.display][0].is_paused = True
            offscreen_canvas = self.displays[self.display][0].display()
            if self.matrix is not None:
                offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
        elif command == "out":
            logging.info("'Garbage has been taken out' command received.")
            self.modules['Weekly Calendar'].garbage_out(True)
            self.modules['Weekly Calendar'].data_dirty = True
        else:
            logging.warning(f"Unknown web control command: {command}")

    async def cycle_displays(self):
        logging.info(f"Number of displays: {self.displayCount}, Current display: {self.display}")
        """
        Cycle through the displays based on the configuration.
        """
        while True:
            try:
                if self.running: self.display = (self.display + 1) % self.displayCount
                current_display, display_time, frames = self.displays[self.display]
                logging.info(f"Displaying {current_display.type} for {display_time} seconds with {frames} frames.")
                for f in range(frames):
                    logging.debug(f"Displaying frame {f+1} of {frames} for {current_display.type}")
                    canvas = current_display.display()
                    if self.matrix is not None:
                        canvas = self.matrix.SwapOnVSync(canvas)
                    else:
                        logging.debug("No matrix initialized, skipping canvas swap.")
                    await asyncio.sleep(display_time/frames)
            except Exception as e:
                logging.error(f"Error in cycle_displays: {e}")
                await asyncio.sleep(5)          
                
    async def main(self):        
        import command_line_parser as clp
        
        logging.info("Starting microclient display...")
        clp_args = clp.parse_command_line_args()
        if clp_args.init_rgb > 0:
            from initialize_matrix import init_matrix
            logging.info("Initializing RGB Matrix Display...")
            self.matrix = init_matrix(clp_args)
            offscreen_canvas = self.matrix.CreateFrameCanvas()
        else:
            logging.info("No RGB Matrix Display initialized.")
            self.matrix = None

        self.modules = self.buildModules()                                # instantiates display page modules
        self.key_map = self.buildKeyMap()                                 # map message type to modules
        self.display_config = self.load_display_config()                  # hack to load display config (should be from file)
        self.displays, self.displayCount, self.display = self.buildDisplays() # builds array of display objects, how long to display them, and how many frames they can display
        self.fetch_initial_state()                                        # fetch initial state from API

        await asyncio.gather(
            self.listen_forever(),                                        # listen for updates from the API
            self.cycle_displays()                                         # cycle through the displays based on the configuration
        )

cd = ClientDisplay()
asyncio.run(cd.main())