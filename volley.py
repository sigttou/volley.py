#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# volley.py - Create match thread style info for reddit from volleyball games
# Further Information:
# https://crap.solutions/pages/volley.html - https://github.com/sigttou/volley.py

import urllib3
from bs4 import BeautifulSoup
from string import Template
import praw
import OAuth2Util
from config import TELEGRAM_GROUP, TELEGRAM_TOKEN, TELEGRAM_ADMIN, DEFAULT_COMP, DEFAULT_LINKS, SUBREDDIT
from telegram.ext import Updater, CommandHandler
import logging
import os

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def match_update_routine(update, end=0):
    data = {'home_team': '',
            'away_team': '',
            'home_points': 0,
            'away_points': 0,
            'home_over': 0,
            'away_over': 0,
            'time_over': 0,
            'location': '',
            'kick_off': '',
            'competition': os.environ['VOLLEYPY_COMP'],
            'refs': '',
            'stream': os.environ['VOLLEYPY_STREAM'],
            'links': os.environ['VOLLEYPY_LINKS'],
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
            'away_set_points': [None] * 5,
            'status': ''
            }
    get_match_links(data)
    get_general_info(data)
    get_scoreline(data)
    if update:
        if end:
            update = "**FINISHED: " + update + "**"
        add_updates(data, update)
    if end:
        post_thread(data, os.environ['VOLLEYPY_REDDIT'])
        open("updates", 'w').close()
        return
    post_thread(data, os.environ['VOLLEYPY_REDDIT'])


def get_match_links(data):
    spliturl = os.environ['VOLLEYPY_VOLLEYDATA'].split("/")
    part_1 = "/".join(spliturl[:-1]) + "/"
    part_2 = spliturl[-1].split("_")[0]
    data['stat_url'] = part_1 + "&" + part_2 + "_REPORT.htm"
    data['score_url'] = part_1 + part_2 + "_LIVE.htm"


def get_general_info(data):
    url = data['stat_url']
    http_pool = urllib3.connection_from_url(url)
    r = http_pool.urlopen('GET', url)
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
    data['teams'] += u" | {} | | {}\n".format(data['home_coach'],
                                              data['away_coach'])


def get_scoreline(data):
    url = data['score_url']
    http_pool = urllib3.connection_from_url(url)
    r = http_pool.urlopen('GET', url)
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

    for i in range(0, len(data['set_time'])):
        data['scoreline'] += "{} | {}' | {}:{}\n".format(i+1,
                                                         data['set_time'][i],
                                                         data['home_set_points'][i],
                                                         data['away_set_points'][i])
    data['scoreline'] += "**OA** | **{time_over}'** | **{home_over}:{away_over}**\n".format(**data)


def add_updates(data, update):
    with open("updates", "a") as f:
        f.write("**" + str(data['time_over']) + "'**: " + " " + update + "\n\n")


def post_thread(data, url):
    filein = open("updates")
    data['updates'] = filein.read()
    filein.close()
    filein = open("templates/thread.tpl")
    src = Template(filein.read())
    filein.close()
    result = src.substitute(data)
    r = praw.Reddit("python3:VolleyAT1.0 (by /u/K-3PX)")
    OAuth2Util.OAuth2Util(r, configfile="oauth.ini")
    if url:
        post = r.get_submission(url=url)
        post.edit(result)
    else:
        title = "Match Thread: {home_team} Vs {away_team} [{competition}]".format(**data)
        post = r.submit(SUBREDDIT, title, result)
        os.environ['VOLLEYPY_REDDIT'] = post.url


def update_match(bot, update):
    if not (update.message.from_user.username == TELEGRAM_ADMIN or update.message.id == TELEGRAM_GROUP):
        update.message.reply_text("WRONG USER NAME OR GROUP")
        return
    if not os.environ['VOLLEYPY_REDDIT']:
        update.message.reply_text("No reddit link set")
        return
    text = ""
    if len(update.message.text.split()) > 1:
        text = u" ".join(update.message.text.split()[1:])
    match_update_routine(text, 1)
    update.message.reply_text("Match updated!")


