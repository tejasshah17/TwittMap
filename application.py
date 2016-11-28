import tweepy
from tweepy.streaming import StreamListener
from tweepy import Stream
from elasticsearch import Elasticsearch
import time
from flask import Flask,render_template,request,abort
import json

from kafka import KafkaProducer
from kafka.errors import KafkaError
import urllib2


_CONSUMER_KEY = 'IDRWiVEJxA5BLbbLxfK5HVkjd'
_CONSUMER_SEC_KEY = 'RKCIS6bcVxIULPOPbaYsNkqbJco6rifTtsckUstXVOqCfiGR67'
_ACCESS_TOKEN = '789914399427403776-GZZAcCDOMIqS9fbDIRMsISam1D7oLWY'
_ACCESS_TOKEN_SECRET = 'GbqFwczOAQfOtr8KQGfF5aoebWXQhfpOBKM3oGOrzbwmA'


try:

    producer = KafkaProducer(bootstrap_servers=['localhost:9092'],value_serializer=lambda v: json.dumps(v).encode('utf-8'))

except KafkaError:
    print KafkaError

class StdOutListener(StreamListener):

    def on_data(self, data):
        if data != None:
            jsonData = json.loads(data)
            if 'contributors' in jsonData and jsonData['geo'] is not None  and jsonData['lang']== 'en':
                try:
                    future = producer.send('test',jsonData)
                    #record_metadata = future.get(timeout=10)

                    #print "Data Inserted"
                    return True

                except KafkaError,Exception:
                    print KafkaError
                    print Exception



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


new_tweet = False
num_tweet = 0


## -------------- SETUP ELASTICSEARCH -------------- ##
es = Elasticsearch()
es.indices.create(index='twitter', ignore=400)

## ------------- START TWITTER API STREAMING -------------##
l = StdOutListener()
auth = tweepy.OAuthHandler(_CONSUMER_KEY, _CONSUMER_SEC_KEY)
auth.set_access_token(_ACCESS_TOKEN, _ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)


## ---------------- CHANGE SEARCH TERMS TO FIND TRENDING TAGS ------------- ##
setTerms = ['TheEllenShow', 'Cricket', 'Instagram', 'Subway', 'TheWalkingDead', 'pizza', 'Snapchat',
                   'NYC', 'Food', 'Trump']

## -------------- ENABLE TWITTER STREAM DURING DEMO ---------##
stream = Stream(auth, l)
stream.filter(track=setTerms, async=True)

@app.route('/')
def index():
    if es.indices.exists(index='twitter'):
        searchtext = setTerms[0]
        response = es.search(index='twitter',doc_type='tweet',body={"query":{"query_string":{"query":searchtext}}},size=2000)
        data = {'searchParams' : setTerms, 'tweets': response['hits']['hits'] }
        global new_tweet,num_tweet
        new_tweet = False
        num_tweet = 0
        return render_template('index.html',data=data)

    else:
        return 'Welcome to TwitterTrends HomePage <br> False'

@app.route('/',methods=['POST'])
def search():
    try:
        searchtext = request.form['TrendKeyword']
        response = es.search(index='twitter', doc_type='tweet',body={"query": {"query_string": {"query": searchtext}}},size=2000)
        data = {'searchParams': setTerms, 'tweets': response['hits']['hits'], 'currentSearch': searchtext}
        global new_tweet,num_tweet
        new_tweet = False
        num_tweet = 0
        return render_template('index.html', data=data)

    except Exception:
        print Exception.message

def save():
    try:
        j = request.get_json(force=True)
        message = j['Message']
        test = json.loads(message)
        sentiment = test['sentiment']
        es.index(index="twitter",doc_type="tweet",body=json.loads(message))

        global new_tweet,num_tweet
        print str(new_tweet) + "-" + str(num_tweet)

        new_tweet = True
        num_tweet += 1

        print str(new_tweet) + "-" + str(num_tweet)
        return "OK"

    except Exception as e:
        print e.message
        abort(400)


@app.route('/sns', methods=['POST'])
def sns():
    msg_type = request.headers.get('x-amz-sns-message-type')
    if msg_type == 'SubscriptionConfirmation':
        return subscribe()
    elif msg_type == 'Notification':
        return save()

    else:
        abort(400)

def subscribe():
    try:
        j = request.get_json(force=True)
        urllib2.urlopen(j['SubscribeURL'])
        return "OK"

    except:
        print Exception.message
        abort(400)


@application.route('/getTweetNum',methods=['POST'])
def getTweetsNum():
    try:
        tweet = int(request.form['num'])
        global new_tweet,num_tweet
        if new_tweet:
            val = '%s New Tweets Available\nPlease Refresh to view' %num_tweet
            response = json.dumps({'return_code':1,'value':val})
            return response
        else:
            response = json.dumps({'return_code': 0, 'value': 'No New Tweets !!'})
            return response

    except Exception as e:
        print e.message
        abort(400)




if __name__ == '__main__':
    try:
        app.run()
    except Exception:
        print Exception.message
