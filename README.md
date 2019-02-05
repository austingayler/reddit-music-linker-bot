# reddit-music-linker-bot

Since Python is fun and I hadn't done anything in Python in a while, I decided to make a reddit bot that posts alternative links for music posted in a subreddit. Turned out to be much more complicated than I was expecting... 

1. Uses PRAW to get the hot posts in a subreddit
2. Checks the local db file (which simply stores a list of post IDs we've already commented on). Skips post if so.
3. Extracts the Spotify track IDs from the submitted URL, and queries the Spotify API to get the official metadata (track/artist name)
4. Using that data, do a Youtube video search. We get a list of video results from this. However, I wanted to verify that the song lengths were similar (=> greater likelihood of being the 'correct' video), so...it has to do another query to the YT api because the normal search results endpoint does not include video times in the response, annoyingly enough. Perform this second query and select the best match from the results.
4.5. Message `/r/trap`'s main moderator, `ghostmacekillah`. I wanted to be respectful of the subreddit s/he puts so much work into moderating, so I asked them first. They suggested adding SoundCloud links as well.
5. Easy. Just import the API, and...oh wait, SoundCloud hasn't handed out API keys for a couple of years now (gleaned from reading various forums). Okay, backup plan. Just download the page with BeautifulSoup and parse that. Wait, nevermind. The search results are lazy-loaded in the SC website so it's not that simple. Okay, add another layer. Selenium to the rescue. Boot up a Selenium Chrome driver, load the page and theeeen we can parse the HTML. Great. Load a search result in a local browser, see how to select the song titles in the page: looks like they're in there as `a.soundTitle__title`. Grab all those on the page, do a primitive check to see if the artist's name is even in the search results (the results seem to be quite irrelevant sometimes), then return that as the alternative link. It would be cool to also compare the song lengths, but...
6. `TODO: use an image recognition library to extract the song length from the song's <canvas />, and use that as a metric of validity`
7. Finally, post the comment to the Reddit submission.
8. Update the local db to record that we've commented on that submission. 
9. Sometimes the links might be incorrect. If any of the bot's comments are below a score of 1, delete them.
