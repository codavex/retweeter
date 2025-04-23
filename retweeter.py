#!/usr/bin/python3

import configparser
import time
import sys
import logging
import logging.config
import logging.handlers
import tweepy


def setup_api(bearer_token):
    return tweepy.Client(bearer_token)


def blacklist_match(text, blacklist):
    for blacklist_item in blacklist.split(","):
        if blacklist_item in text:
            return True
    return False


def already_retweeted(tweet_to_check):
    #if hasattr(tweet_to_check, 'retweeted_status'):
         #for retweet in api.get_retweets(tweet_to_check.retweeted_status.id):
         #   if USERNAME in retweet.user.screen_name:
         #       return True
    return False


if len(sys.argv) != 2:
    print("Need a config file")
    sys.exit(0)

Config = configparser.ConfigParser()
Config.read(sys.argv[1])

SEARCH_TERMS = Config.get("Search", "SEARCH_TERMS")
BLACKLIST_TERMS = Config.get("Search", "BLACKLIST_TERMS")

BASE_CONFIG = Config.get("Settings", "BASE_CONFIG")
Config.read(BASE_CONFIG)

# get the authentication information from the ini file
BEARER_TOKEN = Config.get("Authentication", "BEARER_TOKEN")

USERNAME = Config.get("Settings", "USERNAME")
THROTTLE = Config.getint("Settings", "THROTTLE")
EXCLUDE_MENTIONS = Config.getboolean("Settings", "EXCLUDE_MENTIONS")
RESTRICT_USERS = Config.getint("Settings", "RESTRICT_USERS")
TRIAL_RUN = Config.getboolean("Settings", "TRIAL_RUN")
LOG_CONFIG = Config.get("Settings", "LOG_CONFIG")

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

# get more recent tweets by USERNAME
try:
    response = client.get_users_tweets(
        id=my_id,
        # tweet_fields=['author_id', 'entities'],
        # user_fields=['username', 'public_metrics', 'description', 'location'],
        # tweet_fields=['author_id','created_at', 'geo', 'public_metrics', 'text'],
        expansions=['author_id', 'entities.mentions.username'],
        user_fields=['username'],
        tweet_fields=['author_id', 'created_at', 'referenced_tweets', 'text'],
        #expansions=['author_id'],

        max_results=RESTRICT_USERS,
        )
except tweepy.errors.TweepyException as e:
    logger.error('Error getting recent retweets %s', e)
    sys.exit(-1)

# get id of most recent tweet
recent_tweets = response.data
recent_authors = response.includes
most_recent_tweet = response.data[0]
logger.debug("Most recent tweet: %s", most_recent_tweet.text)

print(recent_authors)

for tweet in recent_tweets:
    logger.debug("%s %s", tweet.author_id, tweet.text)

# get last X tweets authors
retweeted_authors = []
if RESTRICT_USERS:
    for user in recent_authors['users']:
        retweeted_authors.append(
            user.username
        )

logger.debug("retweeted_authors: %s", retweeted_authors)

# get tweets
results = []

results += reversed(
    client.search_recent_tweets(
        query=SEARCH_TERM,
        # tweet_fields=['author_id', 'entities', 'referenced_tweets'],
        # user_fields=['username'],
        user_fields=['username', 'public_metrics', 'description', 'location'],
        tweet_fields=['author_id','created_at', 'geo', 'public_metrics', 'text'],
        # expansions=['author_id', 'entities.mentions.username'],
        expansions=['author_id'],
        max_results=100,
    )
)

# if we've had multiple search terms, sort to get back in time order
# results.sort(key=lambda result: result.id)

print(results[2])
print(results[3])
print("\n\n\n")
logger.info("Found %d tweet(s)", results[0]['result_count'])

print(results)

# retweet what we've found.
for result in results[3]:
    logger.info(
            "Tweet under consideration: %d - %s",
            result.id,
            result.text
            )

    if TRIAL_RUN:
        # do nothing
        logger.info("TRIAL RUN - not retweeting")
    elif EXCLUDE_MENTIONS and USERNAME in result.text:
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
            client.retweet(result.id)
            retweeted_authors.append(result.author.screen_name)
            time.sleep(THROTTLE)
        except tweepy.errors.TweepyException as e:
            logger.error('Error retweeting: %s', e)
