import unittest
import model
import sqlite3


rdb = 'reddit.db'

class TestDbs(unittest.TestCase):

    #Test DB Creation

    def testInitDb(self):

        model.init_dbs()

        conn = sqlite3.connect(rdb)
        cur = conn.cursor()

        query = "SELECT name FROM sqlite_master WHERE type='table' AND name='Posts'"

        cur.execute(query)

        self.assertEqual(cur.fetchone()[0], "Posts")

        query = "SELECT name FROM sqlite_master WHERE type='table' AND name='Tweets'"

        cur.execute(query)

        self.assertEqual(cur.fetchone()[0], "Tweets")

        conn.close()

    # Test query limits that are only enforced when not caching

    def testRedditLimit(self):

        model.retrieve_data(False, 100)
        model.populate_reddit_data(model.reddit_cache)
        data = model.get_reddit_data()

        self.assertEqual(len(data),100)

        model.retrieve_data(False, 150)
        model.populate_reddit_data(model.reddit_cache)
        data = model.get_reddit_data()

        self.assertEqual(len(data), 150)

        model.retrieve_data(False, 200)
        model.populate_reddit_data(model.reddit_cache)
        data = model.get_reddit_data()

        self.assertEqual(len(data),200)

    # Test caching reddit data from file and retrieving from DB

    def testRedditCache(self):

        model.retrieve_data(False, 100)
        model.populate_reddit_data(model.reddit_cache)
        data = model.get_reddit_data()

        self.assertEqual(len(data),100)


        model.retrieve_data(True, 200)
        model.populate_reddit_data(model.reddit_cache)
        data2 = model.get_reddit_data()

        self.assertEqual(len(data2),len(data))
        self.assertEqual(data2[0],data[0])
        self.assertEqual(data2[1],data[1])

        model.retrieve_data(False,101)
        model.populate_reddit_data(model.reddit_cache)
        data3 = model.get_reddit_data()

        self.assertNotEqual(len(data3),len(data))

    # Test DB querys to sort and retrieve data

    def testGetRedditData(self):

        model.retrieve_data(True, 100)
        model.populate_reddit_data(model.reddit_cache)
        data = model.get_reddit_data()
        data2 = model.get_reddit_data("score")

        self.assertEqual(data2[0],data[0])

        data3 = model.get_reddit_data("date")

        self.assertNotEqual(data3[0],data[0])

        data4 = model.get_reddit_data("subreddit")

        self.assertNotEqual(data4[0],data[0])

        data5 = model.get_reddit_data("postid")

        self.assertNotEqual(data5[0],data[0])

        self.assertEqual(len(data[0]),7)
        self.assertEqual(len(data2[0]),7)
        self.assertEqual(len(data3[0]),2)
        self.assertEqual(len(data4[0]),2)
        self.assertEqual(len(data5[0]),1)

    # Test if tweets are retrieved and sorted by favorites

    def testTweetData(self):
        rdata = model.get_reddit_data()
        post_id = rdata[0][0]
        post_title = rdata[0][1]

        model.populate_tweets_for_post(post_title, post_id)
        data = model.get_tweet_data(post_id)

        self.assertNotEqual(len(data),0)

        self.assertGreaterEqual(data[0][2],data[1][2])
        self.assertGreaterEqual(data[1][2],data[2][2])
        self.assertGreaterEqual(data[2][2],data[3][2])
        self.assertGreaterEqual(data[3][2],data[4][2])

        self.assertEqual(data[0][8],post_id)




unittest.main()
