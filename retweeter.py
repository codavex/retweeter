#!/usr/bin/python

import tweepy, time, sys
import ConfigParser

if len(sys.argv) != 2:
  print "Need a config file"
  exit(0)

Config = ConfigParser.ConfigParser()
Config.read(sys.argv[1])

# get the authentication information from the ini file
CONSUMER_KEY = Config.get("Authentication", "CONSUMER_KEY")
CONSUMER_SECRET = Config.get("Authentication", "CONSUMER_SECRET")
ACCESS_KEY = Config.get("Authentication", "ACCESS_KEY")
ACCESS_SECRET = Config.get("Authentication", "ACCESS_SECRET")

THROTTLE = Config.getint("Settings", "THROTTLE")
EXCLUDE_MENTIONS = Config.getboolean("Settings", "EXCLUDE_MENTIONS")

SEARCH_TERMS = Config.get("Search", "SEARCH_TERMS")

# authenticate
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

# get my user details
whoami = api.me()
 
# get id of most recent tweet
most_recent_tweet = api.user_timeline(count = 1)[0]

# get tweets 
results = []

for search_string in  SEARCH_TERMS.split(","):
  results += reversed(api.search(q="\""+search_string+"\"",since_id=most_recent_tweet.id))

# retweet what we've found.
for result in results:
  if not (EXCLUDE_MENTIONS and whoami.screen_name in result.text):
    api.retweet(result.id)
    time.sleep(THROTTLE)

