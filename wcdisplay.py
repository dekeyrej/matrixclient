import json
import arrow
from PIL import Image, ImageFont, ImageDraw
import textwrap
from pages import DisplayPage
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '../rpi-rgb-led-matrix/bindings/python'))

class WorldCupDisplay(DisplayPage):
    
    def __init__(self,matrix=None):
        super().__init__(matrix)
        if matrix is not None:
            from rgbmatrix import RGBMatrix
            self.matrix = True
        else:
            self.matrix = False
        self.currentGame = -1
        self.gameCount = 0
        self.last = 0
        self.textColor = (255,255,255)
        self.smfont    = ImageFont.load(r'fonts/4x6.pil')
        self.font      = ImageFont.load(r'fonts/5x7.pil')
        self.bgfont    = ImageFont.load(r'fonts/6x10.pil')
        self.hgfont    = ImageFont.load(r'fonts/7x13B.pil')
        self.active = -1
        self.activecount = 0
        self.event = 'game_event'
        self.no_event = 'no_game_event'
                     
    def update(self,data):
        now = arrow.now().format('MMM/DD HH:mm')
        self.games = data
        self.activegames = []
        for game in self.games:
            if game['status'] == 'in_progress':
                self.activegames.append(game)
        self.gameCount = len(self.games)
        self.activecount = len(self.activegames)
        
    def display(self):
        self.icon = Image.new("RGB", (128,64))
        draw = ImageDraw.Draw(self.icon)        
        if self.gameCount > 0:
            if self.activecount > 0:
                #display cycle active
                self.active = (self.active + 1) % self.activecount
                game = self.activegames[self.active]
            else:
                #display cycle all
                self.currentGame = max(0,(self.currentGame + 1) % self.gameCount) # cycle all
                game = self.games[self.currentGame]
            self.DrawGame(draw,game)
        else: # no matches today
            self.DrawNoGames(draw)  
        if self.is_paused:
            draw.line(((125,0),(125,2)), fill='White', width=1)
            draw.line(((127,0),(127,2)), fill='White', width=1)
        self.icon.save("static/thumb.bmp", "BMP")
        if self.matrix:
            self.my_canvas.Clear()
            self.my_canvas.SetImage(self.icon,0,0)
            return self.my_canvas
    
#         game = {'update',    -- string with last update time
#                 'home_name', -- string proper country name
#                 'home_flag', -- string with country abbreviation (keys for flags)
#                 'away_name', -- string proper country name
#                 'away_flag', -- string with country abbreviation (keys for flags)
#                 'status',    -- string 'future_scheduled', 'in_progress', 'completed'
#                 'score',     -- string scores 'h-a'
#                 'penalties', -- string penalties '(h-a)'
#                 'time',      -- string formated with 'Scheduled...', game time, 'full-time'
#                }

    def DrawGame(self, draw, game):
        t = arrow.now()
        now = t.format('MMM/DD HH:mm')
        xoff,yoff = self.justify(now, self.font, 128, 0, 'TR')
        # Display current date/time
        draw.text((xoff, 1), now,  font = self.font, fill=self.textColor)
        # Display background boxes
        draw.rectangle([(0, 9),(49, 42)], outline=(63,63,63),width=1)
        draw.rectangle([(78,9),(127,42)], outline=(63,63,63),width=1)
        # Display Team Logos
        homelogo = Image.open("img/wc/{}.bmp".format(game['home_flag']))
        awaylogo = Image.open("img/wc/{}.bmp".format(game['away_flag']))
        self.icon.paste(homelogo, box=(1, 10))
        self.icon.paste(awaylogo, box=(79,10))
        # Display Team (country) Names
        home = game['home_name']
        homeoff = max(0, 24 - (len(home) * 4) / 2) # centers team name under left flag, unless it would cut it off in which case it left justifies it
        away = game['away_name']
        awayoff = min(104 - (len(away) * 4) /2, 128 - (len(away) * 4)) # centers team name under right flag, unless it would cut it off in which case it right justifies it
        draw.text((homeoff, 44), home,  font = self.smfont, fill=self.textColor)
        draw.text((awayoff, 44), away,  font = self.smfont, fill=self.textColor)
        # set 'game time', 'score' and 'penalties'
        time = game['time']
        score = game['score']
        penalties = game['penalties']
        print(penalties)
        # Display 'score'
        draw.text((54, 20), score, font = self.hgfont, fill=self.textColor)
        if penalties != '':
            draw.text((52, 33), penalties, font = self.font, fill=self.textColor)
        # Display 'game time'
        timeoff = 64 - ((len(time) - 1) * 6) /2
        draw.text((timeoff, 52), time, font = self.bgfont, fill=self.textColor)
        
    def DrawNoGames(self, draw):
        draw.text((2, 1), "No World Cup matches today.", font = self.bgfont, fill=self.textColor)