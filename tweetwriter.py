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
import serial
import dateutil.parser
import pytz
from rauth import OAuth1Session

config_file = 'config.json'
line_width = 65
serial_glob = '/dev/ttyUSB*'
serial_baud_rate = 115200
serial_allowed_characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%&*()-_+=[]?/,.<>;:\'" \n'
time_zone = 'US/Pacific'
wait_char = 0.1
wait_newline = 2.2
wait_poll = 60
wait_serial_init = 5

def readFile(filename):
    f = open(filename, 'r')
    result = f.read()
    f.close()
    return result

class Printer:
    def type(self, output):
        devs = glob.glob(serial_glob)
        if len(devs):
            for dev in devs:
                syslog.syslog(syslog.LOG_INFO, "Printing to "+dev)
                self.sprint(dev, serial_baud_rate, output)
        else:
            syslog.syslog(syslog.LOG_WARNING, "No output devices found")

    def typeTweet(self, tweet, created, name, place):
        timestamp = dateutil.parser.parse(created).astimezone(pytz.timezone(time_zone))
        output = "@"+name+" at "+timestamp.strftime("%H:%M:%S %Z")
        if place is not None:
            output = output+" in "+place['full_name']
        output = output + ":\n"+tweet+"\n\n\n"
        print output.replace('\n', ' ').strip()

        syslog.syslog(syslog.LOG_INFO, "Tweet by @"+name+" from "+created)
        self.type(output)

    def sprint(self, path, baud, payload):
        port = serial.Serial(path, baud)
        # The FTDI chip resets the Arduino on connect, wait for it to stabilise!
        time.sleep(wait_serial_init)
        pos = 0
        for c in payload:
            if c not in serial_allowed_characters:
                print "replacing character '"+c+"' with '?'"
                c = "?"
            port.write(c)
            if c == '\n':
                sleeptime = float(wait_newline) * float(pos) / float(line_width) + 0.2
                pos = 0
                time.sleep(sleeptime)
            else:
                pos = pos + 1
                time.sleep(wait_char)
                """ Dumb line wrapping """
                if pos >= line_width:
                    syslog.syslog(syslog.LOG_WARNING, "Force wrapping!")
                    port.write('\n')
                    time.sleep(wait_newline)
                    pos = 0

class Tweeter:
    session = None
    latest = None
    def __init__(self, id=None):
        if self.session is None:
            config = json.loads(readFile(config_file))
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

def softWrap(text, cols=80):
    tokens = text.split(" ")
    pos = 0
    text = ""
    for token in tokens:
        if pos + 1 + len(token) >= cols:
            text = text + "\n"
            pos = 0
        elif text != "":
            text = text + " "
            pos = pos + 1
        text = text + token
        pos = pos + len(token)
    return text
        
def printTweets(tweets):
    tweets.reverse()
    h = HTMLParser.HTMLParser()
    for tweet in tweets:

        """ NO MORE RETWEETS JESUS """
        if tweet['text'].startswith('RT @'):
            print "Skipping RT by "+tweet['user']['screen_name']+" ("+tweet['id_str']+")"
            continue

        """ CURLY QUOTES ARE THE DEVIL """
        text = tweet['text'].replace('“'.decode('utf-8'), '"').replace('”'.decode('utf-8'), '"')
        """ SO ARE ELLIPSES """
        text = text.replace('…'.decode('utf-8'), '...')
        text = text.replace('\t', '    ')

        """ &amp -> &, etc """
        text = h.unescape(text)

        text = softWrap(text, line_width)

        Printer().typeTweet(text, tweet['created_at'], tweet['user']['screen_name'], tweet['place'])

# Initialization
os.environ['TZ'] = time_zone
time.tzset()
tweeter = Tweeter('370776114576113665')
date = datetime.date.today()
print "Most recent id: "+tweeter.latest

# Runloop
while 1:
    try:
        tweets = tweeter.fetch()
        printTweets(tweets)
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        print ''.join('!! ' + line for line in lines)
    
    time.sleep(wait_poll)
    newdate = datetime.date.today()
    if date.day != newdate.day:
        print "Day changed to "+date.strftime("%A %B %d, %Y")
        Printer().type("Day changed to: "+newdate.strftime("%A %B %d, %Y")+"\n\n\n")
    date = newdate
