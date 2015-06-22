# -*- coding: utf-8 -*-

import os, sys
import time, datetime, email.utils
import hashlib

import inspect
import pprint
def pp(o): pprint.PrettyPrinter(indent=4).pprint(o)
def ppf(o): return pprint.pformat(o, indent=4)
def mems(o): return inspect.getmembers(o)
def args(f): return inspect.getargspec(f)
def ppmems(o): pp(mems(o))
def ppargs(f): pp(args(f))

def get_logo(text="Please input logo text", border='='):
	text = text if type(text) is str else str(text)
	border = ''.join(border for x in range(0, len(text)+2))
	logo = [ border, " {} ".format(text), border, '' ]
	return logo

def logo(text="Please input logo text", border='='):
	print(os.linesep.join(get_logo(text=text, border=border)))

def timestamp(format="%Y%m%d-%H%M%S", rfc=None):
	if rfc is not None and type(rfc) in [ int, float ]:
		if rfc == 1123: return email.utils.formatdate(timeval=time.time, localtime=False, usegmt=True)
	else: return datetime.datetime.fromtimestamp(time.time()).strftime(format)

def md5(s):
	s = s if type(s) is str else str(s)
	e = hashlib.md5(s.encode("utf-8"))
	return e.hexdigest()

def convert(s, encoding="utf-8"):
	bs = s if type(s) is bytes else str(s).encode(encoding)
	ba = bytearray()
	offset = 0
	for b in bs:
		if b in [ 0xC2, 0xC3 ]: offset = b
		else:
			if offset == 0xC2:
				if b == 0xA0: offset = -0#x80
				else: offset = 0
			elif offset == 0xC3: offset = 0x40
			b += offset
			ba.append(b)
			offset = 0
	bs = bytes(ba)
	bs = bs if type(s) is bytes else bs.decode(encoding)
	return bs

def check_encoding(bs, filename="tools.tmp", error=True):
	try:
		bs = bs if type(bs) is bytes else str(bs).encode()
		stdout = os.dup(1)
		wo = open(filename, "wb")
		os.dup2(wo.fileno(), 1)
		print(bs)
		os.dup2(stdout, 1)
		wo.close()
		return True
	except:
		if error: raise
		else: return False

def normalize(s, encoding="utf-8", replace=b'_', isfile=False):
	bs = s if type(s) is bytes else str(s).encode(encoding)
	replace = replace if type(replace) is bytes else str(replace).encode("ascii")
	if len(replace) == 0: replace = b'_'

	if not check_encoding(bs, error=False):
		ba = bytearray()
		for b in bs: ba.append(ord(replace) if b > 127 else b)
		bs = bytes(ba)

	if isfile:
		for c in "\\/:*?\"<>|":
			bs = bs.replace(c.encode("ascii"), replace)

	if type(s) is bytes: s = bs
	elif type(s) is str: s = bs.decode(encoding)
	return s