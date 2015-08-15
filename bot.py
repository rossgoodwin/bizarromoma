import os
import time
import json
import string
from collections import defaultdict, Counter
from random import random

import tweepy

class TwitterAPI:
    """
    Class for accessing the Twitter API.

    Requires API credentials to be available in environment
    variables. These will be set appropriately if the bot was created
    with init.sh included with the heroku-twitterbot-starter
    """
    def __init__(self):
        consumer_key = "ZyyYUZVcGfbMBa644Ey77Tu5b"
        consumer_secret = "FgL9UAXDin6YQwR1ILqMdE8aCLG9wPkhKDm8wJibyNnWLem2kc"
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        access_token = "3299819928-mYYqdXnQmZTURU9iXaalXDq7BGnCESNfe7MGUJE"
        access_token_secret = "1pkxjxkpIPQCnAM0zEttaCHKezdlW5Co3x5B2KY1j40qI"
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth)

    def tweet(self, message):
        """Send a tweet"""
        self.api.update_status(status=message)


def train_char_lm(fname, order=4):
#     data = file(fname).read()
    data = fname
    lm = defaultdict(Counter)
    pad = "~" * order
    data = pad + data
    for i in xrange(len(data)-order):
        history, char = data[i:i+order], data[i+order]
        lm[history][char]+=1
    def normalize(counter):
        s = float(sum(counter.values()))
        return [(c,cnt/s) for c,cnt in counter.iteritems()]
    outlm = {hist:normalize(chars) for hist, chars in lm.iteritems()}
    return outlm

def generate_letter(lm, history, order):
        history = history[-order:]
        dist = lm[history]
        x = random()
        for c,v in dist:
            x = x - v
            if x <= 0: return c
            
def generate_text(lm, order, nletters=5000):
    history = "~" * order
    out = []
    for i in xrange(nletters):
        c = generate_letter(lm, history, order)
        history = history[-order:] + c
        out.append(c)
    return "".join(out)


# In[148]:

def fix_unmatched(l):
    unmatched_locs = []
    unmatched_locs_rev = []
    
    def error(c, column_number):
#         print 'Error: unmatched', c, 'column', column_number
        if c in [')', ']', '}']:
            unmatched_locs.append(column_number)
        else:
            unmatched_locs_rev.append(column_number)

    def check(stack, wanted, c, column_number):
        if stack:
            if stack[-1] != wanted:
                error(c, column_number)
            else:
                stack.pop()
        else:
            error(c, column_number)
        
    def check_parentheses(line):
        stack = list()
        column_number = 0
        for c in line:
            if c == '(' or c == '[' or c == '{':
                stack.append(c)
            elif c == ')':
                check(stack, '(', ')', column_number)
            elif c == ']':
                check(stack, '[', ']', column_number)
            elif c == '}':
                check(stack, '{', '}', column_number)
            column_number += 1
            
    def check_parentheses_rev(line):
        stack = list()
        column_number = 0
        for c in line:
            column_number += 1
            if c == ')' or c == ']' or c == '}':
                stack.append(c)
            elif c == '(':
                check(stack, ')', '(', column_number)
            elif c == '[':
                check(stack, ']', '[', column_number)
            elif c == '{':
                check(stack, '}', '{', column_number)
                
    check_parentheses(l)
    
    lchars = list(l)
    
    newTitle = ''.join([i for j, i in enumerate(lchars) if j not in unmatched_locs])
    
    check_parentheses_rev(newTitle[::-1])
    
    real_unmatched_rev = map(lambda i: len(newTitle)-i, unmatched_locs_rev)
    
    titChars = list(newTitle)
    
    newTitle = ''.join([i for j, i in enumerate(titChars) if j not in real_unmatched_rev])
    
    numDoubleQuotes = newTitle.count('\"')
    if numDoubleQuotes % 2:
        newTitle = string.replace(newTitle, '\"', '', 1)
    
    numSingleQuotes = newTitle.count("\'")
    if numSingleQuotes % 2:
        newTitle = string.replace(newTitle, "\'", "", 1)
        
    return newTitle

def main():
    generatedTexts = map(lambda lm: generate_text(lm, 7), lms)

    entry_candidates = map(lambda x: x.split('\n'), generatedTexts)

    def remove_plagiarized(i):
        plagiarized = set(entry_candidates[i]) & set(data[i])
        keepers = map(fix_unmatched, list(set(entry_candidates[i]) - plagiarized))
        return keepers
                           
    entries = map(remove_plagiarized, range(len(data)))

    invented_art = zip(*entries)

    def unpack(tup):
        t, a, m = tup
        outstr = "%s\n%s\n%s" % (t, a, m)
        return outstr
        
    output = filter(lambda x: len(x) <= 140, map(unpack, invented_art))

    return output


fileObj = open('artworks.json', 'r')
art = json.load(fileObj)[:75000]
fileObj.close()
print "Artwork list loaded..."

titles = map(lambda d: d['title'], art)
artists = map(lambda d: d['artist'], art)
media = map(lambda d: d['medium'], art)

print "Got titles, artists, media..."
# dimensions = map(lambda d: d['dimensions'], art)

data = [titles, artists, media]
lms = map(lambda l: train_char_lm('\n'.join(l), order=7), data)

print "Got language models..."

if __name__ == "__main__":
    twitter = TwitterAPI()
    while True:
        toTweet = main()
        print "Got toTweet list..."
        while toTweet:
            curTweet = toTweet.pop()
            print "Posting tweet..."
            twitter.tweet(curTweet)
            print "...tweet posted!"
            time.sleep(120)
