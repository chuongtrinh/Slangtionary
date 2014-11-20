import json
from lxml import html
import requests
import tweepy
import time
import sys
import re
from random import randint
from collections import defaultdict, OrderedDict
from math import log, sqrt
from operator import itemgetter

class TwitterCrawler():
    # Fill in the blanks here for your own Twitter app.
    consumer_key = "hdtQCs3wdYzbTabEPAii9daoj"
    consumer_secret = "0MxfmOAPAGSF0DF7vDXV7OQXg5AjGgksRPDX6to9VET4FG9oag"
    access_key = "32952561-JJbcCWzlZ9Qmq86bY3FfT0iVzmlEWZXjPRviIsAqS"
    access_secret = "6IV1EWUmvToX2mDARU4Ttenq8E2razoHbtIx85PrDi4Yv"
    auth = None
    api = None

    def __init__(self):
        self.auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        self.auth.set_access_token(self.access_key, self.access_secret)
        self.api = tweepy.API(self.auth, parser=tweepy.parsers.JSONParser(), search_host='search.twitter.com')
        #print self.api.rate_limit_status()

    def re_init(self):
        self.auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        self.auth.set_access_token(self.access_key, self.access_secret)
        self.api = tweepy.API(self.auth, parser=tweepy.parsers.JSONParser(), search_host='search.twitter.com')

    def check_api_rate_limit(self, sleep_time):
        try:
            rate_limit_status = self.api.rate_limit_status()
        except Exception as error_message:
            if error_message['code'] == 88:
                print "Sleeping for %d seconds." %(sleep_time)
                #print rate_limit_status['resources']['statuses']
                time.sleep(sleep_time)

        while rate_limit_status['resources']['statuses']['/statuses/user_timeline']['remaining'] < 10:
            print "Sleeping for %d seconds." %(sleep_time)
            #print rate_limit_status['resources']['statuses']
            time.sleep(sleep_time)
            rate_limit_status = self.api.rate_limit_status()
        #print rate_limit_status['resources']['statuses']['/statuses/user_timeline']

    def crawl_user_profile(self, user_id):
        self.check_api_rate_limit(900)
        try:
            user_profile = self.api.get_user(user_id)
        except:
            return None
        return user_profile

    def crawl_user_tweets(self, user_id, count):
        self.check_api_rate_limit(900)
        try:
            tweets = self.api.user_timeline(user_id, count = count)
        except:
            tweets = None
        tried_count = 0
        while len(tweets) < count:
            try:
                tweets.extend(self.api.user_timeline(user_id, count = count))
            except:
                pass
            tried_count += 1
            if tried_count == 3:
                break
        return tweets[:count]

    def search_from_query(self, query, count):
        results = self.api.search(q = query, count = count, language = "en")
        #for res in results['statuses']:
        #    print res['text']
        return results


class Slangtionary:
	def __init__(self):
		self.tc = TwitterCrawler()
		self.words = []
		self.tweets = []

	def get_new_slang(self):
		''' sets the words member'''
		page = requests.get('http://www.urbandictionary.com/yesterday.php')
		tree = html.fromstring(page.text)
		terms = tree.xpath('//div[@id="columnist"]//li/a/text()')
		self.words = terms

	def get_twitter_results(self, query, count):
		'''sets tweets member - type: list of dictionaries'''
		self.tweets = self.tc.api.search(q = query, count = count, language = "en")['statuses']

	def calc_tweet_scores(self):
		#go through self.tweets
		#for t in self.tweets:
			#some fields to use
			#t['favorite_count']
			#t['retweet_count']
			#t['statuses_count']
			#t['id']
		pass

if __name__ == '__main__':
	sl = Slangtionary()
	sl.get_new_slang()
	print 'got slang words'
	#go through with loop for each word
	sl.get_twitter_results(sl.words[0], 50)
	print sl.tweets