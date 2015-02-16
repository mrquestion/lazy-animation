# -*- coding: utf-8 -*-

import os, sys
import re
import json
import requests as rq
from urllib.parse import urlparse, urlunparse, urlsplit, urlunsplit, parse_qs, unquote, unquote_to_bytes
from lxml import etree
etree.namespaces = dict(re="http://exslt.org/regular-expressions")

import pprint, inspect
def pp(o): pprint.pprint(o, indent=4)
def ppmems(o): pp(inspect.getmembers(o))

URL_FORMAT1 = "http://www.anissia.net/anitime/list?w={}"
URL_FORMAT2 = "http://www.anissia.net/anitime/cap?i={}"
FIRST_DATE = "20141001000000"
LAST_DATE = "20141231235959"
WEEKDAY = [ "[{}]".format(x) for x in [ "일", "월", "화", "수", "목", "금", "토" ] ]

class objdict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getattr__(self, key):
        return self[key] if key in self.keys() else None

    def __setattr__(self, key, value):
        self[key] = value

    def __str__(self):
        return "<objdict {}>".format(super().__str__())

''' Longest common subsequence
    Referenced from:
        http://rosettacode.org/wiki/Longest_common_subsequence#Dynamic_Programming_7
'''
def lcs(a, b):
    lengths = [[0 for j in range(len(b)+1)] for i in range(len(a)+1)]
    # row 0 and column 0 are initialized to 0 already
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            if x == y:
                lengths[i+1][j+1] = lengths[i][j] + 1
            else:
                lengths[i+1][j+1] = \
                    max(lengths[i+1][j], lengths[i][j+1])
    # read the substring out from the matrix
    result = ""
    x, y = len(a), len(b)
    while x != 0 and y != 0:
        if lengths[x][y] == lengths[x-1][y]:
            x -= 1
        elif lengths[x][y] == lengths[x][y-1]:
            y -= 1
        else:
            assert a[x-1] == b[y-1]
            result = a[x-1] + result
            x -= 1
            y -= 1
    return result

def get_weekday(i, retry=False):
    try:
        rs = rq.get(URL_FORMAT1.format(i % 7), timeout=5)
        for x in json.loads(rs.text) if rs.ok else []:
            yield objdict(x)
    except Exception as e:
        if retry:
            raise e
        else:
            yield from get_weekday(i, retry=True)

def get_week():
    for i in range(7):
        yield i, get_weekday(i)

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
    '''
    for j in range(len(data)):
        for i in range(len(data)-1):
            x, y = data[i], data[i+1]
            if any([ x.s > y.s, x.s == y.s and FIRST_DATE < x.d < y.d ]):
                data[i], data[i+1] = data[i+1], data[i]
    return data
    '''

def get_category(data):
    url = data.a
    print(url)

    category = None
    parsed = urlparse(url)
    if re.match(r"blog\.naver\.com", parsed.netloc):
        category = from_naver(url)
    elif re.match(r"[^.]+\.egloos\.com", parsed.netloc):
        category = from_egloos(url)
    elif re.match(r"[^.]+\.tistory\.com", parsed.netloc):
        category = from_tistory(url, data.t)
    else:
        data.a = trace_url(url)
        if data.a is not None:
            category = get_category(data)

    return category

def trace_url(url):
    rs = rq.get(url, timeout=3)
    root = etree.HTML(rs.content if rs.ok else "<error/>")
    naver = root.xpath('//frame[@id="screenFrame" and @src]')
    if len(naver) > 0:
        parsed = urlparse(naver[0].get("src"))
        a, b, c, d, e, f = parsed
        if len(parsed.scheme) == 0 and len(parsed.netloc) == 0:
            parsed = urlparse(url)
            a, b, c, d, e, f = parsed
            c = naver[0].get("src")
        return urlunparse([ a, b, c, d, e, f ])
    if b"user.tistory.com":
        scripts = root.xpath('//script[re:test(text(),".*user\.tistory\.com.*")]', namespaces=etree.namespaces)
        for x in scripts:
            for m in re.finditer(r'\s+__pageTracker\.__addParam\("([^"]+)".*,.*"([^"]+)"\);.*', x.text):
                k, v = m.groups()
                if k == "author":
                    return "http://{}.tistory.com".format(v)

