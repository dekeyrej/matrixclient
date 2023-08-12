# import requests
# import json
import arrow
# import time
# from secrets import secrets
from PIL import Image, ImageFont, ImageDraw
from pages import DisplayPage
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/rpi-rgb-led-matrix/bindings/python'))
# from rgbmatrix import RGBMatrix
from team_colors import TeamColors
import textwrap

class MLBDisplay(DisplayPage):
    
#     dows = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
#     mons = ("NAM", "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
#     dspm = {"1" : 31, "2" : 28, # don't care - no baseball in January
#             "3" : 31, "4" : 30, "5" : 31, "6" : 30,
#             "7" : 31, "8" : 31, "9" : 30,
#             "10": 31, "11": 30, "12": 31}
    
    sj = None                  # json results from query (contains data for all of the day's games)
    
    home_team_abbrev = ""      # 2/3 letter abbreviation of the home team
    away_team_abbrev = ""      # 2/3 letter abbreviation of the away team
    home_win = ""              # for scheduled games, # of wins for the home team this season
    home_loss = ""             # for scheduled games, # of losses for the home team this season
    away_win = ""              # for scheduled games, # of wins for the away team this season
    away_loss = ""             # for scheduled games, # of losses for the away team this season
    start_time = ""            # 12-hour formatted string (h:mm, or hh:mm) for the start time of a game
    ampm = ""                  # AM/PM of start time
    time_zone = ""             # time zone of the start time (seems to be localized)
    
    favoriteInProgress = False # if favorite team's game is I or IR
    ind = ""                   # code that indicates the status of the game (S, P, PW), (I, IR), (O, F, FR, DI, DR))
    inning = 0                 # current inning
    inning_state = ""          # Top, Middle, Bottom, End
    home_runs = ""             # current score (number of runs) of the home team.
    away_runs = ""             # current score (number of runs) of the away team. #, home_hits, away_hits, home_err, away_err, last_play, runners, runners_text, sprite,
    outs = 0                   # number of outs recorded recorded in the current half-inning
    b1 = b2 = b3 = 0           # base (1st, 2nd, 3rd) is unoccupied (=0) or occupied (=1)
    balls = ""                 # number of balls against the current batter
    strikes = ""               # number of strikes against the current batter
    
    textColor = 0xFFFFFF       # text color used for non-In Progress games
    short_date = ""            # MM/DD/YY formatted date for "no game scheduled"
    lines = ["","","","","",""]# 6 text lines for 2-up display of scheduled or completed games
    pitcher_text = ""          # current pitcher
    batter_text = ""           # current batter
    last_play = ""
    teamLogos = {}             # dictionary of images (16x14 pixels) of the teams' logos
    icon = None


    def __init__(self, dba, matrix=None, team="BOS", enabled = False):
        super().__init__(dba, matrix)
        if matrix is not None:
            from rgbmatrix import RGBMatrix
            self.matrix = True
        else:
            self.matrix = False
        self.type = 'MLB'
        self.TEAM = team       # "favorite" team, BOS by default
        self.TEAM_GAME = 99    # indicates favorite team has no game "today"
        self.font    = ImageFont.load(r'fonts/5x7.pil')
        self.bgfont    = ImageFont.load(r'fonts/6x10.pil')
        self.gameCount = 0     # number of games to take place today
        self.scheduledGames = [] # list of games scheduled
        self.scheduledCount = 0  # number of games where ind == S, P, or PW
        self.inProgressGames = [] # list of games in progress
        self.inProgressCount = 0 # number of games where ind == I or IR
        self.finishedGames  = [] # list of finished games
        self.finishedCount  = 0  # number of games where ind == O, F, FR
        self.cycle_enabled  = enabled
        self.gameMode       = 'S' # cycling scheduled games, 'I' for in progress, 'F' for finished
        self.cycle = False     # cycle = false => just show favorite team's game; 
        self.currentGame = 0   # current game if cycling through all games
        self.loadLogos()
        ## during the playoffs, it looks like updates are coming later in the day (I'm going to try 1200)
        self.nextdaytime = 12
        
    def update(self):
