# -*- coding: utf-8 -*-

import os, sys
import re
import json
import requests as rq
from urllib.parse import urlparse, urlunparse, urlsplit, urlunsplit, parse_qs, unquote, unquote_to_bytes
from lxml import etree
etree.namespaces = dict(re="http://exslt.org/regular-expressions")

class objdict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getattr__(self, key):
        return self[key] if key in self.keys() else None

    def __setattr__(self, key, value):
        self[key] = value

    def __str__(self):
        return "<objdict {}>".format(super().__str__())

URL_FORMAT1 = "http://www.anissia.net/anitime/list?w={}"
URL_FORMAT2 = "http://www.anissia.net/anitime/cap?i={}"
DAYS_OF_THE_WEEK = [ "[{}]".format(x) for x in [ "일", "월", "화", "수", "목", "금", "토" ] ]

def get_dotw(i, retry=False):
    try:
        rs = rq.get(URL_FORMAT1.format(i % 7), timeout=5)
        for x in json.loads(rs.text) if rs.ok else []:
            yield objdict(x)
    except Exception as e:
        if retry:
            raise e
        else:
            yield from get_dotw(i, retry=True)

def get_week():
    for i in range(7):
        yield i, get_dotw(i)

def get_subtitles(i, retry=False):
    try:
        rs = rq.get(URL_FORMAT2.format(i), timeout=5)
        for x in json.loads(rs.text) if rs.ok else []:
            yield objdict(x)
    except Exception as e:
        if retry:
            raise e
        else:
            yield from get_subtitles(i, retry=True)

def sort_subtitles(data, rank=1):
    ordered = []
    for x in data:
        if len(ordered) == 0:
            ordered.append(x)
        else:
            for i in range(len(ordered)):
                y = ordered[i]
                if any([ x.s > y.s, x.s == y.s and FIRST_DATE < x.d < y.d ]):
                    ordered.insert(i, x)
                    break
            if x not in ordered:
                ordered.append(x)
    return ordered[:rank] if rank < len(ordered) else ordered

def main(argc, args):
    for dotw, data in get_week():
        print(DAYS_OF_THE_WEEK[dotw], "({})".format(URL_FORMAT1.format(dotw)))
        print()
        print()
        for x in data:
            if not x.l.startswith("http"):
                x.l = "://".join([ "http", x.l ])
            try: print("- {} ({}) <w = {}, i = {}>".format(x.s, x.l, dotw, x.i))
            except:
                try: print("- {} ({}) <w = {}, i = {}>".format(x.s.encode("raw_unicode_escape").decode(), x.l, dotw, x.i))
                except: print("- {} ({}) <w = {}, i = {}>".format(x.s.encode(), x.l, dotw, x.i))

            for y in get_subtitles(x.i):
                if not y.a.startswith("http"):
                    y.a = "://".join([ "http", y.a ])
                print("    => {} ({}) <s = {}, d = {}>".format(y.n, y.a, y.s, y.d))
            print()
        print()

    return




    q = 0
    qq = 50
    category_list = []
    for weekday, data in get_week():
        print(WEEKDAY[weekday])
        for x in data:
            if not x.l.startswith("http"):
                x.l = "://".join([ "http", x.l ])
            try: print("- {} ({}) <w = {}, i = {}>".format(x.s, x.l, weekday, x.i))
            except:
                try: print("- {} ({}) <w = {}, i = {}>".format(x.s.encode("raw_unicode_escape").decode(), x.l, weekday, x.i))
                except: print("- {} ({}) <w = {}, i = {}>".format(x.s.encode(), x.l, weekday, x.i))

            ranked = sort_subtitles(get_subtitles(x.i), rank=3)
            print("  > {} categor{}.".format(len(ranked), 'ies' if len(ranked) > 1 else 'y'))

            for y in ranked:
                if not y.a.startswith("http"):
                    y.a = "://".join([ "http", y.a ])
                print("    => {} ({})".format(y.n, y.a))
                y.t = x.s
                categories = get_category(y)
                if categories is None:
                    print("      >> Invalid URL.")
                else:
                    categories = [ dict(w) for w in set([ tuple(z.items()) for z in categories ]) ]

                    print("      >> {} candidate{}.".format(len(categories), 's' if len(categories) > 1 else ''))
                    i = 1
                    for z in categories:
                        try: print("        ==>> {}. {}".format(i, dict(z)))
                        except:
                            try: print("        ==>> {}. {}".format(i, str(dict(z)).encode("raw_unicode_escape").decode()))
                            except: print("        ==>> {}. {}".format(i, str(dict(z)).encode()))
                        i += 1
                    category_list.extend(categories)
    save_to_file(category_list)

if __name__ == "__main__":
    main(len(sys.argv), sys.argv)