def from_naver(url):
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if re.match(r"^/PostList.nhn\??(blogId|categoryNo)*", parsed.path):
        print(parsed)
    elif parsed.path == "/PostView.nhn" and "logNo" in qs.keys():
        rs = rq.get(url, timeout=3)
        root = etree.HTML(rs.content if rs.ok else "<error/>")
        pcol2s = root.xpath('//div[@id="title_1"]//a[re:test(@href,".*/PostList\.nhn??.*(blogId=[^&]*|categoryNo=[^&]*).*")]', namespaces=etree.namespaces)
        for x in pcol2s:
            parsed = urlparse(x.get("href"))
            a, b, c, d, e, f = parsed
            qs = parse_qs(e)
            e = '&'.join('&'.join("{}={}".format(k, v2) for v2 in v1) for k, v1 in sorted(qs.items()) if k in [ "blogId", "categoryNo" ])
            if len(parsed.scheme) == 0 and len(parsed.netloc) == 0:
                parsed = urlparse(url)
                a, b = parsed.scheme, parsed.netloc
                c = unquote(c)
                x.text = x.text.encode("raw_unicode_escape").decode("cp949")
            yield objdict(NAVER=urlunparse([ a, b, c, d, e, f ]), TEXT=x.text.strip())
    else:
        rs = rq.get(url, timeout=3)
        root = etree.HTML(rs.content if rs.ok else "<error/>")
        frame = root.xpath('//frame[@id="mainFrame" and @src]')
        if len(frame) > 0:
            parsed = urlparse(frame[0].get("src"))
            a, b, c, d, e, f = parsed
            if len(parsed.scheme) == 0 and len(parsed.netloc) == 0:
                parsed = urlparse(url)
                a, b, c, d, e, f = parsed
                c = frame[0].get("src")
            yield from from_naver(urlunparse([ a, b, c, d, e, f ]))

def from_egloos(url):
    parsed = urlparse(url)
    rs = rq.get(url, timeout=3)
    root = etree.HTML(rs.content if rs.ok else "<error/>")
    anchors = root.xpath('//div[@id="section_content"]//a[re:test(@href,"^/category/.+$") and text()]', namespaces=etree.namespaces)
    for x in anchors:
        parsed = urlparse(x.get("href"))
        a, b, c, d, e, f = parsed
        if len(parsed.scheme) == 0 and len(parsed.netloc) == 0:
            parsed = urlparse(url)
            a, b, c, d, e, f = parsed
            c = unquote(x.get("href"))
        yield objdict(TISTORY=urlunparse([ a, b, c, d, e, f ]), TEXT=x.text.strip())

# TODO: *.tistory.com/m/post/*
def from_tistory(url, title):
    parsed = urlparse(url)
    path = parsed.path

    rs = rq.get(url, timeout=3)
    root = etree.HTML(rs.content if rs.ok else "<error/>")
    anchors = root.xpath('//a[re:test(@href,"^/category/.+$") and text()]', namespaces=etree.namespaces)
    for x in anchors:
        if x.text is None:
            text = []
            for y in x.xpath('.//*'):
                y.text = y.text if y.text is not None else ''
                y.tail = y.tail if y.tail is not None else ''
                text.append(''.join([ y.text, y.tail ]))
            x.text = ''.join(text)
        if len(path) > 0 or len(lcs(x.text, title).strip()) > 1:
            parsed = urlparse(x.get("href"))
            a, b, c, d, e, f = parsed
            if len(parsed.scheme) == 0 and len(parsed.netloc) == 0:
                parsed = urlparse(url)
                a, b, c, d, e, f = parsed
                c = unquote(x.get("href"))
            yield objdict(TISTORY=urlunparse([ a, b, c, d, e, f ]), TEXT=x.text.strip())

def main(argc, args):
    q = 0
    qq = 19
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
                categories = [ dict(w) for w in set([ tuple(z.items()) for z in get_category(y) ]) ]

                print("      >> {} candidate{}.".format(len(categories), 's' if len(categories) > 1 else ''))
                i = 1
                for z in categories:
                    try: print("        ==>> {}. {}".format(i, dict(z)))
                    except:
                        try: print("        ==>> {}. {}".format(i, str(dict(z)).encode("raw_unicode_escape").decode()))
                        except: print("        ==>> {}. {}".format(i, str(dict(z)).encode()))
                    i += 1
                if q == qq: return
                q += 1

