#!/usr/bin/python

# @my_next_band
 
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

# authenticate
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)
 
# get id of most recent tweet
most_recent_tweet = api.user_timeline(count = 1)[0]

# get tweets 
results = reversed(api.search(q="\"my next band name\"",since_id=most_recent_tweet.id))

# retweet what we've found.
for result in results:
  api.retweet(result.id)
  time.sleep(THROTTLE)

