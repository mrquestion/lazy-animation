# -*- coding: utf-8 -*-

import json

bs = open("list-from-dc.py.json", "rb").read()
s = bs.decode()
data = json.loads(s)

for x in data:
	print(x["ko"])