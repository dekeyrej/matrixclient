import requests
import json
import arrow
from PIL import Image, ImageFont, ImageDraw
import textwrap
from rgbleddisplay import RGBLEDDisplay
import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/rpi-rgb-led-matrix/bindings/python'))
# from rgbmatrix import RGBMatrix

class NFLDisplay(RGBLEDDisplay):
    def __init__(self, matrix=None, team='', strict=False):
        super().__init__(matrix=matrix)
        if matrix is not None:
            from rgbmatrix import RGBMatrix
            self.matrix = True
        else:
            self.matrix = False
        # self.dba = dba
        self.type = 'NFL'
        self.currentGame = 0
        self.gameCount = 0
        self.textColor = (255,255,255)
        self.font      = ImageFont.load(r'fonts/5x7.pil')
        self.bgfont    = ImageFont.load(r'fonts/6x10.pil')
        self.favorite = team
        self.strict = strict
        if team == '':
            self.strict = False
        self.games = []
        self.all_games = []
        self.active_games = []
        self.favorite_games = []
        self.output = False
                
    def update(self, update_data): # overridden for dual data types
        if update_data['type'] == self.type:
            self.values = update_data
        if self.values['values']:
            self.games = self.values['values']['events']
            self.all_games = list(range(len(self.games)))
            self.active_games = []
            self.favorite_games = []
            self.mode = 'cycle_all'
            # self.active = 0
            self.favoriteGame = ""
            for id, game in enumerate(self.games):
                if self.output: print(f'game loop {id}')
                teams = (game['awayabrv'], game['homeabrv'])
                status = game['state']
                if status == 'in':
                    if self.output: print(f'   in active {id}')
                    self.active_games.append(id)
                    self.mode = 'cycle_active'
                    # if self.mode != 'cycle_favorite': self.mode = 'cycle_active'
                    if self.favorite in teams:
                        if self.output: print(f'      in fav {id} (should break)')
                        self.favorite_games.clear()
                        self.favorite_games.append(id)
                        self.mode = 'cycle_favorite'
                        break
                elif status == 'pre':
                    if self.output: print(f'   in pre   {id}')
                    if self.favorite in teams:
                        if self.output: print(f'      in fav {id}')
                        self.favorite_games.append(id)
                        self.mode = 'cycle_favorite'
                elif status == 'post':
                    if self.output: print(f'   in post  {id}')
                    if self.favorite in teams:
                        if self.output: print(f'      in fav {id}')
                        self.favorite_games.append(id)
                        self.mode = 'cycle_favorite'
            self.gameCount = len(self.games)

    def next_game(self, id: int , gamelist: list[int]) -> int:
        if id in gamelist: 
            current = gamelist.index(id)
            return gamelist[(current + 1) % len(gamelist)]
        else:
            return gamelist[0]    
    
    def display(self):
        self.icon = Image.new("RGB", (128,64))
        draw = ImageDraw.Draw(self.icon)
        ###################################################
        if self.mode == 'cycle_all':
            self.currentGame = self.next_game(self.currentGame, self.all_games)
            # print(f'cycle through all {len(self.games)} games.')
        elif self.mode == 'cycle_favorite':
            self.currentGame = self.next_game(self.currentGame, self.favorite_games)
            # print(f'cycle through all {len(self.favorite_games)} favorite games.')
        elif self.mode == 'cycle_active':
            self.currentGame = self.next_game(self.currentGame, self.active_games)
            # print(f'cycle through all {len(self.active_games)} active games.')
        
        if self.gameCount == 0:
            self.DrawNoGames(draw)
        else:
            self.DrawGame(draw, self.games[self.currentGame])
        ###################################################
        # else: # no game data received
        #     draw.text(( 1,  2), "No nfl data received.", font = self.font, fill='white')
        if self.is_paused:
            draw.line(((125,0),(125,2)), fill='White', width=1)
            draw.line(((127,0),(127,2)), fill='White', width=1)
        self.icon.save("static/nfl.bmp", "BMP")
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
            # print(line)
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
        draw.text((50,17), game.get('downandyardage',''),   font = self.font, fill=self.textColor)
        # Draw ball position
        draw.text((50,24), game.get('position',''),   font = self.font, fill=self.textColor)
        # Indicate who has possession
        poss = game.get('possession','')
        if poss != '':
            if poss == game['awayabrv']:
                self.DrawPossession(draw, True, (255,255,255), (150,75,0)) # 'football' outline in white, fill in brown
            elif poss == game['homeabrv']:
                self.DrawPossession(draw, False, (255,255,255), (150,75,0)) # 'football' outline in white, fill in brown
        # Draw the last play
        i = 0
        lastplay = game.get('lastplay', '')
        for line in textwrap.wrap(lastplay,width=25, expand_tabs=False, max_lines=4):
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