if __name__ == "__main__":
    main(len(sys.argv), sys.argv)

exit()

import os, sys
import time, datetime
import re
import json
import random
import socket
from urllib.parse import urlparse as parse_url, parse_qs
import requests as rq
from bs4 import BeautifulSoup as bs
import lxml
from lxml import etree
from urllib.parse import urlparse, urlunparse, parse_qs as qsparse, urlencode, quote, unquote, quote_from_bytes, unquote_to_bytes
from collections import Counter

from email.parser import Parser
from http.client import HTTPConnection, HTTPMessage
from requests.adapters import HTTPAdapter
from requests.structures import CaseInsensitiveDict
from requests.packages.urllib3.response import HTTPResponse

import inspect
import pprint
def pp(o): pprint.PrettyPrinter(indent=4).pprint(o)

BASE_URL1 = "http://www.anissia.net/anitime/list?w={}"
BASE_URL2 = "http://www.anissia.net/anitime/cap?i={}"
FIRST_DATE = "20141001000000"
LAST_DATE = "20141231235959"
WEEKDAY = { 0: "[일]", 1: "[월]", 2: "[화]", 3: "[수]", 4: "[목]", 5: "[금]", 6: "[토]" }

def convert(s, encoding="utf-8"):
    bs = s if type(s) is bytes else str(s).encode(encoding)
    ba = bytearray()
    p = 0x00
    for b in bs:
        if b in [ 0xC2, 0xC3 ]: p = b
        else:
            if p == 0xC2:
                if b == 0xA0: b -= 0x80
            elif p == 0xC3: b += 0x40
            ba.append(b)
            p = 0
    bs = bytes(ba)
    bs = bs if type(s) is bytes else bs.decode(encoding)
    return bs

def get_weekday(min=0, max=7):
    for i in range(min, max):
        yield { "WEEKDAY": WEEKDAY[i] }
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
        elif s == episode and FIRST_DATE < d < fastest: fastest, url = d, a
        if fastest == LAST_DATE: fastest = None
    return episode, fastest, url

def naver_prepare(url):
    m = re.match(r"(?P<fixed>.*blog\.naver\.com/[^/]+/[0-9]+).*", url)
    url = m.groupdict()["fixed"] if m else url
    if not url.startswith("http://"): url = "http://{}".format(url)
    rs = rq.get(url)
    dom = bs(rs.content) if rs.ok else None
    if dom:
        mainFrame = dom.find("frame", id="mainFrame")
        p = urlparse(url)
        url = urlunparse([ p.scheme, p.netloc, mainFrame["src"], p.params, p.query, p.fragment ])
        return url



