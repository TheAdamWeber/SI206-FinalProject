import praw
import requests
import secret_data
import json
import datetime
import sqlite3
from requests_oauthlib import OAuth1


client_id = secret_data.CLIENT_ID
client_secret = secret_data.CLIENT_SECRET
user_agent = secret_data.USER_AGENT

consumer_key = secret_data.TWITTER_CONSUMER_KEY
consumer_secret = secret_data.TWITTER_CONSUMER_SECRET
access_token = secret_data.TWITTER_ACCESS_KEY
access_secret = secret_data.TWITTER_ACCESS_SECRET


REDDIT_DB = 'reddit.db'


reddit = praw.Reddit(client_id=client_id,client_secret=client_secret,redirect_uri="http://localhost:5000/validate",user_agent=user_agent)
reddit_cache = 'reddit_cache.json'
#auth = OAuth1(client_id,client_secret,redirect_uri,user_agent)
#test = requests.get(reddit.auth.url(['identity'], '...', 'permanent')).text



url = 'https://api.twitter.com/1.1/account/verify_credentials.json'
auth = OAuth1(consumer_key, consumer_secret, access_token, access_secret)
requests.get(url, auth=auth)
CACHE_FNAME = 'twitter_cache.json'
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()

# if there was no file, no worries. There will be soon!
except:
    CACHE_DICTION = {}

def get_pop_score(tw):
    return int(tw.popularity_score)

def get_unique_key(baseurl, params):
    alphabetized_keys = sorted(params.keys())
    res = []
    for k in alphabetized_keys:
        res.append("{}-{}".format(k, params[k]))
    return baseurl + "_".join(res)

def make_request_using_cache(url, params, auth=None):
    #Get a unique url with parameters
    unique_ident = get_unique_key(url, params)

    ## first, look in the cache to see if we already have this data
    if unique_ident in CACHE_DICTION:
        #print("Getting cached data...")
        return CACHE_DICTION[unique_ident]

    ## if not, fetch the data afresh, add it to the cache,
    ## then write the cache to file
    else:
        #print("Making a request for new data...")
        # Make the request and cache the new data
        if (auth == None):
            resp = requests.get(url, params=params)
        else:
            resp = requests.get(url, params=params, auth=auth)
        CACHE_DICTION[unique_ident] = resp.text
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close() # Close the open file
        return CACHE_DICTION[unique_ident]


class Tweet:
    def __init__(self, tweet_dict_from_json):
        self.retweet_count = str(tweet_dict_from_json['retweet_count'])
        self.favorite_count = str(tweet_dict_from_json['favorite_count'])
        self.popularity_score = str(int(self.retweet_count)*2 + int(self.favorite_count)*3)
        self.is_retweet = tweet_dict_from_json['retweeted']
        self.user_name = tweet_dict_from_json['user']['screen_name']
        self.date = tweet_dict_from_json['created_at']
        self.id = str(tweet_dict_from_json['id'])
        self.text = tweet_dict_from_json['text']

def populate_tweets_for_post(post_title, post_id):
    url = 'https://api.twitter.com/1.1/search/tweets.json'
    params = {'q':post_title, 'count':'100'}

    dic = make_request_using_cache(url, params, auth)
    json_dump = json.dumps(json.loads(dic), indent=4)
    fw = open("tweet.json", "w")
    fw.write(json_dump)
    fw.close()

    data = json.loads(dic)['statuses']
    tweets = []
    for tw in data:
        tweets.append(Tweet(tw))
    tweets = [item for item in tweets if item.is_retweet != True]
    tweets.sort(key=get_pop_score, reverse=True)


    conn = sqlite3.connect(REDDIT_DB)
    cur=conn.cursor()
    query = 'DELETE FROM Tweets WHERE RedditId=?'
    insertion = (post_id,)

    cur.execute(query,insertion)

    for tw in tweets:
        insertion = (tw.id,tw.retweet_count,tw.favorite_count,tw.popularity_score,tw.user_name,tw.date,tw.text,post_id)
        statement = '''
            INSERT INTO "Tweets"
            VALUES (?,?,?,?,?,?,?,?)
        '''
        cur.execute(statement, insertion)

    conn.commit()
    conn.close()

    return

