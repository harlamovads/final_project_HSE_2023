from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_auth_app import db
from flask_auth_app.models import Activity
from flask_login import login_required, current_user
import pandas as pd
from datetime import datetime
import spacy
from spacy import displacy
from sqlalchemy import func
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import io
import base64
import json
import requests

nlp = spacy.load("en_core_web_sm")

HTML_WRAPPER = """<div style="overflow-x: auto; border: 
1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem">{}</div>"""

main = Blueprint('main', __name__)


def dataframe(spacy_doc):
    list_list = []
    list_traits = []
    for token in spacy_doc:
        list_traits.append(token.text)
        list_traits.append(token.lemma_)
        list_traits.append(token.pos_)
        list_traits.append(token.tag_)
        print()
        if not token.is_stop:
            list_traits.append('No')
        if token.is_stop:
            list_traits.append('Yes')
        list_list.append(list_traits)
        list_traits = []

    df = pd.DataFrame(list_list, columns=['text', 'lemma', 'pos', 'tag', 'stop'], dtype=float)
    return df


API_URL = "https://api-inference.huggingface.co/models/Zlovoblachko/en_pipeline"
API_TOKEN = "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"
headers = {"Authorization": f"Bearer {API_TOKEN}", "X-Wait-For-Model": "true" }


def query(payload):
    data1 = json.dumps(payload)
    response = requests.request("POST", API_URL, headers=headers, data=data1)
    return json.loads(response.content.decode("utf-8"))


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/profile')
@login_required
def profile():
    da_data = {'daily_mean_len': db.session.query(Activity.date, func.avg(Activity.length)).filter(
                   Activity.user_id == current_user.id).group_by(Activity.date).all(),
               'glob_quantity': db.session.query(Activity).filter(Activity.user_id == current_user.id).count(),
               'glob_avg_len':
                   db.session.query(func.avg(Activity.length)).filter(Activity.user_id == current_user.id)[0][0],
               'daily_commit': db.session.query(Activity.date, func.count(Activity.sentence)).filter(
                   Activity.user_id == current_user.id).group_by(Activity.date).all(),
               'daily_mean_sense': db.session.query(Activity.date, func.avg(Activity.sense)).filter(
                   Activity.user_id == current_user.id).group_by(Activity.date).all(),
               'mean_sense': db.session.query(func.avg(Activity.sense)).filter(Activity.user_id == current_user.id)[0][0]}
    if not da_data['glob_avg_len'] is None:
        da_data['glob_avg_len'] = round(da_data['glob_avg_len'], 2)
    emotion = ""
    if da_data['mean_sense'] > 0.7:
        emotion = 'positive'
    if 0.3 < da_data['mean_sense'] < 0.7:
        emotion = 'neutral'
    if da_data['mean_sense'] < 0.3:
        emotion = 'negative'
    dates = []
    mean_data = []
    commit_data = []
    sense_data = []
    for i in da_data['daily_mean_len']:
        dates.append(i[0])
        mean_data.append(i[1])
    for j in da_data['daily_commit']:
        commit_data.append(j[1])
    for k in da_data['daily_mean_sense']:
        sense_data.append(k[1])
    fig, ax = plt.subplots(figsize=(5, 3), facecolor='lightskyblue',
                           layout='constrained')
    x = dates
    y = mean_data
    z = commit_data
    if len(x) == 1:
        ax.scatter(x, y, label="Mean sentence length (words)")
        ax.scatter(x, z, label="Number of daily commits")
    if len(x) > 1:
        ax.plot(x, y, label="Mean sentence length")
        ax.plot(x, z, label="Number of daily commits")
    fig.legend()
    pngimage = io.BytesIO()
    FigureCanvas(fig).print_png(pngimage)
    pngimageb64string = "data:image/png;base64,"
    pngimageb64string += base64.b64encode(pngimage.getvalue()).decode('utf8')
    fig1, ax1 = plt.subplots(figsize=(5, 3), facecolor='lightskyblue',
                           layout='constrained')
    x = dates
    a = sense_data
    if len(x) == 1:
        ax1.scatter(x, a, label="Average sentiment rate each day")
    if len(x) > 1:
        ax1.plot(x, a, label="Average sentiment rate each day")
    fig1.legend()
    pngimage1 = io.BytesIO()
    FigureCanvas(fig1).print_png(pngimage1)
    pngimage1b64string = "data:image/png;base64,"
    pngimage1b64string += base64.b64encode(pngimage1.getvalue()).decode('utf8')
    return render_template('profile.html', name=current_user.name,
                           da_data=da_data, image=pngimageb64string,
                           image1=pngimage1b64string, emote=emotion)


@main.route('/sentencing', methods=['POST', 'GET'])
@login_required
def sentence_creation():
    if request.method == 'POST':
        sentence1 = request.form.get('sentence')
        length = len((sentence1.split()))
        quer = {"inputs": sentence1.strip()}
        data2 = query(quer)
        print(data2)
        estimate = ""
        for jk in data2:
            estimate = jk[0]['score']
        sense = ""
        if estimate > 0.7:
            sense = 1
        if 0.7 > estimate > 0.3:
            sense = 0.5
        if estimate < 0.2:
            sense = 0
        new_entry = Activity(user_id=current_user.id,
                             date=str(datetime.now().day) + '.' +
                                  str(datetime.now().month) + '.' +
                                  str(datetime.now().year),
                             sentence=sentence1,
                             length=length,
                             sense=sense)
        db.session.add(new_entry)
        db.session.commit()
        session['sentence'] = sentence1
        session['sense1'] = sense
        return redirect(url_for('main.statistics'))
    return render_template("sentence_getter.html")


@main.route('/statistics', methods=['POST', 'GET'])
@login_required
def statistics():
    sentence2 = session.get('sentence', None)
    sense2 = session.get('sense1', None)
    doc = nlp(sentence2)
    display = ''
    if sense2 == 1:
        display = 'Positive'
    if sense2 == 0.5:
        display = 'Neutral'
    if sense2 == 0:
        display = 'Negative'
    options = {"compact": True}
    html = displacy.render(doc, style='dep', options=options)
    html = html.replace('\n\n', '\n')
    result = HTML_WRAPPER.format(html)
    datafr = dataframe(doc)
    return render_template('stata.html',
                           sentence=sentence2,
                           html=html,
                           result=result,
                           tables=[datafr.to_html(classes='data')],
                           titles=datafr.columns.values,
                           emotion=display)
