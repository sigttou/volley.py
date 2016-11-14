#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# volley.py - Create match thread style info for reddit from volleyball games
# Further Information: https://crap.solutions/pages/volley.html - https://github.com/sigttou/volley.py

import urllib3
import sys
from bs4 import BeautifulSoup
from string import Template

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
HOME_NUMS = {}
AWAY_MEMBERS = {}
AWAY_NUMS = {}
HOME_COACH = ""
AWAY_COACH = ""

# Get some info from Stats website
url = "http://volleynet.at/datavolley/2016/women/&D1-" + sys.argv[1] + "_REPORT.htm"
http_pool = urllib3.connection_from_url(url)
r = http_pool.urlopen('GET',url)
content = str(r.data.decode())
soup = BeautifulSoup(content, 'html.parser')

lookfor = []
for td in soup.find_all('td'):
    if td.attrs.get('class') == ["TabResults_Value"]:
        if td.contents[0].attrs.get('color') == "#333333":
            lookfor.append(td.contents[0])

for i in range(0, len(lookfor)):
    analyse = lookfor[i].contents
    if len(analyse) > 1:
        analyse = analyse[1]
    else:
        continue
    if analyse.attrs.get('id') and analyse.attrs.get('id').startswith("corpo_pagina_GV_elenco_casa_L_Nome_"):
        HOME_MEMBERS[len(HOME_MEMBERS)] = analyse.contents[0]
        HOME_NUMS[len(HOME_NUMS)] = lookfor[i-1].contents[0]
    elif analyse.attrs.get('id') and analyse.attrs.get('id').startswith("corpo_pagina_GV_elenco_fuori_L_Nome_"):
        AWAY_MEMBERS[len(AWAY_MEMBERS)] = analyse.contents[0]
        AWAY_NUMS[len(AWAY_NUMS)] = lookfor[i-1].contents[0]

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
    elif span.attrs.get('id') == 'corpo_pagina_Coach_Casa':
        HOME_COACH = span.contents[0][1:-1]
    elif span.attrs.get('id') == 'corpo_pagina_Coach_Fuori':
        AWAY_COACH = span.contents[0][1:-1]


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
COMPETITION = "Austrian Volley League Women, regular season"
STREAM = "TBA"
LINKS = ""

data = {'home_team': HOME_TEAM,
        'away_team': AWAY_TEAM,
        'home_points': HOME_POINTS,
        'away_points': AWAY_POINTS,
        'home_over': HOME_OVERALL,
        'away_over': AWAY_OVERALL,
        'time_over': TIME_OVERALL,
        'location': LOCATION,
        'kick_off': KICK_OFF,
        'competition': COMPETITION,
        'refs': ", ".join(REFS),
        'stream': STREAM,
        'links': LINKS,
        'teams': "",
        'scoreline': "",
        'updates': ""
        }

# Team table sucks in template, so here is the code for it:

data['teams'] += "\# | {home_team} | \# | {away_team}\n".format(**data)
data['teams'] += "---|---|---|----\n"
for i in range(0, max(len(HOME_MEMBERS), len(AWAY_MEMBERS))):
    data['teams'] += "{} | {} | {} | {}\n".format( HOME_NUMS.get(i) if HOME_NUMS.get(i) else "", HOME_MEMBERS.get(i) if HOME_MEMBERS.get(i) else "", AWAY_NUMS.get(i) if AWAY_NUMS.get(i) else "", AWAY_MEMBERS.get(i) if AWAY_MEMBERS.get(i) else "")
data['teams'] += "|||\n"
data['teams'] += u" | {} | | {}\n".format(HOME_COACH, AWAY_COACH)


for i in range(0,len(SET_TIME)):
    data['scoreline'] += "{} | {}' | {}:{}\n".format(i+1, SET_TIME[i], AWAY_SET_POINTS[i], HOME_SET_POINTS[i])
data['scoreline'] += "**OA** | **{time_over}'** | **{home_over}:{away_over}**\n".format(**data)

filein = open("templates/thread.tpl")
src = Template(filein.read())
result = src.substitute(data)
print(result)
