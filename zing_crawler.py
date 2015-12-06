# -*- encoding: utf-8 -*-
from pack import *
from urllib.request import quote
import re
import json
import uuid

HOMEPAGE = "http://mp3.zing.vn"
TOTAL_PLAY_API = "http://mp3.zing.vn/xhr/song/get-total-play?id={}&type=song"
RE_URL_ARTIST = re.compile("^[^/]+//[^/]+/nghe-si/[^/]+/?$", re.IGNORECASE)
RE_URL_SONG = re.compile("^[^/]+//[^/]+/bai-hat/.*$", re.IGNORECASE)
RE_EXTRACT_GENRE_ID = re.compile(\
    "^[^/]*//[^/]*/the-loai-bai-hat/[^/]*/([^/.]*)\\.html$", re.IGNORECASE)
RE_VALID_URL = re.compile("^http\\://mp3\\.zing\\.vn/.*\\.html$", re.IGNORECASE)

def start_crawl(deep=3):
    crawl = [(HOMEPAGE, 0)]
    crawled = []
    artists = []
    songs = []
    genres = []
    
    def artist_inner_crawl(inner_url='', inner_soup=None):
        if not inner_soup:
            inner_soup = get_soup(inner_url, gz=True)
            crawled.append(inner_url)
        if inner_soup:
            follow = inner_soup.find("a", class_="fn-follow")
            data_id = follow["data-id"]
            data_name = follow["data-name"]
            print("add artist", data_name, end=", ")
            artist = data_id, data_name
            artists.append(artist)
            return artist
        else:
            return None

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
            soup = get_soup(url, True)
            
            if soup.header: soup.header.extract()
            if soup.footer: soup.footer.extract()
            if node_deep > 0: soup.nav.extract()
            
            if soup:
                s = "\n%s|%s %s: " % (count, node_deep, url)
                print(s, end="")
                if RE_URL_ARTIST.match(url):
                    artist_inner_crawl(inner_url=url)
                elif RE_URL_SONG.match(url):
                    like = soup.find("div", class_="zlike fn-zlike")
                    info = soup.find("div", class_="info-content")
                    # get id and title of song
                    song_id = like["data-id"]
                    song_title = info.h1.getText()
                    print("add song", song_title, end=", ")
                    # get name of artist
                    song_artists = []
                    artist_links = info.select("span.zadash + div.inline a")
                    for artist_link in artist_links:
                        title = artist_link["title"]
                        artist_id = next((artist[0] for artist in artists \
                                          if artist[1] == title), None)
                        if not artist_id:
                            artist = artist_inner_crawl(inner_url=artist_link["href"])
                            if not artist:
                                artist_name = title
                                artist_id = uuid.uuid1()
                                print("add unknown artist", artist_name, end=", ")
                                artists.append((artist_id, artist_name))
                            else:
                                artist_id = artist[0]
                        song_artists.append(artist_id)
                    # get genre of song
                    song_genres = []
                    genre_links = info.select("div.info-song-top")
                    if len(genre_links) > 1:
                        genre_links = genre_links[-1].select("a")
                        for genre_link in genre_links:
                            genre_name = genre_link.getText()
                            genre_id = next((genre[0] for genre in genres \
                                             if genre[1] == genre_name),\
                                None)
                            if not genre_id:
                                print("add genre", genre_name, end=", ")
                                href = genre_link["href"]
                                search = RE_EXTRACT_GENRE_ID.search(href)
                                genre_id = search.group(1)
                                genres.append((genre_id, genre_name))
                            song_genres.append(genre_id)
                    # get total play
                    api_url = TOTAL_PLAY_API.format(song_id)
                    b = get_html(api_url)
                    j = json.loads(b.decode("utf-8"))
                    total = j["total_play"]
                    # append song into list of songs
                    songs.append((song_id, song_title, total, \
                                  ";".join(str(x) for x in song_artists), \
                                  ";".join(str(x) for x in song_genres)))
                    
                if node_deep < deep:
                    links = get_all_link(soup=soup, gz=True,\
                                         check=lambda x: RE_VALID_URL.match(x))
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
    write_csv("[zing][%s] songs" % now, songs, \
              ["Id", "Title", "Total play", "Artists", "Genres"])
    write_csv("[zing][%s] artists" % now, artists, \
              ["Id", "Name"])
    write_csv("[zing][%s] genres" % now, genres, \
              ["Id", "Name"])