#         tstart = time.monotonic()
        self.values = self.dba.read(self.type)
        if self.values is not None:
            self.nextUpdate = arrow.get(self.fix_edt(self.values['valid']),'MM/DD/YYYY h:mm:ss A ZZZ').shift(seconds=+1)
        t = arrow.now()
        if t.hour >= 11:
            self.short_date = t.format('MM/DD/YY')
        else:
            self.short_date = t.shift(days=-1).format('MM/DD/YY')
        self.sj = self.values['values']
        favgames = list()
        self.gameCount = len(self.sj)  # normally < 20.  If it's big, it may be because it's the All-Star game, or only 1 game?
#         print(self.gameCount)
        if self.gameCount < 32:
#                 print(self.gameCount)
            self.scheduledCount = 0
            self.inProgressCount = 0
            self.finishedCount = 0
            self.scheduledGames.clear()
            self.inProgressGames.clear()
            self.finishedGames.clear()
            # self.cycle = True
#             firstStartTime = t.replace(hour=23,minute=59,second=59)
            
            for i in range(self.gameCount):
#                 print(i)
                if self.sj[i]["status"] == 'pre':
#                     print("scheduled")
                    self.scheduledCount += 1
                    self.scheduledGames.append(i)
                elif self.sj[i]["status"] == 'in':
#                     print("in-progress")
                    self.inProgressCount += 1
                    self.inProgressGames.append(i)
                    # if a favorite game is in progress, turn off the cycle
                    if self.sj[i]['awayAbbreviation'] == self.TEAM or self.sj[i]['homeAbbreviation'] == self.TEAM:
                        self.cycle = False
                else:
#                     print("finished or something else...")
                    self.finishedCount += 1
                    self.finishedGames.append(i)
                # make a list of favorite games
#                     print("end of if")
                if self.sj[i]['awayAbbreviation'] == self.TEAM or self.sj[i]['homeAbbreviation'] == self.TEAM or self.sj[i]['homeAbbreviation'] == 'AL':
                    favgames.append(i)
                    if not self.cycle_enabled:
                        self.cycle = False
                
#                      print(self.scheduledCount)
#                      print(self.inProgressCount)
#                      print(self.finishedCount)
#                      print(firstStartTime)
                    
                # loops through the days games (assumed to be pre-sorted in time order) to find the next starting game
#                 start_time = arrow.get(self.sj[i]['startTime'],'MM/DD/YYYY h:mm A ZZZ')
#                 if start_time < firstStartTime and start_time >= t:
#                     firstStartTime = start_time
                    
#             print(self.scheduledCount)
#             print(self.inProgressCount)
#             print(self.finishedCount)
#             print(firstStartTime)
# 
#             print(favgames)
#             print(len(favgames))
#             print('Next game starts at {}'.format(firstStartTime.format('MM/DD/YYYY h:mm A ZZZ')))
            if len(favgames) == 0:
                self.TEAM_GAME = 99
                # self.cycle = True
    #             self.currentGame = 0
            elif len(favgames) == 1: # favorite has 1 or 2 games today
                gind = self.sj[favgames[0]]["status"]
                self.TEAM_GAME = favgames[0]
                self.currentGame = favgames[0]
                    # 1 game
#                     if (gind == 'I' or gind == 'IR'): # 1 game, and it's in progress
#                         self.TEAM_GAME = favgames[0]
#                         self.currentGame = favgames[0]
            else: # 2 games (double-header)
                gind  = self.sj[favgames[0]]["status"]
                gind1 = self.sj[favgames[1]]["status"]
                if (gind == 'in'): # 1 game, and it's in progress
                    self.TEAM_GAME = favgames[0]
                    self.currentGame = favgames[0]
                elif (gind1 == 'in'):  # 2nd game, and it's in progress
                    self.TEAM_GAME = favgames[1]
                    self.currentGame = favgames[1]
                else:
                    self.TEAM_GAME = favgames[0]
                    self.currentGame = favgames[0]