def end_match(bot, update):
    if not update.message.from_user.username == TELEGRAM_ADMIN:
        update.message.reply_text("WRONG USER NAME")
        return
    if not os.environ['VOLLEYPY_REDDIT']:
        update.message.reply_text("No reddit link set")
        return
    text = ""
    if len(update.message.text.split()) > 1:
        text = u" ".join(update.message.text.split()[1:])
    match_update_routine(text, 1)
    os.environ['VOLLEYPY_REDDIT'] = ""
    os.environ['VOLLEYPY_STREAM'] = "TBA"
    os.environ['VOLLEYPY_VOLLEYDATA'] = ""
    update.message.reply_text("Match ended!")


def init_match(bot, update):
    if not update.message.from_user.username == TELEGRAM_ADMIN:
        update.message.reply_text("WRONG USER NAME")
        return
    if len(update.message.text.split()) != 2:
        update.message.reply_text("Wrong number of parameters")
        return
    tocheck = update.message.text.split()[1]
    if not tocheck.startswith("http://volleynet.at/") and not tocheck.endswith("LIVE.htm"):
        update.message.reply_text("Wrong init LIVE link!")
        return
    os.environ['VOLLEYPY_VOLLEYDATA'] = tocheck
    match_update_routine("")
    update.message.reply_text(os.environ['VOLLEYPY_REDDIT'] + " DONE!")


def chg_reddit(bot, update):
    if not update.message.from_user.username == TELEGRAM_ADMIN:
        update.message.reply_text("WRONG USER NAME")
        return
    if len(update.message.text.split()) != 3:
        update.message.reply_text("Wrong number of parameters")
        return
    tocheck = update.message.text.split()[1]
    if not tocheck.startswith("https://www.reddit.com/r/" + SUBREDDIT):
        update.message.reply_text("Wrong reddit link!")
        return
    os.environ['VOLLEYPY_REDDIT'] = tocheck
    tocheck = update.message.text.split()[2]
    if not tocheck.startswith("http://volleynet.at/") and not tocheck.endswith("LIVE.htm"):
        update.message.reply_text("Wrong init LIVE link!")
        return
    os.environ['VOLLEYPY_VOLLEYDATA'] = tocheck
    update.message.reply_text(os.environ['VOLLEYPY_REDDIT'] + " DONE!")


def chg_comp(bot, update):
    if not update.message.from_user.username == TELEGRAM_ADMIN:
        update.message.reply_text("WRONG USER NAME")
        return
    if len(update.message.text.split()) < 2:
        update.message.reply_text("Wrong number of parameters")
        return
    os.environ['VOLLEYPY_COMP'] = u" ".join(update.message.text.split()[1:])
    update.message.reply_text(os.environ['VOLLEYPY_COMP'] + " DONE!")


def chg_stream(bot, update):
    if not update.message.from_user.username == TELEGRAM_ADMIN:
        update.message.reply_text("WRONG USER NAME")
        return
    if len(update.message.text.split()) != 2:
        update.message.reply_text("Wrong number of parameters")
        return
    link = update.message.text.split()[1]
    os.environ['VOLLEYPY_STREAM'] = "[stream](" + link + ")"
    update.message.reply_text(os.environ['VOLLEYPY_STREAM'] + " DONE!")


def info(bot, update):
    reply = "'/i <LIVE_LINK>' will init the match thread\n"
    reply += "'/u <UPDATE>' will add the given update to the thread\n"
    reply += "'/e <FINALUPDATE>' will reset the bot and set the one given update\n"
    reply += "'/comp <COMP>' will change the competition if it's not the default\n"
    reply += "'/reddit <REDDIT_LINK> <LIVE_LINK>' load already existing thread\n"
    reply += "'/stream <STREAM_LINK> will set a live stream'\n"
    update.message.reply_text(reply)


def main():
    os.environ['VOLLEYPY_REDDIT'] = ""
    os.environ['VOLLEYPY_STREAM'] = "TBA"
    os.environ['VOLLEYPY_COMP'] = DEFAULT_COMP
    os.environ['VOLLEYPY_VOLLEYDATA'] = ""
    os.environ['VOLLEYPY_LINKS'] = DEFAULT_LINKS
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("u", update_match))
    dp.add_handler(CommandHandler("e", end_match))
    dp.add_handler(CommandHandler("i", init_match))
    dp.add_handler(CommandHandler("comp", chg_comp))
    dp.add_handler(CommandHandler("reddit", chg_reddit))
    dp.add_handler(CommandHandler("stream", chg_stream))
    dp.add_handler(CommandHandler("help", info))
    dp.add_handler(CommandHandler("start", info))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
