import requests
import json
from PIL import Image, ImageFont, ImageDraw
import textwrap
from pages import DisplayPage
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/rpi-rgb-led-matrix/bindings/python'))
# from rgbmatrix import RGBMatrix

class NFLDisplay(DisplayPage):
    def __init__(self,matrix=None, twelve=True):
        super().__init__(matrix)
        if matrix is not None:
            from rgbmatrix import RGBMatrix
            self.matrix = True
        else:
            self.matrix = False
        self.event = 'nfl_event'
        self.no_event = 'no_nfl_event'
        self.currentGame = 0
        self.gameCount = 0
        self.last = 0
        self.textColor = (255,255,255)
        self.font      = ImageFont.load(r'fonts/5x7.pil')
        self.bgfont    = ImageFont.load(r'fonts/6x10.pil')
        self.favorite = ''
        self.favoriteGame = ""
        self.active = 0
        self.activecount = 0
        
              
    def update(self,data):
        self.games = data
        if data is not None:
            self.activegames = []
            self.favoriteGame = ""
            for game in self.games:
                if self.games[game]['state'] == 'in':
                    self.activegames.append(game)
                    if self.games[game]['awayabrv'] == self.favorite or self.games[game]['homeabrv'] == self.favorite:
                        self.favoriteGame = game
                        self.currentGame = int(game)
            self.gameCount = len(self.games) + 1
            self.activecount = len(self.activegames)

        
    def display(self):
        self.icon = Image.new("RGB", (128,64))
        draw = ImageDraw.Draw(self.icon)
        if self.games is not None:
            if self.gameCount > 1:
                if self.favorite == '': # no favorite
                    if self.activecount > 0:
                        #display cycle active
                        self.active = (self.active + 1) % self.activecount
                        game = self.games[self.activegames[self.active]]
                    else:
                        #display cycle all
                        self.currentGame = max(1,(self.currentGame + 1) % self.gameCount) # cycle all
                        game = self.games[str(self.currentGame)]
                else: # we have a favorite team
                    if self.favoriteGame == "": # no favorite game scheduled this week
                        if self.activecount > 0:
                            #display cycle active
                            self.active = (self.active + 1) % self.activecount
                            game = self.games[self.activegames[self.active]]
                        else:
                            #display cycle all
                            self.currentGame = max(1,(self.currentGame + 1) % self.gameCount) # cycle all
                            game = self.games[str(self.currentGame)]
                    else: # favorite team playing this week
                        #display favorite game
                        game = self.games[str(self.favoriteGame)]
                self.DrawGame(draw,game)
            else: # no games this week
                self.DrawNoGames(draw)  
        else: # no weather data received
            draw.text(( 1,  2), "No nfl data received.", font = self.font, fill='white')
        if self.is_paused:
            draw.line(((125,0),(125,2)), fill='White', width=1)
            draw.line(((127,0),(127,2)), fill='White', width=1)
        self.icon.save("static/thumb.bmp", "BMP")
        self.dirty = True
        if self.matrix:
            self.my_canvas.Clear()
            self.my_canvas.SetImage(self.icon,0,0)
            return self.my_canvas
    
    def DrawGame(self, draw, game):
        lines = []
        if game['state'] == 'pre':
            lines.append("Sched - {}".format(game['date']))
            lines.append("{:<3}  {:>6}".format(game['awayabrv'], game['awayrecord']))
            lines.append("{:<3}  {:>6}".format(game['homeabrv'], game['homerecord']))
        elif game['state'] == 'in':
            self.DrawInProgressGame(game,draw)
        elif game['state'] == 'post':
            lines.append("{} - Final".format(game['date']))
            lines.append("{:<3}  {:>6}    {:>4}".format(game['awayabrv'], game['awayrecord'], game['awayscore']))
            lines.append("{:<3}  {:>6}    {:>4}".format(game['homeabrv'], game['homerecord'], game['homescore']))
        
        i = 0
        for line in lines:
            print(line)
            draw.text((2, 11 * i), line, font = self.bgfont, fill=self.textColor)
            i += 1
            
    def DrawNoGames(self, draw):
        draw.text((2, 1), "No NFL this week.", font = self.bgfont, fill=self.textColor)

    def DrawInProgressGame(self, game, draw, period=None):
        if period == None: period = game['period']
        homelogoloc = "img/nfl/{}.bmp".format(game['homeabrv'])
        awaylogoloc = "img/nfl/{}.bmp".format(game['awayabrv'])
        homelogo = Image.open(homelogoloc)
        awaylogo = Image.open(awaylogoloc)
        # Background fill with "team color"
        draw.rectangle([ (0,0),(31,15)],fill=game['awaycolor'], outline=game['awaycolor'], width=1)
        draw.rectangle([(0,16),(31,31)],fill=game['homecolor'], outline=game['homecolor'], width=1)
        # Display Team Logos
        self.icon.paste(awaylogo, box=(0,0))
        self.icon.paste(homelogo, box=(0,16))
        # Display Team Abbreviations and score (in white)
        draw.text((17, 1), game['awayabrv'],  font = self.font, fill=self.textColor)
        draw.text((19, 9), game['awayscore'], font = self.font, fill=self.textColor)
        draw.text((17,17), game['homeabrv'],  font = self.font, fill=self.textColor)
        draw.text((19,25), game['homescore'], font = self.font, fill=self.textColor)
        # draw quarter
        draw.text((50, 1), period, font = self.font, fill=self.textColor)
        # Draw time remaining in period
        draw.text((50, 8), game['clock'], font = self.font, fill=self.textColor)
        # Draw the down & yards to go
        draw.text((50,17), game['downandyardage'],   font = self.font, fill=self.textColor)
        # Draw ball position
        draw.text((50,24), game['position'],   font = self.font, fill=self.textColor)
        # Indicate who has possession
        if game['possession'] == game['awayabrv']:
            self.DrawPossession(draw, True, (255,255,255), (150,75,0)) # 'football' outline in white, fill in brown
        elif game['possession'] == game['homeabrv']:
            self.DrawPossession(draw, False, (255,255,255), (150,75,0)) # 'football' outline in white, fill in brown
        # Draw the last play
        i = 0
        for line in textwrap.wrap(game['lastplay'],width=25, expand_tabs=False, max_lines=4):
            draw.text((1,33 + i * 8), line, font = self.font, fill=self.textColor)
            i += 1
            
    def DrawPossession(self, draw, away, outline_color, fill_color):
        x = 35
        if away:
            y=8
            draw.polygon([(x+0,y),  (x+1,y-2),(x+2,y-3),(x+6,y-3),(x+7,y-2),(x+8,y),(x+7,y+2),(x+6,y+3),(x+2,y+3),(x+1,y+2)],fill=fill_color,outline=outline_color,width=1)
            draw.line(   [(x+2,y),  (x+6,y)],fill=outline_color,width=1)
            draw.line(   [(x+3,y-1),(x+3,y+1)],fill=outline_color,width=1)
            draw.line(   [(x+5,y-1),(x+5,y+1)],fill=outline_color,width=1)
        else:
            y=24
            draw.polygon([(x+0,y),  (x+1,y-2),(x+2,y-3),(x+6,y-3),(x+7,y-2),(x+8,y),(x+7,y+2),(x+6,y+3),(x+2,y+3),(x+1,y+2)],fill=fill_color,outline=outline_color,width=1)
            draw.line(   [(x+2,y),  (x+6,y)],fill=outline_color,width=1)
            draw.line(   [(x+3,y-1),(x+3,y+1)],fill=outline_color,width=1)
            draw.line(   [(x+5,y-1),(x+5,y+1)],fill=outline_color,width=1)
                   
    def stringToTime(self,timeStr,ampm):
        try:
            if len(timeStr) == 4: # single digit hour
                start_hour = int(timeStr[0])
                start_minute = int(timeStr[2:])
            else:  # two digit hour
                start_hour = int(timeStr[:2])
                start_minute = int(timeStr[3:])
            if ampm == 'PM' and start_hour < 12:
                start_hour += 12  # convert to 24-hour time
        except:
            print("exception: timeStr - {}, ampm - {}".format(timeStr, ampm))
            start_hour = 23
            start_minute = 59
        return (start_hour, start_minute)
