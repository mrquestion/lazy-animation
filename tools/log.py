# -*- coding: utf-8 -*-

import os

class Log:
	BASEDIR = "log"

	def __init__(self, filepath=BASEDIR, filename=None, error=True):
		self.filepath = filepath
		self.filename = filename
		self.error = error
		self.og = self.print

	def print(self, *args, sep=' ', linesep=True):
		linesep = os.linesep if linesep else ''
		s = ''
		for x in args:
			if len(s) == 0:
				if type(x) is bytes:
					try: s = x.decode()
					except: s = str(x)
				elif type(x) is list:
					s = sep.join(str(y) for y in x)
				else: s = str(x)
			else:
				if type(x) is bytes:
					try: s = sep.join([ s, x.decode() ])
					except: s = sep.join([ s, str(x) ])
				elif type(x) is list:
					y = [ s ]
					y.extend(str(z) for z in x)
					s = sep.join(y)
				else: s = sep.join([ s, str(x) ])

		try: print(s, end=linesep, flush=True)
		except Exception as e:
			if self.error: print("Error: {}".format(e))

		if self.filename:
			if not os.path.exists(self.filepath):
				os.makedirs(self.filepath, exist_ok=True)

			filename = os.sep.join([ self.filepath, self.filename ])
			with open(filename, "a", newline=linesep) as abo:
				try: print(s, file=abo, end=linesep, flush=True)
				except Exception as e:
					if self.error: print("Error: {}".format(e))