class HTTPSocketClient:
    def get(self, url, cookies=None, verbose=False):
        parsed = parse_url(url)
        host = parsed.hostname
        port = parsed.port if parsed.port else 80
        uri = "{}{}".format(parsed.path, "?{}".format(parsed.query) if parsed.query else '')

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        client.settimeout(5)
        client.connect((host, port))

        request = self.make_request(host, uri=uri, cookies=cookies)
        #client.send(request.encode())
        self.send_random(client, request.encode())

        data = self.get_data(client, verbose=verbose)

        client.close()

        return data

    def make_request(self, host, uri=None, cookies=None, body=None):
        uri = uri if uri else '/'
        uri = uri if uri.startswith('/') else "/{}".format(uri)
        request = [ "GET {} HTTP/1.1".format(uri) ]
        request.append("Host: {}".format(host))
        request.append("User-Agent: Python Socket")
        if type(cookies) is dict:
            request.append("Cookie: {}".format("; ".join("{}={}".format(key, value) for key, value in cookies.items())))
        request.append('')
        request.append(body if body else '')
        return "\r\n".join(request)

    def send_random(self, client, data):
        index = 0
        while index < len(data):
            length = int(random.random() * 0x10) + 0x10
            client.send(data[index:index+length] if index+length < len(data) else data[index:])
            index += length
            time.sleep(random.random())

    def get_data(self, client, size=4096, verbose=False):
        def recv(client, size):
            while True:
                data = client.recv(size)
                if len(data) <= 0: break
                yield data

        response = bytearray()
        headers = None
        token = b"\r\n\r\n"
        total = length = 0
        for data in recv(client, size):
            response.extend(data)
            if headers:
                if length:
                    total += len(data)
                    if verbose: print(self.make_progress(total, length))
                    if total >= length: break
            elif token in response:
                headers, response = self.split_token(response, token)
                response = bytearray(response)
                total = len(response)
                token = b"\r\n"
                http, headers = self.split_token(headers, token)
                headers = CaseInsensitiveDict(Parser(_class=HTTPMessage).parsestr(headers.decode()))
                length = int(headers["Content-Length"]) if "Content-Length" in headers else length

        if "Transfer-Encoding" in headers and headers["Transfer-Encoding"] == "chunked":
            token = b"\r\n"
            ba = bytearray()
            while len(response) > 0:
                length, response = self.split_token(response, token)
                ba.extend(response[:int(length, 16)])
                response = response[int(length, 16)+len(token):]
            response = ba

        return headers, bytes(response)

    def parse_filename(self, url, headers):
        if "Content-Disposition" in headers:
            m = re.match(r".*filename=['\"]?([^'\"]+)['\"]?", headers["Content-Disposition"])
            return m.group(1) if m else None
        else:
            m = re.match(r".*/([^/]+)\.([^/]+)", parse_url(url).path)
            filename = "{}.{}".format(m.group(1), m.group(2)) if m else None
            #filename = parse_url(url).path.split('/')[-1]
            #filename = filename if len(filename.strip()) > 0 else None
            return filename

    def split_token(self, s, t):
        array = s.split(t)
        return array[0], t.join(array[1:]) if len(array) > 1 else None

def get(url, method):
    if re.match(r"^REQUEST$", method, re.I):
        pass
    else:
        http = HTTPSocketClient()
        headers, content = http.get(url)
        filename = http.parse_filename(url, headers)
        return headers, content, filename


def naver(url):
    if not url.startswith("http://"): url = "http://{}".format(url)
    rs = rq.get(url)
    dom = bs(rs.text) if rs.ok else None
    if dom:
        p = urlparse(url)
        title_1 = dom.find("div", id="title_1")
        if title_1:
            cate = title_1.find("span", class_=[ "cate", "pcol2" ])
            pcol2s = cate.find_all("a", class_="pcol2", href=True)
            for pcol2 in pcol2s:
                path = urlparse(pcol2["href"]).path
                qs = qsparse(urlparse(pcol2["href"]).query)
                if "blogId" in qs and "categoryNo" in qs:
                    queries = []
                    for key in [ "blogId", "categoryNo" ]:
                        queries += [ '='.join([ key, value ]) for value in qs[key] ]
                    qs = '&'.join(queries)
                    url = urlunparse([ p.scheme, p.netloc, path, p.params, qs, p.fragment ])

                    rs = rq.get(url)
                    dom = bs(rs.content) if rs.ok else None
                    category_name = dom.find("div", id="category-name")
                    if category_name:
                        postlisttitle = category_name.find("div", class_="postlisttitle")
                        toplistSpanBlind = postlisttitle.find("span", id="toplistSpanBlind")
                        title = toplistSpanBlind.previousSibling.strip()
                        yield url, convert(title.encode()).decode("cp949")

def naver_check(url):
    if not url.startswith("http://"): url = "http://{}".format(url)
    rs = rq.get(url)
    dom = bs(rs.content) if rs.ok else None
    if dom:
        screenFrame = dom.find("frame", id="screenFrame")
        if screenFrame: return naver_prepare(screenFrame["src"])

def egloos(url):
    if not url.startswith("http://"): url = "http://{}".format(url)
    rs = rq.get(url)
    dom = bs(rs.content) if rs.ok else None
    if dom:
        p = urlparse(url)
        anchors = dom.find_all("a", href=re.compile(r"^/category/.*"))
        hrefs = [ href for href, count in Counter([ anchor["href"] for anchor in anchors ]).most_common(3) ]
        for href in hrefs:
            path = urlparse(href).path
            url = urlunparse([ p.scheme, p.netloc, path, p.params, p.query, p.fragment ])
            yield unquote(url)

