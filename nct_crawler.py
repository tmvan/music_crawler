# -*- encoding: utf-8 -*-
from pack import *
from urllib.request import quote
import re
import json
import uuid


HOMEPAGE = "http://www.nhaccuatui.com"
TOTAL_PLAY_API = "http://www.nhaccuatui.com/interaction/api/v2/hit-counter"
RE_URL_ARTIST = re.compile("^[^/]+//[^/]+/nghe-si-[^/]+/?$", re.IGNORECASE)
RE_URL_SONG = re.compile("^[^/]+//[^/]+/bai-hat/[^/\.]+\.\w+\.html$", re.IGNORECASE)
RE_VALID_URL = re.compile("^http\\://(www\\.)?nhaccuatui\\.com/.*\\.html$", re.IGNORECASE)
RE_SONG_ID_EXTRACT = re.compile("\\.([a-z0-9]+)\\.html$", re.IGNORECASE)
RE_HIT_COUNTER = re.compile(\
    "NCTWidget\\.hitCounter\\([\\s\\\'\\\"]*(\\d+)[\\s\\\'\\\"]*," + \
    "[\\s\\\'\\\"]*(\\d+)[\\s\\\'\\\"]*,[\\s\\\'\\\"]*(\\w+)[\\s\\\'\\\"]*," + \
    "[^\\)]*\\)", re.IGNORECASE)


def start_crawl(deep=3):
    crawl = [(HOMEPAGE, 0)]
    crawled = []
    artists = []
    songs = []
    genres = []

    count = 1
    while crawl:
        try:
            node = crawl.pop()
            count -= 1
            url = node[0]
            node_deep = node[1]

            if node_deep > deep:
                crawled.append(url)
                continue

            if url in crawled:
                continue

            crawled.append(url)
            soup = get_soup(url)

            if node_deep > 0:
                remove_divs = [soup.find("div", attrs={"id": "header"}),\
                               soup.find("div", attrs={"id": "submenu"}),\
                               soup.find("div", class_="footer"),\
                               soup.find("div", class_="cfooter")]
                for remove_div in remove_divs:
                    if remove_div:
                        remove_div.extract()

            if soup:
                s = "\n%s|%s %s: " % (count, node_deep, url)
                print(s, end="")
                if RE_URL_ARTIST.match(url):
                    artist_left_avatar = soup.find("div", class_="singer-left-avatar")
                    artist_name = artist_left_avatar.h1.getText()
                    artist_id = url
                    artists.append((artist_id, artist_name))
                elif RE_URL_SONG.match(url):
                    detail_info = soup.find("div", class_="detail_info_playing_now")
                    bold_string = soup.find_all("b")
                    # get id and title of song
                    song_id = RE_SONG_ID_EXTRACT.search(url).group(1)
                    song_title = bold_string[0].getText()
                    print("add song", song_title, end=", ")
                    # get name of artist
                    song_artists = []
                    artist_links = bold_string[1].find_all("a")
                    for artist_link in artist_links:
                        artist_name = artist_link.getText()
                        artist_id = next((artist[0] for artist in artists \
                                          if artist[1] == artist_name), None)
                        if not artist_id:
                            print("add artist", artist_name, end=", ")
                            href = quote(artist_link["href"], safe=":/")
                            if RE_URL_ARTIST.match(href):
                                artist_id = href
                            else:
                                artist_id = uuid.uuid1()
                            artists.append((artist_id, artist_name))
                        song_artists.append(artist_id)
                    # get genre of song
                    song_genres = []
                    genre_links = bold_string[2].find_all("a")
                    for genre_link in genre_links:
                        genre_name = genre_link.getText()
                        genre_id = next((genre[0] for genre in genres \
                                         if genre[1] == genre_name),\
                                        None)
                        if not genre_id:
                            print("add genre", genre_name, end=", ")
                            href = genre_link["href"]
                            genre_id = href
                            genres.append((genre_id, genre_name))
                        song_genres.append(genre_id)
                    # get total play
                    total = 0
                    for script in soup.find_all("script"):
                        html = str(script)
                        found = RE_HIT_COUNTER.search(html)
                        if found:
                            item_id = found.group(1)
                            time = found.group(2)
                            sign = found.group(3)
                            form_data = "item_id=%s&time=%s&sign=%s&type=song" % \
                                        (item_id, time, sign)
                            form_bytes = str.encode(form_data)
                            b = urlopen(TOTAL_PLAY_API, data=form_bytes).read()
                            j = json.loads(b.decode("utf-8"))
                            total = j["data"]["counter"]
                            break
                    # append song into list of songs
                    songs.append((song_id, song_title, total, \
                                  ";".join(str(x) for x in song_artists), \
                                  ";".join(str(x) for x in song_genres)))

                if node_deep < deep:
                    links = get_all_link(soup=soup, check=lambda x: \
                        RE_VALID_URL.match(x))
                    for link in links:
                        quote_link = quote(string=link, safe=":/")
                        if all(item[0] != quote_link for item in crawl) and \
                           quote_link not in crawled:
                            crawl.append((quote_link, node_deep + 1))
                            count += 1
        except Exception as e:
            print(e)
            pass
    return songs, artists, genres

if __name__ == "__main__":
    songs, artists, genres = start_crawl()
    now = get_now("%Y-%m-%d")
    write_csv("[nct][%s] songs" % now, songs, \
              ["Id", "Title", "Total play", "Artists", "Genres"])
    write_csv("[nct][%s] artists" % now, artists, \
              ["Id", "Name"])
    write_csv("[nct][%s] genres" % now, genres, \
              ["Id", "Name"])

