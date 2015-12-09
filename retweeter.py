#!/usr/bin/python

import tweepy, time, sys
import ConfigParser

def blacklist_match(text, blacklist):
  for blacklist_item in blacklist.split(","):
    if blacklist_item in text:
      return True
  return False

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
RESTRICT_USERS = Config.getint("Settings", "RESTRICT_USERS")
DEBUG = Config.getboolean("Settings", "DEBUG")

SEARCH_TERMS = Config.get("Search", "SEARCH_TERMS")
BLACKLIST_TERMS = Config.get("Search", "BLACKLIST_TERMS")

# authenticate
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

# get my user details
whoami = api.me()
 
# get id of most recent tweet
most_recent_tweet_id = api.user_timeline(count = 1)[0].id

# get last X tweets authors

retweeted_authors = []

if (RESTRICT_USERS):
  recent_tweets = api.user_timeline(count = RESTRICT_USERS)

  for tweet in recent_tweets:
    retweeted_authors.append(tweet.entities['user_mentions'][0]['screen_name'])

if (DEBUG):
  print retweeted_authors
  print

# get tweets 
results = []

for search_string in  SEARCH_TERMS.split(","):
  results += reversed(api.search(q="\""+search_string+"\"",since_id=most_recent_tweet_id,result_type='recent'))

# if we've had multiple search terms, sort to get back in time order
results.sort(key=lambda result: result.id)

# retweet what we've found.
for result in results:
  if (DEBUG):
    print "%s - %s: %s" % ( result.id, result.author.screen_name, result.text )

  if (EXCLUDE_MENTIONS and whoami.screen_name in result.text):
    # do nothing if we're excluding mentions and mentioned
    pass
  elif (RESTRICT_USERS and result.author.screen_name in retweeted_authors):
    # if users has been retweeted recently, ignore
    pass
  elif (blacklist_match(result.text, BLACKLIST_TERMS)):
    pass
  else:
    api.retweet(result.id)
    time.sleep(THROTTLE)

