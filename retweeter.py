#!/usr/bin/python

import logging
import tweepy, time, sys
import ConfigParser

from logging.handlers import RotatingFileHandler

def setupApi(consumerKey, consumerSecret, accessKey, accessSecret):
  auth = tweepy.OAuthHandler(consumerKey, consumerSecret)
  auth.set_access_token(accessKey, accessSecret)
  api = tweepy.API(auth)
  return api

def setupLogging(logfile):
  logging.basicConfig(level=logging.DEBUG)
  logger = logging.getLogger(__name__)

  handler = RotatingFileHandler(logfile, maxBytes=100000, backupCount=8)
  handler.setLevel(logging.DEBUG)

  formatter = logging.Formatter("%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s")
  handler.setFormatter(formatter)

  logger.addHandler(handler)
  return logger

def blacklist_match(text, blacklist):
  for blacklist_item in blacklist.split(","):
    if blacklist_item in text:
      return True
  return False

def already_retweeted(whoami, retweets):
  for retweet in retweets:
    if whoami.screen_name in retweet.user.screen_name:
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
TRIAL_RUN = Config.getboolean("Settings", "TRIAL_RUN")
LOGFILE = Config.get("Settings", "LOGFILE")

SEARCH_TERMS = Config.get("Search", "SEARCH_TERMS")
BLACKLIST_TERMS = Config.get("Search", "BLACKLIST_TERMS")

# set up logging
logger = setupLogging(LOGFILE)

# authenticate and setup tweepy
api = setupApi(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET)

# get my user details
whoami = api.me()
logger.info("whoami: %s", whoami.screen_name)

# get id of most recent tweet
most_recent_tweet = api.user_timeline(count = 1)[0]
logger.debug("Most recent tweet: %s - %s", most_recent_tweet.author.screen_name, most_recent_tweet.text )

# get last X tweets authors
retweeted_authors = []

if (RESTRICT_USERS):
  recent_tweets = api.user_timeline(count = RESTRICT_USERS)

  for tweet in recent_tweets:
    retweeted_authors.append(tweet.entities['user_mentions'][0]['screen_name'])

logger.debug("retweeted_authors: %s", retweeted_authors)

# get tweets 
results = []

for search_string in  SEARCH_TERMS.split(","):
  results += reversed(api.search(q="\""+search_string+"\"",since_id=most_recent_tweet.id,result_type='recent'))

# if we've had multiple search terms, sort to get back in time order
results.sort(key=lambda result: result.id)

# retweet what we've found.
for result in results:
  logger.info("Tweet under consideration: %s - %s", result.author.screen_name, result.text )

  if (TRIAL_RUN):
    # do nothing
    logger.debug("TRIAL RUN - not retweeting")
    pass
  elif (EXCLUDE_MENTIONS and whoami.screen_name in result.text):
    # do nothing if we're excluding mentions and mentioned
    logger.debug("Mentioned in tweet - not retweeting")
    pass
  elif (RESTRICT_USERS and result.author.screen_name in retweeted_authors):
    # if users has been retweeted recently, ignore
    logger.debug("User retweeted recently - not retweeting")
    pass
  elif (blacklist_match(result.text, BLACKLIST_TERMS)):
    logger.debug("Blacklist hit - not retweeting")
    pass
  elif hasattr (result, 'retweeted_status') and already_retweeted(whoami, api.retweets( result.retweeted_status.id) ):
    # if I've already retweeted, ignore
    logger.debug("Already retweeted - not retweeting")
    pass
  else:
    logger.info("Retweeting")
    api.retweet(result.id)
    time.sleep(THROTTLE)

