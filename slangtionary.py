from __future__ import division
import json
from lxml import html
import requests
import tweepy
import time
import sys
import re
import math
from stemming.porter2 import stem
from operator import itemgetter
from random import randint
from utility import TextProcess
from collections import defaultdict, OrderedDict
from math import log, sqrt
from operator import itemgetter

class TwitterCrawler():
        # Fill in the blanks here for your own Twitter app.
        consumer_key = "TC5bMiNlg0onU5tZkxZSMIPks"
        consumer_secret = "bDE2pVIa6EPFksMJikQL6mG8b3TwOA5j85swgRGVRIsYW764ET"
        access_key = "2834729734-jZM6x0heA2aryjIfLsbzvEwSpmIDLk2ywCMEFsI"
        access_secret = "L5w3qpfFfGcrF7vtmfndIaNqt7LvIGMyBlZkJn04dwOZt"
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
                self.words = [] #list of slang words from urban dictionary
                self.tweets = {} #{word:[list of status dicts]}
                self.scores = [] # [ { id: 231, 'text': fsdfs, 'score':0.23} , { id: 231, 'text': fsdfs, 'score':0.23} ]
                self.sortedTweets = {} # { word: self.scores, 
                
        def get_new_slang(self):
                ''' sets the words member'''
                page = requests.get('http://www.urbandictionary.com/yesterday.php')
                tree = html.fromstring(page.text)
                terms = tree.xpath('//div[@id="columnist"]//li/a/text()')
                self.words = terms

        def get_twitter_results(self, query, count):
                '''sets tweets member - type: list of dictionaries'''
                self.tweets[query] = self.tc.api.search(q = query, count = count, language = "en")['statuses']
                #maybe later trim down unneeded fields
        
        def calc_tweet_scores(self):
                '''calculate relevancy of tweets
                                - 20% from favorite count
                                - 30% from retweet count
                                - 30% from number of followers_count
                                - 20% from user's total number of tweets
                   (these amounts may be adjusted later)'''
                #score = 0
                for word in self.tweets:
                        sortedList =[]
                        for t in self.tweets[word]:
                                # adds up to 100%
                                score = 0
                                score += math.log(t['favorite_count']+1,2) * 0.35
                                score += math.log(t['retweet_count']+1,2) * 0.35
                                score += math.log(t['user']['followers_count']+1,2) * 0.15
                                score += math.log(t['user']['statuses_count']+1,2) * 0.15

                                #stemming the texts
                                tokens = TextProcess.tokenize(t['text'])
                                list_of_stem_words = TextProcess.stemming(tokens)
                                text = ' '.join(list_of_stem_words).strip()
                                self.scores.append({ 'id': t['id'], 'text': unicode(text,errors='ignore'), 'score' : score})
                                #print t
                                #print self.tc.crawl_user_profile(t['user']['id'])
                                #print "\n_____________________\n"
                                #print self.tc.crawl_user_tweets(t['user']['id'],3)
                                #print self.tc.crawl_user_profile(32952561)
                                sortedList = sorted(self.scores, key = lambda k: k['score'], reverse=True)[0:100]
                        self.sortedTweets[word] = sortedList
                print self.sortedTweets

if __name__ == '__main__':
        sl = Slangtionary()
        sl.get_new_slang()
        tojson = {}
        print 'got slang words'
        #for now, just show results for first word and 5 tweets from search
        for w in sl.words[5:20]:
                sl.get_twitter_results(w, 10)
        #sl.get_twitter_results(sl.words[7], 1)
        sl.calc_tweet_scores()
        #prints out slang word followed by a list of tweet IDs and their associated scores
        #print sl.words[7]
        #print '==================='
        #for item in sl.scores.keys():
        #	print unicode(sl.scores[item][0]) + ': ' + unicode(sl.scores[item][1])
        #need to put this into a dict, then dump to json
        with open('score.json','w') as f:
                json.dump(sl.sortedTweets,f)
        with open('slangtionary.json', 'w') as f:
                json.dump(sl.tweets, f)
