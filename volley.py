#!/usr/bin/env python
# -*- coding: utf-8 -*-
# volley.py - Create match thread style info for reddit from volleyball games
# Further Information:
# https://crap.solutions/pages/volley.html https://github.com/sigttou/volley.py

import urllib3
from bs4 import BeautifulSoup
from string import Template
import praw
import OAuth2Util
from config import TELEGRAM_GROUP, TELEGRAM_TOKEN, TELEGRAM_ADMIN
from config import DEFAULT_COMP, DEFAULT_LINKS, SUBREDDIT, TEAM_DIR
from config import THREAD_TEMPLATE
from telegram.ext import Updater, CommandHandler
import logging
import os
from os import listdir
from os.path import isfile, join
import json
import re

# Enable logging
logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)
logger = logging.getLogger(__name__)


def match_update_routine(update, end=0):
    data = {'home_team': '',
            'away_team': '',
            'status': '',
            'home_points': 0,
            'away_points': 0,
            'home_over': 0,
            'away_over': 0,
            'time_over': 0,
            'kick_off': os.environ['VOLLEYPY_KICKOFF'],
            'competition': os.environ['VOLLEYPY_COMP'],
            'stream': os.environ['VOLLEYPY_STREAM'],
            'links': os.environ['VOLLEYPY_LINKS'],
            'teams': '',
            'scoreline': '',
            'updates': '',
            'score_url': '',
            'home_store': os.environ['VOLLEYPY_HJSON'],
            'away_store': os.environ['VOLLEYPY_AJSON'],
            'home_members': {},
            'away_members': {},
            'home_coaches': [],
            'away_coaches': [],
            'set_time': [None] * 5,
            'home_set_points': [None] * 5,
            'away_set_points': [None] * 5,
            }

    get_match_links(data)
    get_general_info(data)
    get_scoreline(data)

    if update:
        if end:
            data['status'] = "FT: "
            update = "**FINISHED: " + update + "**"
    add_updates(data, update)
    if end:
        open("updates", 'w').close()

    if os.environ['VOLLEYPY_COMMENT']:
        r = praw.Reddit("python3:VolleyAT1.0 (by /u/K-3PX)")
        OAuth2Util.OAuth2Util(r, configfile="oauth.ini")
        text = os.environ['VOLLEYPY_COMMENT']
        text = replace_kitnr(text, data)
        post = r.get_submission(url=os.environ['VOLLEYPY_REDDIT'])
        post.add_comment(text)
        os.environ['VOLLEYPY_COMMENT'] = ""

    post_thread(data, os.environ['VOLLEYPY_REDDIT'])


def get_match_links(data):
    spliturl = os.environ['VOLLEYPY_VOLLEYDATA'].split("/")
    part_1 = "/".join(spliturl[:-1]) + "/"
    part_2 = spliturl[-1].split("_")[0]
    data['score_url'] = part_1 + part_2 + "_LIVE.htm"


def get_general_info(data):
    with open(os.environ['VOLLEYPY_HJSON'], "r") as f:
        hloadfrom = json.loads(f.read())
    with open(os.environ['VOLLEYPY_AJSON'], "r") as f:
        aloadfrom = json.loads(f.read())
    data['home_team'] = hloadfrom['name']
    data['away_team'] = aloadfrom['name']
    data['home_members'] = hloadfrom['players']
    data['away_members'] = aloadfrom['players']
    data['home_coaches'] = hloadfrom['managers']
    data['away_coaches'] = aloadfrom['managers']

    data['teams'] += "\# | {home_team} | \# | {away_team}\n".format(**data)
    data['teams'] += "---|---|---|----\n"
    for i in range(0,
                   max(len(data['home_members']), len(data['away_members']))):
        data['teams'] += "{} | {} | {} | {}\n".format(
                list(data['home_members'].keys())[i] if
                len(data['home_members']) > i else "",
                data['home_members'][list(data['home_members'].keys())[i]] if
                len(data['home_members']) > i else "",
                list(data['away_members'].keys())[i] if
                len(data['away_members']) > i else "",
                data['away_members'][list(data['away_members'].keys())[i]] if
                len(data['away_members']) > i else "")
    data['teams'] += "|||\n"
    data['teams'] += u" | {} | | {}\n".format(data['home_coaches'][0],
                                              data['away_coaches'][0])


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
                data['set_time'][int(span.attrs.get('id')[-1])-1] = \
                        int(span.contents[0][:-1])
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
        data['scoreline'] += "{} | {}' | {}:{}\n".format(
                i+1,
                data['set_time'][i],
                data['home_set_points'][i],
                data['away_set_points'][i]
                )
    data['scoreline'] += ("**OA** | **{time_over}'** | " +
                          "**{home_over}:{away_over}**\n").format(**data)