#                 print("made it to the end?")
#                 print(self.TEAM_GAME)
#                 print(self.currentGame)
        else:
            self.gameCount = 1
            self.cycle = False
            self.currentGame = 0
            self.TEAM_GAME = 0
            # (hour, minute) = self.stringToTime(self.sj["time"],self.sj["ampm"])
            # firstStartTime = arrow.get(current_year, url_mon, url_day, hour, minute, 0)
            
            if self.sj["status"] == 'pre':
                self.scheduledCount += 1
            elif self.sj["status"] == 'in':
                self.inProgressCount += 1
            else:
                self.finishedCount += 1
                
#         tend = time.monotonic()
#         print(tend - tstart)

#     except:
#         print("exception")
# #             print(json.dumps(self.sj[4], indent=4, sort_keys=True))
#         self.gameCount = 0
#         self.cycle = False
#         self.currentGame = -1
#     # end try/except
    # calculate next sleep time
#     if self.gameCount == 0 or (self.inProgressCount == 0 and self.finishedCount == self.gameCount):
#         # sleep until 9am today/tomorrow
#         next_sleep = seconds29am   
#     elif self.inProgressCount > 0:
#         # sleep for a minute
#         next_sleep = 28 # 58 is more polite...
#     else:
#         # sleep until the start of the first game
#         next_sleep = firstStartTime.format('X') - t.format('X')
# #         print(next_sleep)
#     self.update_rate = next_sleep # seconds between updates

    def loadGame(self, gid):
#         print(gid)
        if gid != -1 and gid != 99:
            self.b1 = self.b2 = self.b3 = 0 # bases are empty
    #         print(self.TEAM_GAME)
    #         if self.TEAM_GAME != 99:
            if self.gameCount > 1:
                game = self.sj[gid]
            else: 
                game = self.sj  # self.gameCount = 1