def get_tweet_data(post_id):
    conn = sqlite3.connect(REDDIT_DB)
    cur=conn.cursor()

    query = '''
        SELECT Text, User, Favorites, Retweets, Date
        FROM Tweets
        WHERE RedditId=?
        ORDER BY Favorites DESC
    '''

    insertion = (post_id,)

    cur.execute(query,insertion)

    data = cur.fetchall()
    conn.close()

    return data


def retrieve_data(cache,limit):

    subreddit = reddit.front.hot(limit=limit)

    lis = []

    if(cache):
        pass
    else:
        i = 0
        for submission in subreddit:
            if i == limit:
                break
            data = {}
            data["title"] = str(submission.title)
            data["score"] = submission.score
            data["id"] = submission.id
            data["url"] = submission.url
            data["subreddit"] = str(submission.subreddit)
            data["author"] = str(submission.author)
            data["date"] = str(datetime.datetime.fromtimestamp(submission.created))
            lis.append(data)
            i += 1


        with open(reddit_cache, 'w') as outfile:
            json.dump(lis, outfile, indent=4)

def init_dbs():
    conn = sqlite3.connect(REDDIT_DB)
    cur = conn.cursor()

    statement = '''
        DROP TABLE IF EXISTS 'Posts'
    '''

    cur.execute(statement)

    statement = '''
        DROP TABLE IF EXISTS 'Tweets'
    '''

    cur.execute(statement)

    conn.commit()

    statement = '''
       CREATE TABLE 'Posts' (
                'PostId' TEXT NOT NULL,
                'Title' TEXT,
                'Score' INTEGER,
                'Subreddit' TEXT,
                'Author' TEXT,
                'Link' TEXT,
                'Date' TEXT
        );
    '''

    cur.execute(statement)

    statement = '''
       CREATE TABLE 'Tweets' (
                'Id' TEXT NOT NULL,
                'Retweets' INTEGER,
                'Favorites' INTEGER,
                'Score' INTEGER,
                'User' TEXT,
                'Date' TEXT,
                'Text' TEXT,
                'RedditId' TEXT
        );
    '''

    cur.execute(statement)

    conn.commit()
    conn.close()


def populate_reddit_data(name):
    conn = sqlite3.connect(REDDIT_DB)
    cur=conn.cursor()
    query = 'DELETE FROM Posts'

    cur.execute(query)
    rfile = open(name)
    data = json.load(rfile)
    rfile.close()
    for item in data:
        insertion = (item['id'],item['title'],item['score'],item['subreddit'],item['author'],item['url'],item['date'])
        statement = '''
            INSERT INTO "Posts"
            VALUES (?,?,?,?,?,?,?)
        '''
        cur.execute(statement, insertion)

    conn.commit()
    conn.close()

def get_reddit_data(sort="score"):
    conn = sqlite3.connect(REDDIT_DB)
    cur=conn.cursor()
    query = ""
    if sort == "score":
        query = '''
            SELECT *
            FROM Posts
            ORDER BY Score DESC
        '''
    elif sort == "date":
        query = '''
            SELECT Date, Score
            FROM Posts
            ORDER BY Date ASC
        '''
    elif sort == "subreddit":
        query = '''
            SELECT Subreddit, AVG(Score)
            FROM Posts
            GROUP BY Subreddit
    '''
    elif sort == "postid":
        query = '''
            SELECT PostId
            FROM Posts
            ORDER BY Score DESC
        '''
    cur.execute(query)
    data = cur.fetchall()
    conn.close()

    return data

def vote(select, post_number):
    data = get_reddit_data("postid")
    post_id = data[post_number]
    post = reddit.submission(id=post_id)
    if select == 'up':
        post.upvote()
    else:
        post.downvote()
    return