def add_updates(data, update):
    if update:
        with open("updates", "a") as f:
            f.write("**" + str(data['time_over']) + "'**: " +
                    " " + update + "\n\n")
    with open("updates") as filein:
        data['updates'] = filein.read()
    data['updates'] = replace_kitnr(data['updates'], data)


def post_thread(data, url):
    with open(THREAD_TEMPLATE) as filein:
        src = Template(filein.read())
    result = src.substitute(data)
    r = praw.Reddit("python3:VolleyAT1.0 (by /u/K-3PX)")
    OAuth2Util.OAuth2Util(r, configfile="oauth.ini")
    if url:
        post = r.get_submission(url=url)
        post.edit(result)
    else:
        title = ("Match Thread: " +
                 "{home_team} Vs {away_team} [{competition}]").format(**data)
        post = r.submit(SUBREDDIT, title, result)
        os.environ['VOLLEYPY_REDDIT'] = post.url


def replace_kitnr(text, data):
    away_toreplace = [x[2:] for x in re.findall("#a[0-9]+", text)]
    home_toreplace = [x[2:] for x in re.findall("#h[0-9]+", text)]

    for entry in away_toreplace:
        if data['away_members'].get(entry):
            replacement = data['away_members'].get(entry).split()
            replacement = [x.title() for x in replacement]
            replacement = " ".join(replacement)
            text = re.sub("#a" + entry, replacement, text)
    for entry in home_toreplace:
        if data['home_members'].get(entry):
            replacement = data['home_members'].get(entry).split()
            replacement = [x.title() for x in replacement]
            replacement = " ".join(replacement)
            text = re.sub("#h" + entry, replacement, text)
    return text


def reset_env():
    os.environ['VOLLEYPY_REDDIT'] = ""
    os.environ['VOLLEYPY_STREAM'] = "TBA"
    os.environ['VOLLEYPY_COMP'] = DEFAULT_COMP
    os.environ['VOLLEYPY_VOLLEYDATA'] = ""
    os.environ['VOLLEYPY_LINKS'] = DEFAULT_LINKS
    os.environ['VOLLEYPY_HJSON'] = ""
    os.environ['VOLLEYPY_AJSON'] = ""
    os.environ['VOLLEYPY_KICKOFF'] = ""
    os.environ['VOLLEYPY_COMMENT'] = ""


def handl_update_match(bot, update):
    if not update.message.from_user.username == TELEGRAM_ADMIN:
        update.message.reply_text("WRONG USER NAME")
        return
    if not os.environ['VOLLEYPY_REDDIT']:
        update.message.reply_text("No reddit link set")
        return
    text = ""
    if len(update.message.text.split()) > 1:
        text = u" ".join(update.message.text.split()[1:])
    match_update_routine(text)
    update.message.reply_text("Match updated!")


def handl_end_match(bot, update):
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
    reset_env()
    update.message.reply_text("Match ended!")


def handl_init_match(bot, update):
    if not update.message.from_user.username == TELEGRAM_ADMIN:
        update.message.reply_text("WRONG USER NAME")
        return
    if len(update.message.text.split()) != 5:
        update.message.reply_text("Wrong number of parameters")
        return
    if os.environ['VOLLEYPY_VOLLEYDATA']:
        update.message.reply_text("Please end current game first")
        return
    tocheck = update.message.text.split()[1]
    if not (tocheck.startswith("http://volleynet.at/") and
            tocheck.endswith("LIVE.htm")):
        update.message.reply_text("Wrong init LIVE link!")
        return
    hjson = TEAM_DIR + update.message.text.split()[2] + ".json"
    if not isfile(hjson):
        update.message.reply_text("Home team does not exist")
        return
    ajson = TEAM_DIR + update.message.text.split()[3] + ".json"
    if not isfile(ajson):
        update.message.reply_text("Away team does not exist")
        return
    os.environ['VOLLEYPY_VOLLEYDATA'] = tocheck
    os.environ['VOLLEYPY_HJSON'] = hjson
    os.environ['VOLLEYPY_AJSON'] = ajson
    os.environ['VOLLEYPY_KICKOFF'] = update.message.text.split()[4]
    match_update_routine("")
    update.message.reply_text(os.environ['VOLLEYPY_REDDIT'] + " DONE!")


