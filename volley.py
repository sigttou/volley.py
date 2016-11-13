#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# volley.py - Create match thread style info for reddit from volleyball games
# Further Information: https://crap.solutions/pages/volley.html - https://github.com/sigttou/volley.py

import urllib3
import sys
from bs4 import BeautifulSoup

if len(sys.argv) < 2:
    print("./volley <GAME NR.>")
    exit(-1)

# Variables we want to receive from the website
HOME_TEAM = ""
AWAY_TEAM = ""
HOME_POINTS = ""
AWAY_POINTS = ""
SET_TIME = [None] * 5
HOME_SET_POINTS = [None] * 5
AWAY_SET_POINTS = [None] * 5
REFS = [None] * 2
LOCATION = ""
KICK_OFF = ""
HOME_MEMBERS = {}
AWAY_MEMBERS = {}

# Get some info from Stats website
url = "http://volleynet.at/datavolley/2016/women/&D1-" + sys.argv[1] + "_REPORT.htm"
http_pool = urllib3.connection_from_url(url)
r = http_pool.urlopen('GET',url)
content = str(r.data.decode())
soup = BeautifulSoup(content, 'html.parser')

for span in soup.find_all('span'):
    if span.attrs.get('id') == 'corpo_pagina_L_Impianto':
        LOCATION = span.contents[0]
    elif span.attrs.get('id') and span.attrs.get('id').startswith("corpo_pagina_L_Arbitro"):
        try:
            REFS[int(span.attrs.get('id')[-1])-1] = span.contents[0]
        except:
            pass
    elif span.attrs.get('id') == 'corpo_pagina_L_MatchHour':
        KICK_OFF = span.contents[0]
    elif span.attrs.get('id') and span.attrs.get('id').startswith("corpo_pagina_GV_elenco_casa_L_Nome_"):
        HOME_MEMBERS[len(HOME_MEMBERS)] = span.contents[0]
    elif span.attrs.get('id') and span.attrs.get('id').startswith("corpo_pagina_GV_elenco_fuori_L_Nome_"):
        AWAY_MEMBERS[len(AWAY_MEMBERS)] = span.contents[0]


# Now we fetch the website with the live stats
url = "http://volleynet.at/datavolley/2016/women/D1-" + sys.argv[1] + "_LIVE.htm"
http_pool = urllib3.connection_from_url(url)
r = http_pool.urlopen('GET',url)
content = str(r.data.decode())
soup = BeautifulSoup(content, 'html.parser')

for span in soup.find_all('span'):
    if span.attrs.get('id') == 'L_HomeTeam':
        HOME_TEAM = span.contents[0]
    elif span.attrs.get('id') == 'L_WonSetHome':
        HOME_POINTS = span.contents[0]
    elif span.attrs.get('id') == 'L_GuestTeam':
        AWAY_TEAM = span.contents[0]
    elif span.attrs.get('id') == 'L_WonSetGuest':
        AWAY_POINTS = span.contents[0]
    elif span.attrs.get('id').startswith("L_TimeSet"):
        try:
            SET_TIME[int(span.attrs.get('id')[-1])-1] = int(span.contents[0][:-1])
        except:
            pass
    elif span.attrs.get('id').startswith("L_Set"):
        try:
            index = int(span.attrs.get('id')[5]) - 1
            points = int(span.contents[0])
        except:
            pass
        if span.attrs.get('id').endswith("Guest"):
            HOME_SET_POINTS[index] = points
        else:
            AWAY_SET_POINTS[index] = points
    

HOME_OVERALL = sum(HOME_SET_POINTS)
AWAY_OVERALL = sum(AWAY_SET_POINTS)
TIME_OVERALL = sum(SET_TIME)

data = {'home_team': HOME_TEAM,
        'away_team': AWAY_TEAM,
        'home_points': HOME_POINTS,
        'away_points': AWAY_POINTS,
        'home_over': HOME_OVERALL,
        'away_over': AWAY_OVERALL,
        'time_over': TIME_OVERALL,
        'location': LOCATION,
        'kick_off': KICK_OFF
        }

# And now we print the info

header = "#{time_over}': {home_team} {home_points} : {away_points} {away_team}".format(**data)
print(header)
print("---")
print("**Competition:** Austrian Volley League Women, regular season")
print()
print("**Kick Off Times:** {kick_off} CEST".format(**data))
print()
print("**Venue:** {location}".format(**data))
print()
print("**Referees:** {}, {}".format(REFS[0], REFS[1]))
print()
print("**Stream:** TBA")
print()
print("**Other Links:** [volleynet](https://www.volleynet.at)")
print()
print("--")
print("---")
print("--")
print()
print("#The Teams")
print()
print("\# | {home_team} | \# | {away_team}".format(**data))
print("---|---|---|----")
for i in range(0, max(len(HOME_MEMBERS), len(AWAY_MEMBERS))):
    print(u"{} | {} | {} | {}".format( i, HOME_MEMBERS.get(i), i, AWAY_MEMBERS.get(i)))
print()
print("--")
print("---")
print("--")
print()
print("#Scoreline")
print()
print("Set | Time | Scoreline")
print("---|---|----")
for i in range(0,len(SET_TIME)):
    table_line = "{} | {}' | {}:{}".format(i+1, SET_TIME[i], AWAY_SET_POINTS[i], HOME_SET_POINTS[i])
    print(table_line)
overall = "**OA** | **{time_over}'** | **{home_over}:{away_over}**".format(**data)
print(overall)
print()
print("--")
print("---")
print("--")
print()
print("#Match Updates")
print()
print("--")
print()
