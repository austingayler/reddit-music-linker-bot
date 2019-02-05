import praw
import spotipy
import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import argparse
import json
import isodate
from selenium import webdriver
import requests
import bs4
import ConfigParser
import dataset
import sqlalchemy

sc_url = "https://soundcloud.com"

def init_services():
    services = {}

    config = ConfigParser.ConfigParser()
    config.read("./env.ini")

    db = dataset.connect('sqlite:///bot.db')
    db.create_table('replied_to')
    db['replied_to'].create_column('post_id', sqlalchemy.String)

    reddit = praw.Reddit(user_agent='spotify to yt linkeroo',
                         client_id=config.get("reddit", "reddit_client"),
                         client_secret=config.get("reddit", "reddit_secret"),
                         username=config.get("reddit", "reddit_username"),
                         password=config.get("reddit", "reddit_password"))



    youtube = build(config.get("youtube", "yt_api_service_name"),
        config.get("youtube", "yt_api_version"),
        developerKey=config.get("youtube", "yt_key"))

    return db, reddit, youtube, config


def get_url_yt(artist, track_name):
    yt_search=youtube.search().list(
            q=artist + " " + track_name,
            part="id",
            maxResults=25
    ).execute()
    videos = []

    for search_result in yt_search.get('items', []):
        if search_result['id']['kind'] == 'youtube#video':
            videos.append(search_result['id']['videoId'])

    yt_search=youtube.videos().list(
        part="id,snippet,contentDetails",
        id=",".join(videos)
    ).execute()

    for search_result in yt_search.get('items', []):
        yt_duration=isodate.parse_duration(search_result['contentDetails']['duration']).total_seconds() * 1000
        sp_duration = sp_data['duration_ms']

        if abs(yt_duration - sp_duration) < 5000:
            return search_result


def get_url_sc(artist, track):
    service = webdriver.chrome.service.Service('./chromedriver')
    service.start()
    options = webdriver.ChromeOptions()
    options = options.to_capabilities()
    browser = webdriver.Remote(service.service_url, options)

    query = artist + " " + track
    url = sc_url + "/search?q=" + "%20".join(query.split(" "))
    source = browser.get(url)
    soup = bs4.BeautifulSoup(browser.page_source, "lxml")

    results = soup.select("a.soundTitle__title")
    track_links = []
    track_names = []
    potential = None

    # .waveform__layer > canvas.sceneLayer[2]
    for index, track in enumerate(results):
        if artist in track.text:
            potential = { 'link' : track.get("href"), 'name' : track.text.replace('\n', '') }

    return potential

def get_spotify_submissions(reddit):
    spotify_submissions = []

    for submission in reddit.subreddit('trap').hot(limit=50):
        if "open.spotify.com/track" not in submission.url:
            continue

        if db['replied_to'].find_one(post_id=submission.id):
            print("Already commented on " + submission.id + ", skipping")
            continue

        #print(submission.title)
        #print(submission.url)

        id_index = submission.url.find("track/") + 6
        track_id = submission.url[id_index:id_index+22]

        spotify_submissions.append({ 'track' : track_id, 'post' : submission })

    return spotify_submissions

def delete_bad_comments(reddit):
    comments = reddit.user.me().comments.new(limit=None)

    for comment in comments:
        if comment.score < 1:
            comment.delete()

def get_spotify_headers(config):
    headers = {
            'Authorization': 'Bearer '
    }

    sp_credential_data = {
      'grant_type': 'client_credentials',
      'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0',
    }

    credentials = requests.post('https://accounts.spotify.com/api/token',
            data=sp_credential_data,
            auth = (config.get("spotify", "spotify_client"),
                config.get("spotify", "spotify_secret")))

    headers["Authorization"] = 'Bearer ' + credentials.json()["access_token"]

    return headers


if __name__ == '__main__':

    db, reddit, youtube, config = init_services()
    delete_bad_comments(reddit)

    submissions = get_spotify_submissions(reddit)
    spotify_headers = get_spotify_headers(config)

    for submission in submissions:
        print("\n")
        response = requests.get('https://api.spotify.com/v1/tracks/' + submission['track'] , headers=spotify_headers)
        sp_data = json.loads(response.content)
        artist = sp_data["artists"][0]["name"]
        track_name = sp_data["name"]

        yt = get_url_yt(artist, track_name)
        sc = get_url_sc(artist, track_name)

        if sc or yt:
            comment = "Hi, for the non-Spotify folk, I tried to get links elsewhere on the web. Here's what I came up with:"
            if sc:
                comment += "\n\nSoundCloud: [" + sc["name"] + "](" + sc_url + sc["link"] + ")"
            if yt:
                yt_title = yt['snippet']['title']
                yt_url = 'https://www.youtube.com/watch?v=' + yt['id']
                comment += "\n\nYouTube: [" + yt_title + "](" + yt_url + ")"
            comment += "\n\n^(Am I doing a bad job? Downvote me to make me go away.)"

            print(comment)
            print(submission)
            print(dir(submission))
            db['replied_to'].insert(dict(post_id=submission['post'].id))
            submission['post'].reply(comment)

