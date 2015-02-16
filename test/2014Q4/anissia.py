# -*- coding: utf-8 -*-

import os, sys
import json
import requests as rq
from bs4 import BeautifulSoup as bs
from urllib.parse import urlparse, urlunparse, parse_qs as qsparse, urlencode, quote, unquote, quote_from_bytes, unquote_to_bytes#, ParseResult

import inspect
import pprint
def pp(o): pprint.PrettyPrinter(indent=4).pprint(o)

#PREPARED_PARTS = [ "http", "www.anissia.net", "/anitime/list", "", "w={}", "" ]
#parts = list(PREPARED_PARTS)
#parts[4] = parts[4].format(0)
#url = urlunparse(parts)

BASE_URL1 = "http://www.anissia.net/anitime/list?w={}"
BASE_URL2 = "http://www.anissia.net/anitime/cap?i={}"
FIRST_DATE = "20140701000000"
LAST_DATE = "20141231235959"

def get_weekday():
	for i in range(0, 8):
		url = BASE_URL1.format(i)
		rs = rq.get(url)
		if rs.ok:
			datas = json.loads(rs.content.decode())
			for data in datas: yield data

def get_subtitle(data):
	url = BASE_URL2.format(data["i"])
	rs = rq.get(url)
	if rs.ok:
		datas = json.loads(rs.content.decode())
		for data in datas: yield data

def get_fastest(datas):
	episode = "00000"
	fastest = LAST_DATE
	url = None
	for data in datas:
		d, s, a = data["d"], data["s"], data["a"]
		if s > episode: episode, fastest, url = s, d, a
		elif FIRST_DATE < d < fastest: fastest, url = d, a
		if fastest == LAST_DATE: fastest = None
	return episode, fastest, url

def main(argc, args):
	for data in get_weekday():
		datas = [ data for data in get_subtitle(data) ]
		try: print(data["s"], get_fastest(datas))
		except: print(data["s"].encode(), get_fastest(datas))
		#break

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)

exit()


'''
for i in range(0, 8):
	i = 2
	url = BASE_URL1.format(i)
	rs = rq.get(url)
	if rs.ok:
		datas1 = json.loads(rs.content.decode())
		for data1 in datas1:
			try: print(data1)
			except: print(str(data1).encode())
			url = BASE_URL2.format(data1["i"])
			rs = rq.get(url)
			if rs.ok:
				datas2 = json.loads(rs.content.decode())
				episode = "00000"
				fastest = LAST_DATE
				url = None
				for data2 in datas2:
					d = data2["d"]
					s = data2["s"]
					a = data2["a"]
					if s > episode:
						episode = s
						fastest = d
						url = a
					elif FIRST_DATE < d < fastest:
						fastest = d
						url = a
				if fastest == LAST_DATE: fastest = None
				print(episode, fastest, url)
				#ds = [ data2["d"] for data2 in datas2 ]
				#print(ds)
			#break
	break
	'''