def handl_chg_reddit(bot, update):
    if not update.message.from_user.username == TELEGRAM_ADMIN:
        update.message.reply_text("WRONG USER NAME")
        return
    if len(update.message.text.split()) != 6:
        update.message.reply_text("Wrong number of parameters")
        return
    tocheck = update.message.text.split()[1]
    if not tocheck.startswith("https://www.reddit.com/r/" + SUBREDDIT):
        update.message.reply_text("Wrong reddit link!")
        return
    os.environ['VOLLEYPY_REDDIT'] = tocheck
    tocheck = update.message.text.split()[2]
    if not tocheck.startswith("http://volleynet.at/") and \
            not tocheck.endswith("LIVE.htm"):
        update.message.reply_text("Wrong init LIVE link!")
        return
    hjson = TEAM_DIR + update.message.text.split()[3] + ".json"
    if not isfile(hjson):
        update.message.reply_text("Home team does not exist")
        return
    ajson = TEAM_DIR + update.message.text.split()[4] + ".json"
    if not isfile(ajson):
        update.message.reply_text("Away team does not exist")
        return
    os.environ['VOLLEYPY_VOLLEYDATA'] = tocheck
    os.environ['VOLLEYPY_HJSON'] = hjson
    os.environ['VOLLEYPY_AJSON'] = ajson
    os.environ['VOLLEYPY_KICKOFF'] = update.message.text.split()[5]
    update.message.reply_text(os.environ['VOLLEYPY_REDDIT'] + " DONE!")


def handl_chg_comp(bot, update):
    if not update.message.from_user.username == TELEGRAM_ADMIN:
        update.message.reply_text("WRONG USER NAME")
        return
    if len(update.message.text.split()) < 2:
        update.message.reply_text("Wrong number of parameters")
        return
    os.environ['VOLLEYPY_COMP'] = u" ".join(update.message.text.split()[1:])
    update.message.reply_text(os.environ['VOLLEYPY_COMP'] + " DONE!")


def handl_chg_stream(bot, update):
    if not update.message.from_user.username == TELEGRAM_ADMIN:
        update.message.reply_text("WRONG USER NAME")
        return
    if len(update.message.text.split()) != 2:
        update.message.reply_text("Wrong number of parameters")
        return
    link = update.message.text.split()[1]
    os.environ['VOLLEYPY_STREAM'] = "[stream](" + link + ")"
    update.message.reply_text(os.environ['VOLLEYPY_STREAM'] + " DONE!")


def handl_comment_match(bot, update):
    if not (update.message.from_user.username == TELEGRAM_ADMIN or
            str(update.message['chat']['id']) == TELEGRAM_GROUP):
        update.message.reply_text("WRONG USER NAME OR GROUP")
        return
    if not os.environ['VOLLEYPY_REDDIT']:
        update.message.reply_text("No reddit link set")
        return
    if len(update.message.text.split()) < 2:
        update.message.reply_text("Wrong number of parameters")
        return

    name = update.message.from_user['first_name']
    text = name + " said: "
    text += u" ".join(update.message.text.split()[1:])
    os.environ['VOLLEYPY_COMMENT'] = text
    match_update_routine("")
    update.message.reply_text("Comment added!")


def handl_list_teams(bot, update):
    if not update.message.from_user.username == TELEGRAM_ADMIN:
        update.message.reply_text("WRONG USER NAME")
        return
    if len(update.message.text.split()) != 1:
        update.message.reply_text("Wrong number of parameters")
        return
    reply = [f for f in listdir(TEAM_DIR) if isfile(join(TEAM_DIR, f))]
    reply = [e.split(".")[:-1][0] for e in reply]
    reply = "\n".join(reply)
    update.message.reply_text(reply)


def handl_info(bot, update):
    reply = "'/i <LIVE_LINK> <HOME_TEAM> <AWAY_TEAM> <KICKOFF_TIME>' " + \
            "will init the match thread\n"
    reply += "'/u <UPDATE>' will add the given update to the thread\n"
    reply += "'/c <COMMENT>' will add a comment to the thread " + \
             "possible from the configured group\n"
    reply += "'/e <FINALUPDATE>' " + \
             "will reset the bot and set the one given update\n"
    reply += "'/comp <COMP>' " + \
             "will change the competition if it's not the default\n"
    reply += "'/reddit <REDDIT_LINK> <LIVE_LINK> <HOME_TEAM> <AWAY_TEAM> " + \
             "<KICKOFF_TIME>' " + \
             "load already existing thread\n"
    reply += "'/stream <STREAM_LINK>' will set a live stream\n"
    reply += "'/listteams' get a list of available teams to set\n"
    update.message.reply_text(reply)


def main():
    reset_env()
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("u", handl_update_match))
    dp.add_handler(CommandHandler("e", handl_end_match))
    dp.add_handler(CommandHandler("i", handl_init_match))
    dp.add_handler(CommandHandler("c", handl_comment_match))
    dp.add_handler(CommandHandler("comp", handl_chg_comp))
    dp.add_handler(CommandHandler("reddit", handl_chg_reddit))
    dp.add_handler(CommandHandler("stream", handl_chg_stream))
    dp.add_handler(CommandHandler("help", handl_info))
    dp.add_handler(CommandHandler("start", handl_info))
    dp.add_handler(CommandHandler("listteams", handl_list_teams))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
