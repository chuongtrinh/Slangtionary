from __future__ import division
import json
from lxml import html
import requests
import tweepy
import time
import operator
import sys
import re
import math
from random import randint
from stemming.porter2 import stem
from operator import itemgetter
from random import randint
from utility import TextProcess
from collections import defaultdict, OrderedDict
from math import log, sqrt
from operator import itemgetter

class TwitterCrawler():
        # Fill in the blanks here for your own Twitter app.
        consumer_key = ""
        consumer_secret = ""
        access_key = ""
        access_secret = ""
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
                newQuery = '\"'+query.lower()+ ' is\" -RT'
                self.tweets[query] = self.tc.api.search(q = newQuery, count = count, lang = "en")['statuses']
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
                self.topWords = {}
                self.count =0;
                self.locations = [ (41.8695355,-87.5879599) , (47.614848,-122.3359059) , (34.0204989,-118.4117325) , (29.817178,-95.4012915) , (38.8993487,-77.0145665), (33.7677129,-84.4206039) , (28.4811689,-81.36875) , (39.091919,-94.5757195)]  

        def frequency(self,word, list_of_word_in_doc):
                return list_of_word_in_doc.count(word)

        def num_of_docs_have_word(self,word, list_of_reviews):
                count = 0
                for review_id, review_text in list_of_reviews.iteritems():
                    if self.frequency(word, review_text) >0:
                        count +=1
                return count
    
        def tf(self,word, list_of_word_in_doc):
                # return number of times that term word occurs in d
                return (self.frequency(word,list_of_word_in_doc) / float(len(list_of_word_in_doc)))

        def idf(self,word, list_of_reviews):
                return math.log(len(list_of_reviews) / self.num_of_docs_have_word(word, list_of_reviews))

        def tfidf_score(self,tf_value,idf_value):
                return ((1 + math.log(tf_value)) * idf_value)
    
        def get_review_tfidf_dict(self,list_of_reviews):
                # calculate number of times that t 
                #return a dictionary with each key,value pair as review_id and review_content

                list_of_reviews_w_tfidf = {}
                for review_id, review_text,score in list_of_reviews.iteritems():
                    list_of_tfidf = {} # build a dictionary with key as word and value as if-idf score
                    for word in review_text:
                        list_of_tfidf[word] = self.tfidf_score(self.tf(word,review_text), self.idf(word,list_of_reviews))
                    list_of_reviews_w_tfidf[review_id+'-'+score] = list_of_tfidf
                    # { [ review_id-score : { word1 : 12; word2 : 34; ..... }}
                return list_of_reviews_w_tfidf
    
        def cosine_similarity_matrix(self,review_tfidf_matrix):
                #return a dictionary with each key,value pair as review_id1,[review_id2,cosine_socre]
                cosine_matrix = {}
                for review_id_1, list_of_scores_1 in review_tfidf_matrix.iteritems():
                    each_cosine_matrix = {}
                    for review_id_2, list_of_scores_2 in review_tfidf_matrix.iteritems():
                        product = 0
                        vec_of_2 = 0
                        vec_of_1 = 0
                        for word,score in list_of_scores_1.iteritems():
                            if word in list_of_scores_2:
                                product += score * list_of_scores_2[word]
                                vec_of_2 += list_of_scores_2[word]**2
                            vec_of_1 += score**2
                        if vec_of_2 == 0:
                            sim = 0
                        else:
                            sim = product / (math.sqrt(vec_of_1) * math.sqrt(vec_of_2))
                        each_cosine_matrix[review_id_2] = sim
                    cosine_matrix[review_id_1] = each_cosine_matrix
                return cosine_matrix
                
        def get_similar_review(self,cosine_similarity_matrix):
                #return most similar review{"r_id_1":"review content", "r_id_2":"review content"}
                # convert 2-d to 1-d [ (review_id_1;;review_id_2, score),   ]
                new_cosine_matrix = {}
                #top_10_reviews = {}
                for review_id, list_of_compared_reviews in cosine_similarity_matrix.iteritems():
                    for review_id_2, cosine_value in list_of_compared_reviews.iteritems():
                        new_review_ids = review_id + ";;" + review_id_2
                        new_cosine_matrix[new_review_ids] = cosine_value
                
                # I don't know how to sort list of list with value inside inner list...
                # convert 2-d to 1-d to sort based on second value 
                top_100_reviews = sorted(new_cosine_matrix, key = lambda rev : rev[1], reverse = True)[0:100]
                #print new_cosine_matrix
                top_reviews = []
               # print top_100_reviews
                for review_ids in top_100_reviews:
                    #put 100 review_id has highest score into a list
                    #most_common to find top 10 reviews
                    reviews = review_ids.split(";;")
                    for review in reviews:
                        if review not in top_reviews:
                            top_reviews.append(review)
                #print top_reviews
                return top_reviews[0:10]

        def get_new_slang(self):
                ''' sets the words member'''
                page = requests.get('http://www.urbandictionary.com/yesterday.php')
                tree = html.fromstring(page.text)
                terms = tree.xpath('//div[@id="columnist"]//li/a/text()')
                self.words = terms
                self.remove_old_words() #go ahead and remove old words here before everything else is done

        def get_twitter_results(self, query, cordX, cordY, count):
                '''sets tweets member - type: list of dictionaries'''
                newQuery = '\"'+query.lower()+ '\" -RT -http'
                geoCodeCords  = '\"' +str(cordX)+ ',' + str(cordY) + ',' + '250mi\"'
                print newQuery
                print geoCodeCords
                qryResult = self.tc.api.search(q = newQuery, geocode = geoCodeCords ,count = count, lang = "en")['statuses']
                #self.count += 1
                if query not in self.tweets:
                        self.tweets[query] = qryResult
                else:
                        self.tweets[query] = self.tweets[query] + qryResult
                #maybe later trim down unneeded fields

        def get_twitter_results2(self, query, count):
                '''sets tweets member - type: list of dictionaries'''
                newQuery = '\"'+query.lower()+ '\" -RT -http'
                print newQuery
                self.tweets[query] = self.tc.api.search(q = newQuery, geocode = "40.7628,-74.0059,200mi" ,count = count, lang = "en")['statuses']
                #maybe later trim down unneeded fields
        
        def calc_tweet_scores(self):
                '''calculate relevancy of tweets
                                - 20% from favorite count
                                - 30% from retweet count
                                - 30% from number of followers_count
                                - 20% from user's total number of tweets
                   (these amounts may be adjusted later)'''
                #score = 0
                with open('test.json','w') as f1:
                        json.dump(self.tweets,f1)
                for word in self.tweets:
                        #print word
                        sortedList =[]
                        count = 0
                        totalscore = 0
                        s = self.tweets[word]
                        with open('test2.json','w') as f1:
                                json.dump(s,f1)
                        for t in self.tweets[word]:
                                # adds up to 100%
                                #print t
                                #print stuff
                                #for t in stuff:    
                                #print "t is:"
                                #print t['favorite_count']
                                print count
                                #t = s[count]
                                if word in t['text']:
                                        #print word
                                        #print unicode(t['text'])
                                        score = 0
                                        score += math.log(t['favorite_count']+1,2) * 0.25
                                        score += math.log(t['retweet_count']+1,2) * 0.025
                                        score += math.log(t['user']['followers_count']+1,2) * 0.05
                                        #score += math.log(t['user']['statuses_count']+1,2) * 0.05
                                        totalscore += score
                                        #stemming the texts
                                        tokens = TextProcess.tokenize(t['text'])
                                        #list_of_stem_words = TextProcess.stemming(tokens)
                                        text = ' '.join(tokens).strip()
                                        self.scores.append({ 'id': t['id'], 'text':unicode(text,errors='ignore'), 'score' : score, 'geo':t['geo']['coordinates']})
                                        #print self.scores
                                count+=1
                        if (totalscore >=0):
                                sortedList = sorted(self.scores, key = lambda k: k['score'], reverse=True)[0:100]
                                sortedList2 = sorted(sortedList, key = lambda k: k['geo'][1], reverse=True)
                                if word not in self.sortedTweets:
                                        self.sortedTweets[word] = sortedList2
                                else:
                                        self.sortedTweets[word] += sortedList2
                                self.scores = []
                                        #self.topWords[word] = totalscore
                                #print sortedList
                #print self.sortedTweets
                #tfidf_dict = self.get_review_tfidf_dict(self.

        def remove_old_words(self):
        	''' remove words from self.words that have lots of definitions'''
        	#api.urbandictionary.com/v0/define?term=___
        	new_words_only = []
        	for word in self.words:
        		if ' ' in word:
        			tempword = word.replace(' ', '+')
        		else:
        			tempword = word
        		url = 'http://api.urbandictionary.com/v0/define?term=' + str(tempword)
        		r = requests.get(url)
        		UDjson = r.json()
        		#apiDict = json.load(UDjson) #convert to python dict
        		if len(UDjson['list']) < 3:
        			new_words_only.append(word)
        	self.words = new_words_only
        	print "after removing words:"
        	print self.words


