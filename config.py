# Before a match thread change the settings here
import sys

CONFIG = {
    'stat_url': "http://volleynet.at/datavolley/2016/women/&D1-" + sys.argv[1] + "_REPORT.htm",
    'score_url': "http://volleynet.at/datavolley/2016/women/D1-" + sys.argv[1] + "_LIVE.htm",
    'links': "[volleynet](https://www.volleynet.at)",
    'stream': "TBA",
    'competition': "Austrian Volley League Women: Grunddurchgang"
}

TELEGRAM_TOKEN = 'do not share'
