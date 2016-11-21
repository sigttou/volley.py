#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
import urllib3
from bs4 import BeautifulSoup
import sys
import json
from config import TEAM_DIR

if len(sys.argv) != 3:
    print("team.py <URL> <NAME>")

store_name = sys.argv[2]
url = sys.argv[1]

http_pool = urllib3.connection_from_url(url)
r = http_pool.urlopen('GET', url)
content = str(r.data.decode())
soup = BeautifulSoup(content, 'html.parser')
to_store = {}

to_store['name'] = soup.find_all('h1')[0].contents[0]
to_store['managers'] = []
to_store['players'] = {}
to_look = soup.find_all('td')
i = 0
for td in to_look:
    if td.find("nobr"):
        if to_look[i-1].contents[0] == '\xa0':
            to_store['managers'] += [td.find("nobr").contents[0]]
        else:
            kitnum = int(to_look[i-1].contents[0])
            to_store['players'][kitnum] = td.find("nobr").contents[0]
    i = i + 1

with open(TEAM_DIR + store_name + ".json", "w") as f:
    f.write(json.dumps(to_store))

with open(TEAM_DIR + store_name + ".json", "r") as f:
    a = json.loads(f.read())
    print(a)