def tistory(url):
    if not url.startswith("http://"): url = "http://{}".format(url)
    rs = rq.get(url)
    content = rs.content if rs.ok else b""
    start = content.index(b"<html")
    start = content.index(b"<!doctype") if start < 0 else start
    start = content.index(b"<!DOCTYPE") if start < 0 else start
    content = content[start:]
    #dom = bs(rs.content) if rs.ok else None
    dom = bs(content) if rs.ok else None
    if dom:
        p = urlparse(url)
        if "fuko" in url: open("test.txt", "w").write(dom.prettify())
        anchors = dom.find_all("a", href=re.compile(r"^/category/.*"))
        hrefs = [ href for href, count in Counter([ anchor["href"] for anchor in anchors ]).most_common(3) ]
        for href in hrefs:
            path = urlparse(href).path
            url = urlunparse([ p.scheme, p.netloc, path, p.params, p.query, p.fragment ])
            yield unquote(url)

# TODO: http://*/xe
def xe(url):
    pass

def timestamp(format="%Y%m%d-%H%M%S"):
    return datetime.datetime.fromtimestamp(time.time()).strftime(format)

def save(titles, categories, filename="{}.json".format(timestamp()), encoding="utf-8"):
    content = [ '[', os.linesep, os.linesep ]
    first = True
    for category in categories:
        if first: first = False
        else:
            content.append(',')
            content.append(os.linesep)
        line = ", ".join('"{}": "{}"'.format(key, value) for key, value in category.items())
        content.append("{{ {} }}".format(line))
    content.extend([ os.linesep, os.linesep, ']' ])
    with open(filename, "wb") as wbo:
        wbo.write(''.join(content).encode())

# TODO: consider presented url is not posting url, just default blog url
# just find all anchor tags for candidate
def main(argc, args):
    sc = []
    for data in get_weekday(min=0, max=7):
        if "WEEKDAY" in data: print(data["WEEKDAY"])
        else:
            datas = [ data for data in get_subtitle(data) ]
            if not datas: continue

            title, (episode, fastest, url) = data["s"], get_fastest(datas)
            try: print("- {} ({}) E{} / {}".format(title, url, episode, fastest))
            except: print("- {} ({}) E{} / {}".format(title.encode(), url, episode, fastest))
            if not url: continue

            result = None
            if re.match(r"^blog\.naver\.com/.*", url):
                if not re.match(r"^blog\.naver\.com/PostView\.nhn.*", url): url = naver_prepare(url)
                if url: result = [ dict(NAME=title, NAVER=x, TEST=y) for x, y in naver(url) ]
                else: raise ValueError(title)
            elif re.match(r"^[^.]+\.blog\.me/.*", url):
                url = naver_check(url)
                if url: result = [ dict(NAME=title, NAVER=x, TEST=y) for x, y in naver(url) ]
                else: raise ValueError(title)
            elif re.match(r"^[^.]+\.egloos\.com/.*", url):
                result = [ dict(NAME=title, EGLOOS=x) for x in egloos(url) ]
            elif re.match(r"^[^.]+\.tistory\.com/.*", url):
                result = [ dict(NAME=title, TISTORY=x) for x in tistory(url) ]
            elif re.match(r"^[^/]+/xe/.*", url):
                pass
            else:
                checked = naver_check(url)
                if checked: result = [ dict(NAME=title, NAVER=x, TEST=y) for x, y in naver(checked) ]

            if result:
                sc.extend(result)
                print("  > {} candidate{}.".format(len(result), 's' if len(result) > 1 else ''))
                for i in range(0, len(result)):
                    try: print("    => {}. {}".format(i+1, result[i]))
                    except: print("    => {}. {}".format(i+1, str(result[i]).encode()))
            else:
                sc.append(dict(NAME=title, NOT_SUPPORTED=url))
                print("  > Error: not supported url.")
    save(None, sc)
    #pp(sc)
    #print(json.dumps(json.loads(str(sc).replace("'", '"')), indent=4))

if __name__ == "__main__":
    #url = "http://walnutnseed.tistory.com/category/%EC%95%A0%EB%8B%88%EC%9E%90%EB%A7%89/%EB%A0%88%EC%9D%BC%20%EC%9B%8C%EC%A6%88!"
    #print(unquote(url))
    #exit()
    main(len(sys.argv), sys.argv)