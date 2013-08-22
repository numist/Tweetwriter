#!/usr/bin/python

import serial
import time
import glob
import json

from rauth import OAuth1Session

def readFile(filename):
    f = open(filename, 'r')
    result = f.read()
    f.close()
    return result

class Printer:
    allowed_characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%&*()-_+=[]?/,.<>;:\'"'
    def type(self, tweet, time, name):

        print "@"+name+" tweeted: \""+tweet+"\" at "+time

        devs = glob.glob('/dev/ttyUSB*')
        if len(devs):
            for dev in devs:
                print "Pringing to "+dev
                self.sprint(dev, 115200, "@"+name+": \""+tweet+"\"")
        else:
            print "No output devices found"

    def sprint(self, path, baud, payload):
        port = serial.Serial(path, baud)
        pos = 0
        for c in payload:
            if c not in self.allowed_characters:
                c = "?"
            port.write(c)
            if c == '\n':
                pos = 0
                time.sleep(2)
            else:
                pos = pos + 1
                time.sleep(0.1)
                """ Dumb line wrapping for now """
                if pos > 80:
                    port.write('\n')
                    time.sleep(2)
                    pos = 0

class Tweeter:
    session = None
    latest = None
    def __init__(self, id=None):
        if self.session is None:
            config = json.loads(readFile('config.json'))
            print config
            self.session = OAuth1Session(config['consumer_key'],
                                         config['consumer_secret'],
                                         config['access_token'],
                                         config['access_token_secret'])
        if id is None:
            self.fetch()
        else:
            latest = id
    def fetch(self):
        params = {'q': '@Square', 'result_type': 'recent'}
        if self.latest is not None:
            params['since_id'] = self.latest
        result = self.session.get('https://api.twitter.com/1.1/search/tweets.json', params=params).json()
        if result['statuses'] and len(result['statuses']):
            tweets = result['statuses']
            self.latest = tweets[0]['id_str']
            print "Tweeter: latest tweet id is " + self.latest
            return tweets
        else:
            print "Tweeter: no new tweets"
        return []
        
def printTweets(tweets):
    tweets.reverse()
    for tweet in tweets:
        Printer().type(tweet['text'], tweet['created_at'], tweet['user']['screen_name'])

tweeter = Tweeter(id='370432577292615680')
tweets = tweeter.fetch()
printTweets(tweets)
print "sleeeeepy"
tweeter.fetch()
printTweets(tweets)
