#!/usr/bin/python3

import configparser
import time
import sys
import logging
import logging.config
import logging.handlers
import tweepy


def setup_api(consumer_key, consumer_secret, access_key, access_secret):
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    return tweepy.API(auth)


def blacklist_match(text, blacklist):
    for blacklist_item in blacklist.split(","):
        if blacklist_item in text:
            return True
    return False


def already_retweeted(tweet_to_check):
    if hasattr(tweet_to_check, 'retweeted_status'):
        for retweet in api.get_retweets(tweet_to_check.retweeted_status.id):
            if whoami.screen_name in retweet.user.screen_name:
                return True
    return False


if len(sys.argv) != 2:
    print("Need a config file")
    sys.exit(0)

Config = configparser.ConfigParser()
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
LOG_CONFIG = Config.get("Settings", "LOG_CONFIG")

SEARCH_TERMS = Config.get("Search", "SEARCH_TERMS")
BLACKLIST_TERMS = Config.get("Search", "BLACKLIST_TERMS")

# set up logging
logging.config.fileConfig(LOG_CONFIG)
logger = logging.getLogger(__name__)

# authenticate and setup tweepy
api = setup_api(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET)

# get my user details
whoami = api.get_user()
logger.info("whoami: %s", whoami.screen_name)

# get id of most recent tweet
most_recent_tweet = api.user_timeline(count=1)[0]
logger.debug("Most recent tweet: %s", most_recent_tweet.text)

# get last X tweets authors
retweeted_authors = []

if RESTRICT_USERS:
    recent_tweets = api.user_timeline(count=RESTRICT_USERS)

    for tweet in recent_tweets:
        retweeted_authors.append(tweet.entities['user_mentions'][0]['screen_name'])

logger.debug("retweeted_authors: %s", retweeted_authors)

# get tweets
results = []

for search_string in SEARCH_TERMS.split(","):
    results += reversed(api.search_tweets(q="\""+search_string+"\"", since_id=most_recent_tweet.id, result_type='recent'))

# if we've had multiple search terms, sort to get back in time order
results.sort(key=lambda result: result.id)

logger.info("Found %d tweets", len(results))

# retweet what we've found.
for result in results:
    logger.info("Tweet under consideration: %s - %s", result.author.screen_name, result.text)

    if TRIAL_RUN:
        # do nothing
        logger.info("TRIAL RUN - not retweeting")
    elif EXCLUDE_MENTIONS and whoami.screen_name in result.text:
        # do nothing if we're excluding mentions and mentioned
        logger.info("Mentioned in tweet - not retweeting")
    elif RESTRICT_USERS and result.author.screen_name in retweeted_authors:
        # if users has been retweeted recently, ignore
        logger.info("User retweeted recently - not retweeting")
    elif blacklist_match(result.text, BLACKLIST_TERMS):
        # tweet matches blacklisted terms, ignore
        logger.info("Blacklist hit - not retweeting")
    elif already_retweeted(result):
        # if I've already retweeted, ignore
        logger.info("Already retweeted - not retweeting")
    else:
        logger.info("Retweeting")
        try:
            api.retweet(result.id)
            retweeted_authors.append(result.author.screen_name)
            time.sleep(THROTTLE)
        except tweepy.errors.TweepyException as e:
            logger.error('Error retweeting: %s', e)
