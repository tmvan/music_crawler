# -*- encoding: utf-8 -*-

from urllib.request import urlopen
from bs4 import BeautifulSoup
import io
import gzip
import datetime

def get_html(url, gz=False):
    try:
        response = urlopen(url=url)
        if gz:
            buffer = io.BytesIO()
            buffer.write(response.read())
            buffer.seek(0)
            decompressed = gzip.GzipFile(fileobj=buffer, mode="rb")
            return decompressed.read()
        else:
            return response.read()
    except OSError:
        return None


def get_soup(url, gz=False):
    html = get_html(url, gz)
    if html:
        return BeautifulSoup(html, "html.parser")
    else:
        return None


def get_all_link(url='', soup=None, gz=False, check=lambda x: True):
    if not soup:
        soup = get_soup(url, gz)
    items = soup.find_all("a", attrs={"href": True})
    for item in items:
        href = item["href"]
        if check(href):
            yield href

def get_now(strftime="%Y-%m-%d %H:%M:%S"):
    now = datetime.datetime.now()
    return now.strftime(strftime)

def write_csv(name, list):
    with open(name + ".csv", mode="w+", encoding="utf-8") as f:
        for row in list:
            s = ",".join(str(x) for x in row) + "\n"
            f.write(s)
