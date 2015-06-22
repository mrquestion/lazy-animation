# -*- coding: utf-8 -*-

import os, sys
import re
import multiprocessing as mp
import requests as rq
from lxml import etree

paths = os.path.dirname(os.path.realpath(__file__)).split(os.sep)
sys.path.append(os.sep.join(paths[:-2]))
import tools

import inspect, pprint
def args(f): return inspect.getargspec(f)
def mems(o): return inspect.getmembers(o)
def pp(s): pprint.pprint(s, indent=4, width=80)
def pf(s): return pprint.pformat(s, indent=4, width=80)
def ppargs(f): pp(args(f))
def ppmems(o): pp(mems(o))

def get_term_list(id, no):
	url = "http://gall.dcinside.com/board/view/?id={}&no={}".format(id, no)
	print("Search from '{}'".format(url))
	rs = rq.get(url)

	root = etree.HTML(rs.content if rs.ok else "<error/>")
	imgs = root.xpath('//*[@id="dgn_content_de"]//td/img')
	for img in imgs:
		for x in img.itersiblings():
			if x.tail is not None:
				try:
					s = x.tail.encode("raw_unicode_escape").decode()
				except:
					s = x.tail.encode("raw_unicode_escape").replace(b'\xa0', b'\x20').decode()
				if s.startswith("제목"):
					b = x.getnext()
					if b.tail is None:
						yield dict(en=b.text)
					else:
						ko = b.text.encode("raw_unicode_escape").decode()
						tails = b.tail.split('/')
						en = tails[0]
						if len(tails) > 2:
							en = tails[2]
						yield dict(ko=ko, en=en)
					break
		#print(', '.join(img.getnext().getnext().getnext().itertext()).encode())
		'''
		bold = None
		for x in img.itersiblings():
			if x.tag is "b":
				bold = x
				break
		text = bold.text
		print(text.encode())
		'''
	'''
	ps = root.xpath('/html/body/div[@id="dgn_wrap"]/div[@id="dgn_gallery_wrap"]/div[@id="dgn_gallery_detail"]/div[@id="dgn_content_de"]/div[@class="re_gall_box_1"]/div[@class="con_substance"]/div[@class="s_write"]/table//tr/td/table//tr/td//p')
	for p in ps:
		en = p.xpath('./font[text()]|./span[text()]|./font/span[text()]')
		ko = p.xpath('./strong/font[text()]|./strong/span[text()]|./strong/font/span[text()]|./font/strong/span[text()]')
		if len(en) > 0 and len(ko) > 0:
			en, ko = en[0], ko[0]
			en, ko = tools.convert(en.text), tools.convert(ko.text)
			yield dict(en=en, ko=ko)
			'''

def get_nyaa_list(terms):
	url_format = "http://www.nyaa.se/?page=rss&term={}"

	def get_release_list(name, term):
		words = name.split()
		words.extend(term.split())
		url = url_format.format('+'.join(words))
		try: print("Search from '{}'".format(url))
		except: print("Search from '{}'".format(url.encode()))
		rs = rq.get(url)
		content = rs.text if rs.ok else "<html/>"
		root = etree.XML(content)
		#return root.xpath('/rss/channel/item')
		return words, root.xpath('/rss/channel/item')

	prefixes = [ "Leopard Raws", "Zero Raws" ]

	for term in terms:
		for prefix in prefixes:
			fixed_term, items = get_release_list(prefix, term["en"])
			yield dict(term=fixed_term, count=len(items))

def main(argc, args):
	#terms = [ x for x in get_term_list("anigallers_new", 1682331) ]
	terms = [ x for x in get_term_list("ani1_new1", 4136993) ]
	print(" - {} results found.".format(len(terms)))
	#for x in terms: print(str(x).encode())

	filename = '.'.join([ __file__, "json" ])
	with open(filename, "wb") as wbo:
		print(" - Results save to '{}'".format(filename))
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
			try: wo.write("Keyword: {}{}".format(' '.join(x["term"]), os.linesep))
			except: wo.write("Keyword: {}{}".format(' '.join(x["term"]).encode("raw_unicode_escape").deocde(), os.linesep))
			wo.write(" - {} results.{}".format(x["count"], os.linesep))
		print()
	#result = [ x["term"] for x in result if x["count"] > 0 ]
	result = [ x["term"] for x in result ]
	print("Maybe {} keywords valid.".format(len(result)))
	print()

	filename = "nyaa-words.json"
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
http://gall.dcinside.com/board/view/?id=ani1_new1&no=4136993
http://gall.dcinside.com/board/view/?id=ani1_new1&no=3836730&page=1
http://gall.dcinside.com/board/view/?id=ani1_new1&no=3836733&page=1
http://www.nyaa.se/?page=search&cats=0_0&filter=0&term=ohys
http://gall.dcinside.com/board/view/?id=anigallers_new&no=1682331
'''