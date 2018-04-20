from flask import Flask, render_template, request, Markup, redirect
import model
import praw
from plotly.offline import plot
from plotly.graph_objs import Scatter, Bar

app = Flask(__name__)

@app.route('/')
def index():
    reddit_user = ''
    try:
        reddit_user = str(model.reddit.user.me())
    except:
        pass
    return render_template("index.html", authurl = model.reddit.auth.url(['identity','vote','read'],'...','permanent'), reddituser = reddit_user)

@app.route('/validate')
def validate():
    code = request.args.get('code')
    model.reddit.auth.authorize(code)
    return redirect('/')

@app.route('/retrieve_data', methods=['GET','POST'])
def retrieve_data():
    return render_template("retrieve_data.html")

@app.route('/results', methods=['GET','POST'])
def results():
    if request.method == 'POST':
        use_cache = bool(int(request.form['getdata']))
        number_posts = int(request.form['numberposts'])
        print(number_posts)
        model.retrieve_data(use_cache, number_posts)
        model.populate_reddit_data(model.reddit_cache)
    return render_template("results.html")



@app.route('/results_reddit_table')
def results_reddit_table():


    data = model.get_reddit_data()
    return render_template("results_reddit_table.html",redditdata=data)

@app.route('/results_time_plot')
def results_time_plot():
    data = model.get_reddit_data("date")
    date = []
    score = []
    for d in data:
        date.append(d[0])
        score.append(d[1])

    plot_div = plot([Scatter(x=date, y=score)], output_type='div')

    return render_template('results_time_plot.html', line_plot=Markup(plot_div))

@app.route('/results_tweets', methods=['GET','POST'])
def results_tweets():
    data = model.get_reddit_data()

    return render_template('results_tweets.html',redditdata=data)

@app.route('/results_tweets_graph', methods=['GET','POST'])
def results_tweets_graph():
    twitter_data = []
    if request.method == 'POST':
        post_number = int(request.form['postnumber']) - 1
        r_data = model.get_reddit_data()
        reddit_data = r_data[post_number]
        reddit_id = reddit_data[0]
        reddit_title = reddit_data[1]


        model.populate_tweets_for_post(reddit_title, reddit_id)

        twitter_data = model.get_tweet_data(reddit_id)
    else:
        twitter_data = []

    return render_template('results_tweets_graph.html',twitterdata=twitter_data)

@app.route('/results_subreddits')
def results_subreddits():

    data = model.get_reddit_data("subreddit")
    subreddit = []
    score = []
    for d in data:
        subreddit.append(d[0])
        score.append(d[1])
    sorted_subreddit = [subreddit for _, subreddit in sorted(zip(score,subreddit), reverse=True)]
    sorted_score = sorted(score, reverse=True)

    plot_div = plot([Bar(x=sorted_subreddit, y=sorted_score)], output_type='div')

    return render_template('results_subreddits.html',bar_graph=Markup(plot_div))


if __name__ == '__main__':
    model.init_dbs()
    app.run(debug=True)
