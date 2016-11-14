#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# volley.py - Create match thread style info for reddit from volleyball games
# Further Information: https://crap.solutions/pages/volley.html - https://github.com/sigttou/volley.py

import urllib3
import sys
from bs4 import BeautifulSoup
from string import Template


def main():
    if len(sys.argv) < 2:
        print("./volley <GAME NR.>")
        exit(-1)

    data = {'home_team': '',
            'away_team': '',
            'home_points': 0,
            'away_points': 0,
            'home_over': 0,
            'away_over': 0,
            'time_over': 0,
            'location': '',
            'kick_off': '',
            'competition': '',
            'refs': '',
            'stream': '',
            'links': '',
            'teams': '',
            'scoreline': '',
            'updates': '',
            'stat_url': '',
            'score_url': '',
            'home_members': {},
            'away_members': {},
            'home_nums': {},
            'away_nums': {},
            'home_coach': '',
            'away_coach': '',
            'set_time': [None] * 5,
            'home_set_points': [None] * 5,
            'away_set_points': [None] * 5
            }
    parse_config(data)
    get_general_info(data)
    get_scoreline(data)
    print_thread_content(data)
    exit(0)


def parse_config(data):
    #Config
    from config import CONFIG
    for k in CONFIG:
        data[k] = CONFIG[k]


def get_general_info(data):
    url = data['stat_url']
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
            data['home_members'][len(data['home_members'])] = analyse.contents[0]
            data['home_nums'][len(data['home_nums'])] = lookfor[i-1].contents[0]
        elif analyse.attrs.get('id') and analyse.attrs.get('id').startswith("corpo_pagina_GV_elenco_fuori_L_Nome_"):
            data['away_members'][len(data['away_members'])] = analyse.contents[0]
            data['away_nums'][len(data['away_nums'])] = lookfor[i-1].contents[0]
    
    for span in soup.find_all('span'):
        if span.attrs.get('id') == 'corpo_pagina_L_Impianto':
            data['location'] = span.contents[0]
        elif span.attrs.get('id') and span.attrs.get('id').startswith("corpo_pagina_L_Arbitro"):
            try:
                if(not data['refs']):
                    data['refs'] += span.contents[0] + ","
                else:
                    data['refs'] += " " + span.contents[0]
            except:
                pass
        elif span.attrs.get('id') == 'corpo_pagina_L_MatchHour':
            data['kick_off'] = span.contents[0]
        elif span.attrs.get('id') == 'corpo_pagina_Coach_Casa':
            data['home_coach'] = span.contents[0][1:-1]
        elif span.attrs.get('id') == 'corpo_pagina_Coach_Fuori':
            data['away_coach'] = span.contents[0][1:-1]
        elif span.attrs.get('id') == 'corpo_pagina_L_HomeTeam':
            data['home_team'] = span.contents[0]
        elif span.attrs.get('id') == 'corpo_pagina_L_GuestTeam':
            data['away_team'] = span.contents[0]

    data['teams'] += "\# | {home_team} | \# | {away_team}\n".format(**data)
    data['teams'] += "---|---|---|----\n"
    for i in range(0, max(len(data['home_members']), len(data['away_members']))):
        data['teams'] += "{} | {} | {} | {}\n".format(
                data['home_nums'].get(i) if data['home_nums'].get(i) else "", 
                data['home_members'].get(i) if data['home_members'].get(i) else "",
                data['away_nums'].get(i) if data['away_nums'].get(i) else "",
                data['away_members'].get(i) if data['away_members'].get(i) else "")
    data['teams'] += "|||\n"
    data['teams'] += u" | {} | | {}\n".format(  data['home_coach'],
                                                data['away_coach'])


def get_scoreline(data):
    url = data['score_url']
    http_pool = urllib3.connection_from_url(url)
    r = http_pool.urlopen('GET',url)
    content = str(r.data.decode())
    soup = BeautifulSoup(content, 'html.parser')

    for span in soup.find_all('span'):
        if span.attrs.get('id') == 'L_WonSetHome':
            data['home_points'] = span.contents[0]
        elif span.attrs.get('id') == 'L_WonSetGuest':
            data['away_points'] = span.contents[0]
        elif span.attrs.get('id').startswith("L_TimeSet"):
            try:
                data['set_time'][int(span.attrs.get('id')[-1])-1] = int(span.contents[0][:-1])
            except:
                pass
        elif span.attrs.get('id').startswith("L_Set"):
            try:
                index = int(span.attrs.get('id')[5]) - 1
                points = int(span.contents[0])
            except:
                pass
            if span.attrs.get('id').endswith("Guest"):
                data['away_set_points'][index] = points
            else:
                data['home_set_points'][index] = points
    
    data['home_over'] = sum(data['home_set_points'])
    data['away_over'] = sum(data['away_set_points'])
    data['time_over'] = sum(data['set_time'])

    for i in range(0,len(data['set_time'])):
        data['scoreline'] += "{} | {}' | {}:{}\n".format(   i+1, 
                                                            data['set_time'][i],
                                                            data['home_set_points'][i], 
                                                            data['away_set_points'][i])
    data['scoreline'] += "**OA** | **{time_over}'** | **{home_over}:{away_over}**\n".format(**data)
   

def print_thread_content(data):
    filein = open("templates/thread.tpl")
    src = Template(filein.read())
    result = src.substitute(data)
    print(result)


if __name__ == '__main__':
    main()
