from flask import Flask, render_template, request, Markup
import model
import praw
from plotly.offline import plot
from plotly.graph_objs import Scatter

app = Flask(__name__)

@app.route('/')
def index():
    return '''
        <h1>reddit Frontpage Scraper</h1>
        <ul>
            <li><a href="/validate">Validate redit</li>
            <li><a href="/retrieve_data">Start Scraping</li>
        </ul>
    '''

@app.route('/validate')
def validate():
    return

@app.route('/retrieve_data', methods=['GET','POST'])
def retrieve_data():
    return render_template("retrieve_data.html")

@app.route('/results', methods=['GET','POST'])
def results():
    if request.method == 'POST':
        use_cache = bool(request.form['getdata'])
        model.retrieve_data(use_cache, 100)
        model.populate_reddit_data('cache.txt')
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
        print(post_number)
        r_data = model.get_reddit_data()
        reddit_data = r_data[post_number]
        reddit_id = reddit_data[0]
        reddit_title = reddit_data[1]

        print(reddit_id)
        print(reddit_title)

        model.populate_tweets_for_post(reddit_title, reddit_id)

        twitter_data = model.get_tweet_data(reddit_id)
    else:
        twitter_data = []

    return render_template('results_tweets_graph.html',twitterdata=twitter_data)

if __name__ == '__main__':
    model.init_dbs()
    app.run(debug=True)