#                 print(game)
            # for all ind in (S, P, PW, DR, DI, I, O, F, FR)
            self.home_team_abbrev = game['homeAbbreviation']
            self.homeRecord       = game['homeRecord']
            self.homeColor        = self.hexToTuple(game['homeColor'])
            self.away_team_abbrev = game['awayAbbreviation']
            self.awayRecord       = game['awayRecord']
            self.awayColor        = self.hexToTuple(game['awayColor'])
            self.start_time       = arrow.get(self.fix_edt(game["startTime"]),'MM/DD/YYYY h:mm A ZZZ').format('h:mm A')
            self.ind              = game["status"]
            if self.ind == 'in':       
                self.inning_state     = game["inningState"]
                self.inning           = game["inning"]
                self.home_runs        = game["homeScore"]
                self.away_runs        = game["awayScore"]
                if self.inning_state == 'Top' or self.inning_state == 'Bot':
                    self.balls            = game["balls"]
                    self.strikes          = game["strikes"]
                    self.outs             = int(game["outs"])
                    # self.pitcher_text = "P:" + game["pitcher"]["last"].upper()
                    # self.batter_text  = "B:" + game["batter"]["last"].upper()
                    self.last_play        = game["lastPlay"]
                    if game['onFirst']:  self.b1 = 1
                    if game['onSecond']: self.b2 = 1 
                    if game['onThird']:  self.b3 = 1 
                
            elif self.ind == 'post':
                # self.inning           = game["inning"]
                self.home_runs        = game["homeScore"]
                self.away_runs        = game["awayScore"]
            else:
                pass
            
    def hexToTuple(self,h):
        return (int(h[0:2], 16),int(h[2:4], 16),int(h[4:6], 16))

    def display_stuff(self,top):
        if top:
            l = 0   # populate line 0, 1, 2
        else:
            l = 3   # populate line 3, 4, 5

        if self.gameCount == 0:
            self.textColor = (32,32,32)
            self.lines[l]   = self.short_date
            self.lines[l+1] = 'No MLB'
            self.lines[l+2] = 'today.'
        else:
            # if self.ind == 'DR' or self.ind == 'DI':  # Delayed for Rain (Postponed)
            #     self.textColor = (122,122,122) # 0x7A7A7A
            #     self.lines[l]   = 'Postponed'
            #     self.lines[l+1] = "{:<3} {}".format(self.away_team_abbrev, self.awayRecord)
            #     self.lines[l+2] = "{:<3} {}".format(self.home_team_abbrev, self.homeRecord)
            # elif self.ind == 'PR' or self.ind == 'PI':  # (Rain) Delayed Start
            #     self.textColor = (0,0,255) # 0xEEE843
            #     self.lines[l]   = "{}".format(self.start_time)
            #     self.lines[l+1] = "{:<3} {}".format(self.away_team_abbrev, self.awayRecord)
            #     self.lines[l+2] = "{:<3} {}".format(self.home_team_abbrev, self.homeRecord)
            if self.ind == 'pre':  # Scheduled, Pre-game, Pre-game Warmup
                self.textColor = (238,232,67) # 0xEEE843
                self.lines[l]   = "{}".format(self.start_time)
                self.lines[l+1] = "{:<3} {}".format(self.away_team_abbrev, self.awayRecord)
                self.lines[l+2] = "{:<3} {}".format(self.home_team_abbrev, self.homeRecord)
            elif self.ind == 'in':  # In Progress
                self.textColor = (255,255,255) # 0xFFFFFF
                # if self.inning_state == "End":
                #     self.inning_state = "Top"
                self.lines[l]  = "{} {:<2}  {}".format(self.inning_state[0:3], self.inning, self.b2)
                self.lines[l+1] = "{:<3} {:>2} {} {}".format(self.away_team_abbrev, self.away_runs, self.b3, self.b1)
                self.lines[l+2] = "{:<3} {:>2}  {}".format(self.home_team_abbrev, self.home_runs, self.outs)
            # elif self.ind == 'IR':  # In Progress - Rain Delay
            #     self.textColor = (0,0,255) # 0x0000FF
            #     if self.inning_state == "End":
            #         self.inning_state = "Top"
            #     self.lines[l]  = "Delay {} {:<2}".format(self.inning_state[0:3], self.inning)
            #     self.lines[l+1] = "{:<3} {:>2}".format(self.away_team_abbrev, self.away_runs)
            #     self.lines[l+2] = "{:<3} {:>2}".format(self.home_team_abbrev, self.home_runs)
            elif self.ind == 'post':  # Final, Final - Rain Shortened, Over
                self.textColor = (146,146,206) # 0x9292CE # blue bells
                ind_text = self.ind
                # if self.inning == 9:
                #     ind_text = self.ind
                # else:
                #     ind_text = self.ind + ("" if self.inning == '9' else self.inning)
                self.lines[l]  = self.short_date
                self.lines[l+1] = "{:<3} {:>2} {}".format(self.away_team_abbrev, self.away_runs, ind_text)
                self.lines[l+2] = "{:<3} {:>2}".format(self.home_team_abbrev, self.home_runs)
            elif self.TEAM_GAME == 99:  # No game found for 'TEAM' today
                self.textColor = (32,32,32) # 0x101010
                self.lines[l] = self.short_date
                self.lines[l+1] = 'No {}'.format(self.TEAM)
                self.lines[l+2] = 'game today.'
            else:
                self.textColor = (255,255,255) # 0xFFFFFF
                self.lines[l] = '?'
                self.lines[l+1] = self.ind
                self.lines[l+2] = '?'
                print(self.ind)
            
#         for l in range(6):
#             print(self.lines[l])
        
        
    def display(self):
        self.icon = Image.new("RGB", (128,64))
        draw = ImageDraw.Draw(self.icon)
        if self.cycle and self.currentGame != -1:
            self.currentGame = (self.currentGame + 1) % self.gameCount
        else:
            self.currentGame = self.TEAM_GAME
#         print(self.currentGame)
        if self.gameCount != 0:
            self.loadGame(self.currentGame)
        self.display_stuff(top=True)
        # self.my_canvas.Clear()
        if self.ind == 'in':
            self.DrawInProgressGame(draw)
        else:
            for i in range(3):
                draw.text((2, 11 * i), self.lines[i], font = self.bgfont, fill=self.textColor)
