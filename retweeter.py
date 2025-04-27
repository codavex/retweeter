#!/usr/bin/python3

import configparser
import datetime
import sys
import logging
import logging.config
import logging.handlers
import tweepy


def setup_api(bearer_token):
    return tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)


def blacklist_match(text, blacklist):
    for blacklist_item in blacklist.split(","):
        if blacklist_item in text:
            return True
    return False


def already_retweeted(tweet_id, my_id):
    try:
        retweets_response = client.get_retweeters(id=tweet_id)
    except tweepy.errors.TweepyException as e:
        logger.error('Error looking up %s, %s', USERNAME, e)
        sys.exit(-1)
    users = retweets_response.data
    if users:
        for user in users:
            if user.id == my_id:
                return True
    return False


if len(sys.argv) != 2:
    print("Need a config file")
    sys.exit(0)

Config = configparser.ConfigParser()
Config.read(sys.argv[1])

SEARCH_TERM = Config.get("Search", "SEARCH_TERM")
BLACKLIST_TERMS = Config.get("Search", "BLACKLIST_TERMS")

BASE_CONFIG = Config.get("Settings", "BASE_CONFIG")
Config.read(BASE_CONFIG)

# get the authentication information from the ini file
BEARER_TOKEN = Config.get("Authentication", "BEARER_TOKEN")

USERNAME = Config.get("Settings", "USERNAME")
EXCLUDE_MENTIONS = Config.getboolean("Settings", "EXCLUDE_MENTIONS")
TRIAL_RUN = Config.getboolean("Settings", "TRIAL_RUN")
LOG_CONFIG = Config.get("Settings", "LOG_CONFIG")
SEARCH_WINDOW = Config.getint("Settings", "SEARCH_WINDOW")

# set up logging
logging.config.fileConfig(LOG_CONFIG)
logger = logging.getLogger(__name__)

# authenticate and setup tweepy
client = setup_api(BEARER_TOKEN)

# get my user details
logger.info("USERNAME: %s", USERNAME)

response = []
try:
    response = client.get_user(username=USERNAME)
except tweepy.errors.TweepyException as e:
    logger.error('Error looking up %s, %s', USERNAME, e)
    sys.exit(-1)

my_id = response.data.id

# get tweets
results = []
try:
    results = client.search_recent_tweets(
        query=f"\"{SEARCH_TERM}\"",
        user_fields=['username'],
        tweet_fields=['author_id', 'created_at', 'referenced_tweets', 'text'],
        expansions=['author_id'],
        max_results=100,
        start_time=datetime.datetime.now() - datetime.timedelta(hours = SEARCH_WINDOW)
    )
except tweepy.errors.TweepyException as e:
    logger.error('Error getting searching for tweets: %s', e)
    sys.exit(-1)

logger.info("Found %d tweet(s)", results[3]['result_count'])

if results[0] == None:
    logger.info("No tweets found - exiting")
    sys.exit(-1)

found_tweets = reversed(results[0])
# retweet what we've found.
for tweet in found_tweets:
    logger.info(
            "Tweet under consideration: %d - %s - %s",
            tweet.id,
            tweet.text,
            tweet.created_at
            )
    if TRIAL_RUN:
        # do nothing
        logger.info("TRIAL RUN - not retweeting")
    elif EXCLUDE_MENTIONS and USERNAME in tweet.text:
        # do nothing if we're excluding mentions and mentioned
        logger.info("Mentioned in tweet - not retweeting")
    elif blacklist_match(tweet.text, BLACKLIST_TERMS):
        # tweet matches blacklisted terms, ignore
        logger.info("Blacklist hit - not retweeting")
    elif tweet.referenced_tweets and \
            already_retweeted(tweet.referenced_tweets[0].id, my_id):
        # if I've already retweeted, ignore
        logger.info("Already retweeted - not retweeting")
    else:
        logger.info("Retweeting")
        try:
            client.retweet(tweet.id)
        except tweepy.errors.TweepyException as e:
            logger.error('Error retweeting: %s', e)
