from flask import Flask, request, render_template, redirect, url_for, session, abort, flash, jsonify
import requests
from werkzeug.utils import secure_filename
import sys
import test
import os
import pandas as pd

app = Flask(__name__)
app.config['UPLOAD_PATH'] = 'static'
app.secret_key = os.urandom(24)
app.static_folder = 'static'

url = 'https://project-3e24f-default-rtdb.firebaseio.com/'

@app.route('/')
def index():
    return render_template('homepage.html')

#Takes in the query, location, and food/restaurant button
@app.route('/upload', methods=['POST', 'GET'])
def upload():
    if request.method == "POST":
        path = {}
        for uploaded_file in request.files.getlist('file'):
            filename = secure_filename(uploaded_file.filename)
            if filename != '':
                temp_path = os.path.join(app.config['UPLOAD_PATH'], filename)
            uploaded_file.save(temp_path)
            if 'review' in filename:
                path['review_path'] = temp_path
                session['r_name'] = filename
            elif 'business' in filename:
                path['business_path'] = temp_path
                session['b_name'] = filename
            else:
                abort(400)
        #test.clear_firebase_cache()
        #test.json_to_csv(path['review_path'], path['business_path'])

        return render_template('upload.html')

    else:
        return redirect(url_for('index'))


@app.route("/information", methods = ['POST', "GET"])
def information():
    if request.method == "POST":
        city = request.form['city']
        r_if = requests.get(url = url + 'review_info.json').json()
        b_if = requests.get(url = url + 'business_info.json').json()
        b_res = [b_if['file name'],
                b_if['file size'],
                b_if['number of attributes'],
                b_if['attributes name'],
                b_if['number of rows']]

        r_res = [r_if['file name'],
                 r_if['file size'],
                 r_if['number of attributes'],
                 r_if['attributes name'],
                 r_if['number of rows']]
            
        business = requests.get(url = url + 'business.json?orderBy="city"&equalTo="'+str(city)+'"').json()
        review = requests.get(url = url + 'review.json').json()

        city_business = pd.DataFrame.from_dict(business, orient="index")
        city_rest = city_business[(city_business.categories.str.contains('Restaurants'))| (city_business.categories.str.contains('Food'))]
        review_df = pd.json_normalize(review)
        city_review = review_df[review_df['business_id'].isin(city_rest['business_id'].tolist())]

        grouped_rest = test.preprocess_group_restaurant_review(city_review, city_rest)
        requests.put(url = url + 'grouped_df.json', data = grouped_rest.to_json(orient = 'records'))
        return render_template('information.html', r = r_res, r_df = city_review, b = b_res, b_df = city_rest)
    else:
        return render_template('upload.html')

@app.route("/result", methods = ['POST', 'GET'])
def result():
    if request.method == 'POST':
        if request.form['submit'] == 'Go To Recommendation Page':
            return render_template('result.html')
        else:
            text = request.form.get('querytext')
            rank = request.form.get('num')
            print('Text is' + text, file = sys.stderr)
            print('Number is' + str(rank), file = sys.stderr)

            grouped_df = pd.json_normalize(requests.get(url = url + 'grouped_df.json').json())
            tfidf_df = test.perform_tfidf(grouped_df)
            feature_df = test.generate_n_dataframe(tfidf_df, rank)

            output = test.output_recommendation(feature_df, text, rank)
            return jsonify({'result':'success', 'data': output})
    return

@app.route("/update", methods = ['POST'])
def update():
    if request.method == 'POST':
        text = request.form.get('querybox')
        rank = int(request.form.get('rank'))
        print('Text is' + str(text), file = sys.stderr)
        print('Number is' + str(rank), file = sys.stderr)

        grouped_df = pd.json_normalize(requests.get(url = url + 'grouped_df.json').json())
        tfidf_df = test.perform_tfidf(grouped_df)
        feature_df = test.generate_n_dataframe(tfidf_df, rank)

        with_business_id = grouped_df[['business_id','stars','name']].merge(feature_df)
        all_info = grouped_df[['business_id','categories','review_count','address']].merge(with_business_id).drop_duplicates()

        output = test.output_recommendation(all_info, text, rank)
        return jsonify({'result':'success', 'data': output})
    else:
        return render_template('result.html')

if __name__ == "__main__":
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run() 
