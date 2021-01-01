from random import randint

from flask import Flask, render_template, request, jsonify
import pandas as pd


from climatedb.analytics import create_article_df, groupby_newspaper, groupby_years_and_newspaper
from climatedb.registry import get_newspaper, registry

import pandas as pd

from climatedb.config import DBHOME
from climatedb.databases import Articles


def get_article(article_id, articles):
    return [a for a in articles if a['article_id'] == article_id][0]


def get_articles_from_newspaper(newspaper_id, articles):
    return [a for a in articles if a['newspaper_id'] == newspaper_id]


from itertools import chain
def get_all_articles():
    papers = ['articles/final/' + d.name for d in (DBHOME / 'articles/final').iterdir()]
    paper_dbs = [Articles(p) for p in papers]
    return list(chain(*[db.get() for db in paper_dbs]))


app = Flask("climate-news-db")

registry = pd.DataFrame(registry)
registry = registry.set_index("newspaper_id")


@app.route("/papers.json")
def paper_json():
    """groupby paper, calculate statistics"""
    articles = get_all_articles()
    df = create_article_df(articles)
    group = groupby_newspaper(df)
    group = group.set_index("newspaper_id")

    papers = pd.concat([group, registry], axis=1)
    papers.loc[:, "newspaper_id"] = papers.index
    papers = papers.sort_index()
    papers = papers.reset_index(drop=True)
    return papers.to_dict(orient="records")


@app.route("/years.json")
def year_json():
    """groupby paper and by year"""

    articles = get_all_articles()
    df = create_article_df(articles)
    return groupby_years_and_newspaper(df)


@app.route("/year-chart")
def year_chart():
    return render_template('year_chart.html')


@app.route("/")
def home():
    papers = paper_json()

    articles = get_all_articles()
    data = {
        "n_articles": len(articles),
        "articles": articles,
        "n_papers": len(papers)
    }
    return render_template("home.html", data=data, papers=papers)


@app.route("/random")
def show_random_article():

    articles = get_all_articles()
    idx = randint(0, len(articles) - 1)
    article = articles[idx]
    return render_template("article.html", article=article)


@app.route("/article")
def show_one_article():

    articles = get_all_articles()
    articles = get_all_articles()
    article_id = request.args.get("article_id")
    article = get_article(article_id, articles)
    return render_template("article.html", article=article)


@app.route("/logs")
def show_logs():
    toggle = request.args.get("toggle")
    if toggle is None:
        toggle = 'all'

    from climatedb.logger import load_logs
    logs = load_logs()
    if toggle == 'error':
        logs = [l for l in logs if 'error' in l['msg']]

    logs = logs[-16:]
    return render_template("logs.html", logs=logs, toggle=toggle)


@app.route("/newspaper")
def show_one_newspaper():
    newspaper = request.args.get("newspaper_id")
    articles = get_all_articles()
    articles = get_articles_from_newspaper(newspaper, articles)
    articles = pd.DataFrame(articles)
    articles = articles.sort_values('date_published', ascending=False)
    articles = articles.reset_index(drop=True)
    articles = articles.to_dict(orient="records")
    newspaper = get_newspaper(newspaper)
    return render_template("newspaper.html", newspaper=newspaper, articles=articles)


if __name__ == "__main__":
    app.run(debug=True)
