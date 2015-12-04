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
RE_EXTRACT_GENRE_ID = re.compile("^[^/]*//[^/]*/the-loai-bai-hat/[^/]*/([^/.]*).html", re.IGNORECASE)

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
            artist = data_id, data_name
            artists.append(artist)
            return artist
        else:
            return None

    count = 1
    while crawl:
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
        
        try:
            if soup.header: soup.header.extract()
            if soup.footer: soup.footer.extract()
            if node_deep > 0:
                soup.nav.extract()
        except AttributeError:
            pass
        
        if soup:
            print(count, url)
            if RE_URL_ARTIST.match(url):
                artist_inner_crawl(inner_url=url)
            elif RE_URL_SONG.match(url):
                like = soup.find("div", class_="zlike fn-zlike")
                info = soup.find("div", class_="info-content")
                divs = info.find_all("div", recursive=False)
                count_divs = len(divs)
                # get id and title of song
                song_id = like["data-id"]
                song_title = info.h1.getText()
                # get name of artist
                song_artists = []
                div1st = divs[0]
                list_a = div1st.find_all("a", {"title": True, "href": True})
                for a in list_a:
                    title = a["title"]
                    artist_id = next((artist[0] for artist in artists if artist[1] == title), None)
                    if not artist_id:
                        artist = artist_inner_crawl(inner_url=a["href"])
                        if not artist:
                            artist_name = title
                            artist_id = uuid.uuid1()
                            artists.append((artist_id, artist_name))
                        else:
                            artist_id = artist[0]
                    song_artists.append(artist_id)
                # get genre of song
                song_genres = []
                if count_divs > 2:
                    div3rd = divs[2]
                    list_a = div3rd.find_all("a", {"title": True, "href": True})
                    for a in list_a:
                        genre_name = a.getText()
                        genre_id = next((genre[0] for genre in genres if genre[1] == genre_name), None)
                        if not genre_id:
                            href = a["href"]
                            search = RE_EXTRACT_GENRE_ID.search(href)
                            genre_id = search.group(1)
                            genres.append((genre_id, genre_name))
                        song_genres.append(genre_id)
                # get total play
                api_url = TOTAL_PLAY_API.format(song_id)
                bytes = get_html(api_url)
                j = json.loads(bytes.decode("utf-8"))
                total = j["total_play"]
                # append song into list of songs
                songs.append((song_id, song_title, total, song_artists, song_genres, get_now()))
            if node_deep < deep:
                links = get_all_link(soup=soup, gz=True, check=lambda x: HOMEPAGE in x and "#" not in x and "?" not in x)
                for link in links:
                    quote_link = quote(string=link, safe=":/")
                    if all(item[0] != quote_link for item in crawl) and quote_link not in crawled:
                        crawl.append((quote_link, node_deep + 1))
                        count += 1
    return songs, artists, genres


if __name__ == "__main__":
    songs, artists, genres = start_crawl()
    now = get_now("%Y-%m-%d %H.%M")
    write_csv("[%s] songs" % now, songs)
    write_csv("[%s] artists" % now, artists)
    write_csv("[%s] genres" % now, genres)