#                 graphics.DrawText(self.my_canvas, self.bgfont, 2, 11 * i + 8,  self.textColor, self.lines[i])
        if self.is_paused:
            draw.line(((125,0),(125,2)), fill='White', width=1)
            draw.line(((127,0),(127,2)), fill='White', width=1)
        self.icon.save("static/thumb.bmp", "BMP")
        self.dirty = True
        if self.matrix:
            self.my_canvas.Clear()
            self.my_canvas.SetImage(self.icon,0,0)
            return self.my_canvas

    def DrawInProgressGame(self, draw):
        # Background fill with "team color"
        self.FillAwayColor(draw)
        self.FillHomeColor(draw)
        # Background fill with a little color (maybe)                
        # self.FillScoreBoard(self.my_canvas,graphics.Color(10,15,14)) # Green Monster (84,121,109) Dark Green Monster (21,30,27)
        # Display Team Logos
        self.icon.paste(self.teamLogos[self.away_team_abbrev], box=(0,0))
        self.icon.paste(self.teamLogos[self.home_team_abbrev], box=(0,16))
#         self.my_canvas.SetImage(self.teamLogos[self.away_team_abbrev], 0,  0)
#         self.my_canvas.SetImage(self.teamLogos[self.home_team_abbrev], 0, 16)
        # Display Team Abbreviations in Team Primary Color, and Run counts (in white)
        draw.text((17, 1), self.away_team_abbrev, font = self.font, fill=TeamColors[self.away_team_abbrev][1])
        draw.text((19, 8), self.away_runs,        font = self.font, fill=self.textColor)
        draw.text((17,17), self.home_team_abbrev, font = self.font, fill=TeamColors[self.home_team_abbrev][1])
        draw.text((19,24), self.home_runs,        font = self.font, fill=self.textColor)
#         length = graphics.DrawText(self.my_canvas, self.font, 17,  7, TeamColors[self.away_team_abbrev][1], self.away_team_abbrev)
#         length = graphics.DrawText(self.my_canvas, self.font, 19, 14, self.textColor, self.away_runs)
#         length = graphics.DrawText(self.my_canvas, self.font, 17, 23, TeamColors[self.home_team_abbrev][1], self.home_team_abbrev)
#         length = graphics.DrawText(self.my_canvas, self.font, 19, 30, self.textColor, self.home_runs)
        # Draw the empty bases and fill the occupied ones
        self.DrawBases(draw, (255,255,255), (238,232,67))
        # Draw Inning and State (Top, Mid, Bot)
        draw.text((40,21), str(self.inning), font = self.font, fill=self.textColor)
#         graphics.DrawText(self.my_canvas, self.font,   40, 27, self.textColor, self.inning)
        self.DrawInningState(draw)
        # Draw the Balls - Strikes
        draw.text((50,17), str(self.balls),   font = self.font, fill=self.textColor)
        draw.text((55,17), "-",          font = self.font, fill=self.textColor)
        draw.text((59,17), str(self.strikes), font = self.font, fill=self.textColor)
#         graphics.DrawText(self.my_canvas, self.font,   50, 23, self.textColor, self.balls)
#         graphics.DrawText(self.my_canvas, self.font,   55, 22, self.textColor, "-")
#         graphics.DrawText(self.my_canvas, self.font,   59, 23, self.textColor, self.strikes)
        # Draw the outs
        self.DrawOuts(draw, (255,255,255), (238,232,67))
        # Draw the Pitcher and Batter
        draw.text((65, 1), self.pitcher_text, font = self.font, fill=self.textColor)
        draw.text((65, 8), self.batter_text,  font = self.font, fill=self.textColor)
#         graphics.DrawText(self.my_canvas, self.font,   1, 40, self.textColor, self.pitcher_text)
#         graphics.DrawText(self.my_canvas, self.font,   1, 50, self.textColor, self.batter_text)
        i = 0
        for line in textwrap.wrap(self.last_play, width=25, expand_tabs=False, max_lines=4):
            draw.text((1,34 + i * 8), line, font = self.font, fill=self.textColor)
            i += 1

    def FillAwayColor(self, draw):
        # draw.rectangle([(0,0),(31,15)],fill=TeamColors[self.away_team_abbrev][0], outline=TeamColors[self.away_team_abbrev][0],width=1)
        draw.rectangle([(0,0),(31,15)],fill=self.awayColor, outline=self.awayColor,width=1)
