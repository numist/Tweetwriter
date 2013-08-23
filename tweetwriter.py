#!/usr/bin/python
# -*- coding: utf-8 -*-

# sys:
import datetime
import glob
import HTMLParser
import json
import os
import random
import syslog
import time

# deps:
import serial                   # pyserial
import dateutil.parser          # python-dateutil
import pytz                     # pytz
from rauth import OAuth1Session # rauth

os.environ['TZ'] = 'us/Pacific'
time.tzset()

def readFile(filename):
    f = open(filename, 'r')
    result = f.read()
    f.close()
    return result

class Printer:
    allowed_characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%&*()-_+=[]?/,.<>;:\'" \n\t'

    def type(self, output):
        devs = glob.glob('/dev/ttyUSB*')
        if len(devs):
            for dev in devs:
                syslog.syslog(syslog.LOG_INFO, "Printing to "+dev)
                self.sprint(dev, 115200, output)
        else:
            syslog.syslog(syslog.LOG_WARNING, "No output devices found")

    def typeTweet(self, tweet, created, name, place):
        timestamp = dateutil.parser.parse(created).astimezone(pytz.timezone('US/Pacific'))
        output = "@"+name+" at "+timestamp.strftime("%H:%M:%S %Z")
        if place is not None:
            output = output+" in "+place['full_name']
        output = output + ":\n"+tweet+"\n\n\n"
        print output.strip()

        syslog.syslog(syslog.LOG_INFO, "Tweet by @"+name+" from "+created)
        self.type(output)

    def sprint(self, path, baud, payload):
        port = serial.Serial(path, baud)
        time.sleep(5)
        pos = 0
        for c in payload:
            if c not in self.allowed_characters:
                print "replacing character '"+c+"' with '?'"
                c = "?"
            port.write(c)
            if c == '\n':
                sleeptime = 2.0 * float(pos) / 65.0 + 0.2
                pos = 0
                time.sleep(sleeptime)
            else:
                pos = pos + 1
                time.sleep(0.1)
                """ Dumb line wrapping for now """
                if pos >= 65:
                    syslog.syslog(syslog.LOG_WARNING, "Force wrapping")
                    port.write('\n')
                    time.sleep(2.2)
                    pos = 0

class Tweeter:
    session = None
    latest = None
    def __init__(self, id=None):
        if self.session is None:
            config = json.loads(readFile('config.json'))
            self.session = OAuth1Session(config['consumer_key'],
                                         config['consumer_secret'],
                                         config['access_token'],
                                         config['access_token_secret'])
        if id is None:
            self.fetch()
        else:
            self.latest = id

    def fetch(self):
        params = {'q': '@Square', 'result_type': 'recent'}
        if self.latest is not None:
            params['since_id'] = self.latest
        result = self.session.get('https://api.twitter.com/1.1/search/tweets.json', params=params).json()
        if result['statuses'] and len(result['statuses']):
            tweets = result['statuses']
            self.latest = tweets[0]['id_str']
            syslog.syslog(syslog.LOG_INFO, "Latest tweet id is " + self.latest)
            return tweets
        else:
            syslog.syslog(syslog.LOG_INFO, "No new tweets since " + self.latest)
        return []
        
def printTweets(tweets):
    tweets.reverse()
    h = HTMLParser.HTMLParser()
    for tweet in tweets:

        """ NO MORE RETWEETS JESUS """
        if tweet['text'].startswith('RT @'):
            print "Skipping RT by "+tweet['user']['screen_name']
            continue

        """ CURLY QUOTES ARE THE DEVIL """
        tweet['text'] = tweet['text'].replace('“'.decode('utf-8'), '"').replace('”'.decode('utf-8'), '"')
        """ SO ARE ELLIPSES """
        tweet['text'] = tweet['text'].replace('…'.decode('utf-8'), '...')

        Printer().typeTweet(h.unescape(tweet['text']), tweet['created_at'], tweet['user']['screen_name'], tweet['place'])

tweeter = Tweeter('370726959707222017')
date = datetime.date.today()

while 1:
    tweets = tweeter.fetch()
    printTweets(tweets)
    time.sleep(60)
    newdate = datetime.date.today()
    if date.day != newdate.day:
        print "Day changed to "+date.strftime("%A %B %d, %Y")
        Printer().type("Day changed to: "+newdate.strftime("%A %B %d, %Y")+"\n\n\n")
    date = newdate
