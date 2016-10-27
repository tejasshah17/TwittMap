import tweepy
from tweepy.streaming import StreamListener
from tweepy import Stream
from elasticsearch import Elasticsearch
import time
from flask import Flask,render_template,request
import json
import jinja2

_CONSUMER_KEY = 'IDRWiVEJxA5BLbbLxfK5HVkjd'
_CONSUMER_SEC_KEY = 'RKCIS6bcVxIULPOPbaYsNkqbJco6rifTtsckUstXVOqCfiGR67'
_ACCESS_TOKEN = '789914399427403776-GZZAcCDOMIqS9fbDIRMsISam1D7oLWY'
_ACCESS_TOKEN_SECRET = 'GbqFwczOAQfOtr8KQGfF5aoebWXQhfpOBKM3oGOrzbwmA'


class StdOutListener(StreamListener):
    def on_data(self, data):
        if data != None:
            # print data
            # return True
            jsonData = json.loads(data)
            if 'contributors' in jsonData and jsonData['geo'] is not None:
                #print jsonData['user']['name'] +  " - "  + jsonData['text']
                #print jsonData
                es.index(index='twitter',doc_type='tweet',body=jsonData)
                print jsonData
                return True

    def on_error(self, status):
        print(status)
        if status == 420:
            print "Sleeping 3 sec"
            time.sleep(3)
        return

    def on_exception(self, exception):
        """Called when an unhandled exception occurs."""
        return

application = Flask(__name__)
app = application
es = Elasticsearch()


@app.route('/')
def index():
    if es.indices.exists(index='twitter'):
        searchtext = setTerms[0]
        response = es.search(index='twitter',doc_type='tweet',body={"query":{"query_string":{"query":searchtext,"fields":["text"]}}})
        data = {'searchParams' : setTerms, 'tweets': response['hits']['hits'] }
        return render_template('index.html',data=data)
    else:
        return 'Welcome to TwitterTrends HomePage <br> False'


@app.route('/',methods=['POST'])
def search():
    searchtext = request.form['TrendKeyword']
    response = es.search(index='twitter', doc_type='tweet',body={"query": {"query_string": {"query": searchtext, "fields": ["text"]}}})
    data = {'searchParams': setTerms, 'tweets': response['hits']['hits'],'currentSearch':searchtext}
    return render_template('index.html', data=data)

if __name__ == '__main__':
    ## -------------- SETUP ELASTICSEARCH -------------- ##
    # es = Elasticsearch()
    es.indices.create(index='twitter',ignore = 400)



    ## ------------- START TWITTER API STREAMING -------------##
    l = StdOutListener()
    auth = tweepy.OAuthHandler(_CONSUMER_KEY, _CONSUMER_SEC_KEY)
    auth.set_access_token(_ACCESS_TOKEN, _ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    stream = Stream(auth, l)
    setTerms = ['QueenSugar','NicerRap','GOT','FlytheW','TheWalkingDead','pizza','Instagram','DesignatedSurvivor','Food','Trump']
    #stream.filter(track=setTerms,async=True)
    app.run(debug=True)



