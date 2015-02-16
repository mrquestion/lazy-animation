# -*- coding: utf-8 -*-

import os, sys
import re
import json
import multiprocessing as mp
import requests as rq
import lxml
from lxml import etree
del etree

paths = os.path.dirname(os.path.realpath(__file__)).split(os.sep)
sys.path.append(os.sep.join(paths[:-2]))
import tools

def get_term_list(id, no):
	url = "http://gall.dcinside.com/board/view/?id={}&no={}".format(id, no)
	print("Search from '{}'".format(url))
	rs = rq.get(url)

	content = rs.text if rs.ok else ''
	lines = content.split("<br>")

	'''
	result = []
	lines = [ line for line in lines if line.startswith("제목") ]
	for line in lines:
		m = re.match(r"제목 : ([^/]*)/?([^/]*)/?([^/]*)", line)
		if m: result.append(dict(ko=m.group(1).strip(), jp=m.group(2).strip(), en=m.group(3).strip()))
	return result
	'''
	lines = [ line for line in lines if line.startswith("제목") ]
	for line in lines:
		m = re.match(r"제목 : ([^/]*)/?([^/]*)/?([^/]*)", line)
		if m:
			ko = m.group(1).strip()
			jp = m.group(2).strip()
			en = m.group(3).strip()
			if len(en) == 0:
				if len(jp) == 0: en = ko
				else: en = '/'.join([ ko, jp ])
			yield dict(ko=ko, jp=jp, en=en)

def get_nyaa_list(terms):
	url_format = "http://www.nyaa.se/?page=rss&term={}"

	def get_release_list(name, term):
		words = name.split()
		words.extend(term.split())
		url = url_format.format('+'.join(words))
		print("Search from '{}'".format(url))
		rs = rq.get(url)
		content = rs.text if rs.ok else ''
		root = lxml.etree.XML(content)
		#return root.xpath('/rss/channel/item')
		return words, root.xpath('/rss/channel/item')

	prefixes = [ "Leopard Raws", "Zero Raws" ]

	'''
	def get_release_list(term):
		for prefix in prefixes:
			words = name.split()
			words.extend(term.split())
			term = '+'.join(words)
			url = url_format.format(term)
			print("Search from '{}'".format(url))
			rs = rq.get(url)
			content = rs.text if rs.ok else ''
			root = lxml.etree.XML(content)
			return term, root.xpath('/rss/channel/item')
			'''

	'''
	for term in terms:
		result = get_release_list("Leopard Raws", term["en"])
		print(" - {} results found.".format(len(result)))
		yield dict(term=term["en"], count=len(result))
		'''
	for term in terms:
		for prefix in prefixes:
			fixed_term, items = get_release_list(prefix, term["en"])
			yield dict(term=fixed_term, count=len(items))
	'''
	pool = mp.Pool(mp.cpu_count())
	result = pool.map(get_release_list, terms)
	for term, items in result:
		yield dict(term=term, count=len(items))
		'''

def main(argc, args):
	#terms = [ x for x in get_term_list("ani1_new1", 3836730) ]
	terms = []
	terms.extend(get_term_list("ani1_new1", 3836730))
	terms.extend(get_term_list("ani1_new1", 3836733))
	print(" - {} results found.".format(len(terms)))
	#for x in terms: print(str(x).encode())

	filename = '.'.join([ __file__, "json" ])
	with open(filename, "wb") as wbo:
		print(" - Results save to '{}'".format(filename))
		#wbo.write(json.dumps(terms, indent=4).encode("utf-8"))
		s = str(terms)
		s = s.replace("'", '"')
		s = s.replace(', ', ',{}\t\t'.format(os.linesep))
		s = s.replace('[', '[{}\t'.format(os.linesep))
		s = s.replace(']', '{}]'.format(os.linesep))
		s = s.replace('{', '{{{}\t\t'.format(os.linesep))
		s = s.replace('}', '{}\t}}'.format(os.linesep))
		s = s.replace('}},{}\t\t'.format(os.linesep), '}},{}\t'.format(os.linesep))
		#s = s.replace('}, {', '}},{}    {{{}'.format(os.linesep, os.linesep))
		wbo.write(s.encode("utf-8"))
		print()

	result = [ x for x in get_nyaa_list(terms) ]
	print()
	filename = '.'.join([ __file__, "txt" ])
	with open(filename, "w") as wo:
		print(" - Results save to '{}'".format(filename))
		for x in result:
			wo.write("Keyword: {}{}".format(' '.join(x["term"]), os.linesep))
			wo.write(" - {} results.{}".format(x["count"], os.linesep))
		print()
	result = [ x["term"] for x in result if x["count"] > 0 ]
	print("Maybe {} keywords valid.".format(len(result)))
	print()

	filename = "nyaa-words.json"
	'''
	words = [ '[' ]
	for x in result:
		words.append('"{}"'.format(x))
	words.append(']')
	'''
	words = [ '[', '' ]
	for x in result:
		words.append('"{}",'.format(' '.join(x)))
	words.extend([ '', ']' ])
	with open(filename, "w") as wo:
		#wo.write(os.linesep.join(words))
		wo.write('\n'.join(words))

	print("End.")

if __name__ == "__main__":
	mp.freeze_support()
	main(len(sys.argv), sys.argv)

'''
http://gall.dcinside.com/board/view/?id=ani1_new1&no=3836730&page=1
http://gall.dcinside.com/board/view/?id=ani1_new1&no=3836733&page=1
http://www.nyaa.se/?page=search&cats=0_0&filter=0&term=ohys
'''