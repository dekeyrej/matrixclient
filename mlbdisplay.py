import arrow
from PIL import Image, ImageFont, ImageDraw
from plain_pages.displaypage import DisplayPage
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


    def __init__(self, dba, matrix=None, team='', strict=False):
        super().__init__(dba, matrix)
        if matrix is not None:
            from rgbmatrix import RGBMatrix
            self.matrix = True
        else:
            self.matrix = False
        self.type = 'MLB'
        self.TEAM = team
        self.strict = strict
        if team == '':
            self.strict = False
        self.font    = ImageFont.load(r'fonts/5x7.pil')
        self.bgfont    = ImageFont.load(r'fonts/6x10.pil')
        self.gameCount = 0     # number of games to take place today
        self.currentGame = 0   # current game if cycling through all games
        self.loadLogos()
        self.output = False
        self.mode = 'cycle_all'

    def update(self):
        self.values = self.dba.read(self.type)
        if self.values:
            self.mode = 'cycle_all'
            self.games = self.values['values']
            self.gameCount = len(self.games)
            self.all_games = []
            self.favorite_games = []
            self.active_games = []
            if self.gameCount > 0:
                self.all_games = list(range(self.gameCount))
                for id, game in enumerate(self.games):
                    if self.output: print(f'game loop {id}')
                    teams = (game['homeAbbreviation'], game['awayAbbreviation'])
                    status = game['status']
                    if status == 'in':  ### now have to account for postponed :-/
                        if self.output: print(f'   in active {id}')
                        self.active_games.append(id)
                        if self.mode != 'cycle_favorite': self.mode = 'cycle_active'
                        if self.TEAM in teams:
                            if self.output: print(f'      in fav {id} (should break)')
                            self.favorite_games.clear()
                            self.favorite_games.append(id)
                            self.mode = 'cycle_favorite'
                            break
                    elif status == 'pre':
                        if self.output: print(f'   in pre   {id}')
                        if self.TEAM in teams:
                            if self.output: print(f'      in fav {id}')
                            self.favorite_games.append(id)
                            self.mode = 'cycle_favorite'
                    elif status == 'post':
                        if self.output: print(f'   in post  {id}')
                        if self.TEAM in teams:
                            if self.output: print(f'      in fav {id}')
                            self.favorite_games.append(id)
                            self.mode = 'cycle_favorite'

    def loadGame(self, gid):
        if gid != -1 and gid != 99:
            self.b1 = self.b2 = self.b3 = 0 # bases are empty
            game = self.games[gid]
            # for all ind in (S, P, PW, DR, DI, I, O, F, FR)
            self.home_team_abbrev = game['homeAbbreviation']
            self.homeRecord       = game['homeRecord']
            self.homeColor        = self.hexToTuple(game['homeColor'])
            self.away_team_abbrev = game['awayAbbreviation']
            self.awayRecord       = game['awayRecord']
            self.awayColor        = self.hexToTuple(game['awayColor'])
            start_time            = arrow.get(self.fix_edt(game["startTime"]),'MM/DD/YYYY h:mm A ZZZ')
            self.start_time       = start_time.format('ddd MM/DD h:mm A')
            self.short_date       = start_time.format('MM/DD/YY')
            # self.start_time       = arrow.get(self.fix_edt(game["startTime"]),'MM/DD/YYYY h:mm A ZZZ').format('h:mm A')
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
    
    def next_game(self, id: int , gamelist: list[int]) -> int:
        if id in gamelist: 
            current = gamelist.index(id)
            return gamelist[(current + 1) % len(gamelist)]
        else:
            return gamelist[0]

    def display_stuff(self):
        l = 0
        # if top:
        #     l = 0   # populate line 0, 1, 2
        # else:
        #     l = 3   # populate line 3, 4, 5

        if self.gameCount == 0:
            self.textColor = (32,32,32)
            self.lines[l]   = self.short_date
            self.lines[l+1] = 'No MLB'
            self.lines[l+2] = 'today.'
        else:
            if self.ind == 'pre':  # Scheduled, Pre-game, Pre-game Warmup
                self.textColor = (238,232,67) # 0xEEE843
                self.lines[l]   = "{}".format(self.start_time)
                self.lines[l+1] = "{:<3} {}".format(self.away_team_abbrev, self.awayRecord)
                self.lines[l+2] = "{:<3} {}".format(self.home_team_abbrev, self.homeRecord)
            elif self.ind == 'in':  # In Progress
                pass
                # self.textColor = (255,255,255) # 0xFFFFFF
                # # if self.inning_state == "End":
                # #     self.inning_state = "Top"
                # self.lines[l]  = "{} {:<2}  {}".format(self.inning_state[0:3], self.inning, self.b2)
                # self.lines[l+1] = "{:<3} {:>2} {} {}".format(self.away_team_abbrev, self.away_runs, self.b3, self.b1)
                # self.lines[l+2] = "{:<3} {:>2}  {}".format(self.home_team_abbrev, self.home_runs, self.outs)
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
        
    def display(self):
        if self.data_dirty:
            self.icon = Image.new("RGB", (128,64))
            draw = ImageDraw.Draw(self.icon)
            ######################################################
            if self.strict and self.TEAM != '':
                if len(self.favorite_games) == 0:
                    self.gameCount = 0
                    # print('no favorite game today')
            elif self.mode == 'cycle_all':
                if self.strict and self.TEAM != '':
                    self.gameCount = 0
                    # print('no favorite game today')
                else:
                    self.currentGame = self.next_game(self.currentGame, self.all_games)
                    # print(f'cycle through all {len(self.games)} games.')
            elif self.mode == 'cycle_favorite':
                self.currentGame = self.next_game(self.currentGame, self.favorite_games)
                # print(f'cycle through all {len(self.favorite_games)} favorite games.')
            elif self.mode == 'cycle_active':
                self.currentGame = self.next_game(self.currentGame, self.active_games)
                # print(f'cycle through all {len(self.active_games)} active games.')
            if self.gameCount == 0:
                self.display_stuff()
                for i in range(3):
                    draw.text((2, 11 * i), self.lines[i], font = self.bgfont, fill=self.textColor)
            else:
                self.loadGame(self.currentGame)
                if self.ind == 'in':
                    self.DrawInProgressGame(draw)    
                else:
                    self.display_stuff()
                    for i in range(3):
                        draw.text((2, 11 * i), self.lines[i], font = self.bgfont, fill=self.textColor)
            ######################################################
            if self.is_paused:
                draw.line(((125,0),(125,2)), fill='White', width=1)
                draw.line(((127,0),(127,2)), fill='White', width=1)
            self.icon.save("static/mlb.bmp", "BMP")
            self.dirty = True
        if self.matrix:
            self.my_canvas.Clear()
            self.my_canvas.SetImage(self.icon,0,0)
            return self.my_canvas

    def DrawInProgressGame(self, draw):
        # Background fill with "team color"
        self.FillAwayColor(draw)
        self.FillHomeColor(draw)
        # Display Team Logos
        self.icon.paste(self.teamLogos[self.away_team_abbrev], box=(0,0))
        self.icon.paste(self.teamLogos[self.home_team_abbrev], box=(0,16))
        # Display Team Abbreviations in Team Primary Color, and Run counts (in white)
        draw.text((17, 1), self.away_team_abbrev, font = self.font, fill=TeamColors[self.away_team_abbrev][1])
        draw.text((19, 8), self.away_runs,        font = self.font, fill=self.textColor)
        draw.text((17,17), self.home_team_abbrev, font = self.font, fill=TeamColors[self.home_team_abbrev][1])
        draw.text((19,24), self.home_runs,        font = self.font, fill=self.textColor)
        # Draw the empty bases and fill the occupied ones
        self.DrawBases(draw, (255,255,255), (238,232,67))
        # Draw Inning and State (Top, Mid, Bot)
        draw.text((40,21), str(self.inning), font = self.font, fill=self.textColor)
        self.DrawInningState(draw)
        # Draw the Balls - Strikes
        draw.text((50,17), str(self.balls),   font = self.font, fill=self.textColor)
        draw.text((55,17), "-",          font = self.font, fill=self.textColor)
        draw.text((59,17), str(self.strikes), font = self.font, fill=self.textColor)
        # Draw the outs
        self.DrawOuts(draw, (255,255,255), (238,232,67))
        # Draw the Pitcher and Batter
        draw.text((65, 1), self.pitcher_text, font = self.font, fill=self.textColor)
        draw.text((65, 8), self.batter_text,  font = self.font, fill=self.textColor)
        i = 0
        for line in textwrap.wrap(self.last_play, width=25, expand_tabs=False, max_lines=4):
            draw.text((1,34 + i * 8), line, font = self.font, fill=self.textColor)
            i += 1

    def FillAwayColor(self, draw):
        draw.rectangle([(0,0),(31,15)],fill=self.awayColor, outline=self.awayColor,width=1)
        
    def FillHomeColor(self, draw):
        draw.rectangle([(0,16),(31,31)],fill=self.homeColor, outline=self.homeColor,width=1)
            
    def FillScoreBoard(self, draw, color):
        draw.rectangle([(32,0),(63,31)],fill=color, outline=color,width=1)
    
    def DrawBases(self, draw, outline_color, fill_color):
        draw.line([(32, 0), (32,31)], fill=(127,127,127), width=1)
        # Fill bases if occupied fill = graphics.Color(238,232,67)
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