if __name__ == '__main__':
        sl = Slangtionary()
        sl.get_new_slang()
        sl.tc.check_api_rate_limit(1)
        tojson = {}
        print 'got slang words'
        #for now, just show results for first word and 5 tweets from search
        for w in sl.words[22:23]:
                #picking randomly!
                ran = randint(0,4)
                #if (ran % 3 == 0):
                        #sl.get_twitter_results(w, 50)
                for item in sl.locations:
                        sl.get_twitter_results("salty",item[0],item[1], 12)
                        sl.get_twitter_results("swerve",item[0],item[1], 12)
                        sl.get_twitter_results("basic",item[0],item[1], 12)
                        sl.get_twitter_results("butter face",item[0],item[1], 12)
                        sl.get_twitter_results("bae",item[0],item[1], 12)
                #sl.get_twitter_results("salty",sl.locations[7][0],sl.locations[7][1], 20)
                #sl.get_twitter_results("swerve",sl.locations[7][0],sl.locations[7][1], 20)
                #sl.get_twitter_results("basic",sl.locations[7][0],sl.locations[7][1], 20)
                #sl.get_twitter_results("butter face",sl.locations[7][0],sl.locations[7][1], 20)
                #sl.get_twitter_results("bae",sl.locations[7][0],sl.locations[7][1], 20)
        #sl.get_twitter_results(sl.words[7], 1)
        sl.calc_tweet_scores()
        topTweets = {}
        #print sl.topWords
        topWords2 =  sorted(sl.topWords, key = lambda rev: rev[1], reverse = True)[0:40]
        #print topWords2
        for top_word in topWords2:
                #print top_word
                topTweets[top_word] = sl.sortedTweets[top_word]
        #print topTweets
        with open('score2.json','w') as f1:
                json.dump(sl.sortedTweets,f1)
        with open('slangtionary.json', 'w') as f2:
                json.dump(sl.tweets, f2)
