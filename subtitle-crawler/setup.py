# -*- coding: utf-8 -*-

import sys
from cx_Freeze import setup, Executable

executables = [ Executable("crawl-start.py") ]
options = {
	"build_exe": {
		"packages": [ "lxml._elementpath" ]
	}
}

setup(
	name="subtitle-crawler",
	version="0.1",
	description="Crawl subtitles from NAVER, EGLOOS, TISTORY and XE",
	author="made by R",
	executables=executables,
	options=options
)
#setup(executables=[ Executable("test.py") ])