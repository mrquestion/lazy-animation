# -*- coding: utf-8 -*-

import os, sys

paths = os.path.dirname(os.path.realpath(__file__)).split(os.sep)
sys.path.append(os.sep.join(paths[:len(paths)-2]))
import tools

class Nyaa:
	NAME = "nyaa"
	OUTPUT = "output"
	URL = "http://www.nyaa.se/?page=rss&term={}"

	def __init__(self):
		tools.logo("nyaa.se Torrent Crawler")