#         for i in range (0,16):
#             graphics.DrawLine(canvas, 0, i, 31, i, TeamColors[self.away_team_abbrev][0])
        
    def FillHomeColor(self, draw):
        # draw.rectangle([(0,16),(31,31)],fill=TeamColors[self.home_team_abbrev][0], outline=TeamColors[self.home_team_abbrev][0],width=1)
        draw.rectangle([(0,16),(31,31)],fill=self.homeColor, outline=self.homeColor,width=1)
#         for i in range (16,32):
#             graphics.DrawLine(canvas, 0, i, 31, i, TeamColors[self.home_team_abbrev][0])
            
    def FillScoreBoard(self, draw, color):
        draw.rectangle([(32,0),(63,31)],fill=color, outline=color,width=1)
#         for i in range (0,32):
#             graphics.DrawLine(canvas, 32, i, 63, i, color)
    
    def DrawBases(self, draw, outline_color, fill_color):
        draw.line([(32, 0), (32,31)], fill=(127,127,127), width=1)
        # Fill bases if occupied fill = graphics.Color(238,232,67)
        #ImageDraw.polygon(xy, fill=None, outline=None, width=1)
        #   1B
        if self.b1 == 1:
            draw.polygon([(50,11),(54,7),(58,11),(54,15)],fill=fill_color,outline=outline_color,width=1)
        else:
            draw.polygon([(50,11),(54,7),(58,11),(54,15)],fill=None,outline=outline_color,width=1)
        #  2B
        if self.b2 == 1:
            draw.polygon([(44,5),(48,1),(52,5),(48,9)],fill=fill_color,outline=outline_color,width=1)
        else:
            draw.polygon([(44,5),(48,1),(52,5),(48,9)],fill=None,outline=outline_color,width=1)
        # 3B
        if self.b3 == 1:
            draw.polygon([(38,11),(42,7),(46,11),(42,15)],fill=fill_color,outline=outline_color,width=1)
        else:
            draw.polygon([(38,11),(42,7),(46,11),(42,15)],fill=None,outline=outline_color,width=1)
        

    def DrawOuts(self, draw, outline_color, fill_color):
        if self.outs == 1:
            draw.polygon([(51,26),(55,26),(55,30),(51,30)],fill=fill_color,outline=outline_color,width=1) # 1st out
            draw.polygon([(58,26),(62,26),(62,30),(58,30)],fill=None,outline=outline_color,width=1) # 2nd out
        elif self.outs == 2:
            draw.polygon([(51,26),(55,26),(55,30),(51,30)],fill=fill_color,outline=outline_color,width=1) # 1st out
            draw.polygon([(58,26),(62,26),(62,30),(58,30)],fill=fill_color,outline=outline_color,width=1) # 2nd out
        else:
            draw.polygon([(51,26),(55,26),(55,30),(51,30)],fill=None,outline=outline_color,width=1) # 1st out
            draw.polygon([(58,26),(62,26),(62,30),(58,30)],fill=None,outline=outline_color,width=1) # 2nd out
            
        
    def DrawInningState(self, draw):
        color = (146,146,206)
        if self.inning_state == "Top" or self.inning_state == "End":
            draw.polygon([(36,22),(38,24),(34,24)],fill=color,outline=color,width=1) # Up wedge
        elif self.inning_state == "Mid":                                             
            draw.line([(34, 24), (38, 24)], fill=color, width=1)                     # Horizontal line
        else: # self.inning_state == "Bot"
            draw.polygon([(36,26),(38,24),(34,24)],fill=color,outline=color,width=1) # Down wedge

    def loadLogos(self):
        teamNames = TeamColors.keys()
        for team in teamNames:
            self.teamLogos[team] = Image.open("img/mlb/" + team + "16.bmp")
            
    # def stringToTime(self,timeStr,ampm):
    #     try:
    #         if len(timeStr) == 4: # single digit hour
    #             start_hour = int(timeStr[0])
    #             start_minute = int(timeStr[2:])
    #         else:  # two digit hour
    #             start_hour = int(timeStr[:2])
    #             start_minute = int(timeStr[3:])
    #         if ampm == 'PM' and start_hour < 12:
    #             start_hour += 12  # convert to 24-hour time
    #     except:
    #         print("exception: timeStr - {}, ampm - {}".format(timeStr, ampm))
    #         start_hour = 23
    #         start_minute = 59
    #     return (start_hour, start_minute)
