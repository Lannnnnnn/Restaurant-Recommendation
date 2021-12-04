from flask import Flask, request, render_template, redirect, url_for, session, abort, flash, jsonify
import requests
from werkzeug.utils import secure_filename
import util
import os
import pandas as pd

app = Flask(__name__)
app.config['UPLOAD_PATH'] = 'static'
app.secret_key = os.urandom(24)
app.static_folder = 'static'

# link to the firebase
url = 'https://project-3e24f-default-rtdb.firebaseio.com/'

@app.route('/')
def index():
    return render_template('homepage.html')

# Read and Upload the user input data to the Firebase
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
        # clean the previous Firebase data storage record
        util.clear_firebase_cache()
        # data cleaning and store the data to Firebase
        util.json_to_csv(path['review_path'], path['business_path'])

        return render_template('upload.html')

    else:
        return redirect(url_for('index'))

# retreive the metadata information for the user input file and dataframe first 5 rows based on the city user chosen
@app.route("/information", methods = ['POST', "GET"])
def information():
    if request.method == "POST":
        # get the city name the user chosen
        city = request.form['city']
        # retrieve the data from the firebase
        r_if = requests.get(url = url + 'review_info.json').json()
        b_if = requests.get(url = url + 'business_info.json').json()
        business = requests.get(url = url + 'business.json?orderBy="city"&equalTo="'+str(city)+'"').json()
        review = requests.get(url = url + 'review.json').json()
        # store the metadata
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
        # convert the retrieved data to dataframe and filter out the business infomation in the chosen city
        city_business = pd.DataFrame.from_dict(business, orient="index")
        city_rest = city_business[(city_business.categories.str.contains('Restaurants')
        )| (city_business.categories.str.contains('Food'))].reset_index(drop = True)
        review_df = pd.json_normalize(review)
        city_review = review_df[review_df['business_id'].isin(city_rest['business_id'].tolist())].reset_index(drop = True)
        # group the text reivew by restaurant and upload the grouped information to the firebase  
        grouped_rest = util.preprocess_group_restaurant_review(city_review, city_rest)
        requests.put(url = url + 'grouped_df.json', data = grouped_rest.to_json(orient = 'records'))
        return render_template('information.html', r = r_res, r_df = city_review, b = b_res, b_df = city_rest)
    else:
        return render_template('upload.html')

# jump to the recommendation function
@app.route("/recommendation", methods = ['POST', 'GET'])
def recommendation():
    if request.method == 'POST':
        return redirect(url_for('update'))
    else:

        return redirect(url_for('information'))

# generate the N recommendation restaurants based on the user choice
@app.route("/update", methods = ['POST', 'GET'])
def update():
    if request.method == 'POST':
        # get the restaurant name and number of recommendations the user chosen
        text = request.form.get('querybox')
        rank = int(request.form.get('rank'))

        # retrieve the grouped dataframe from the firebase
        grouped_df = pd.json_normalize(requests.get(url = url + 'grouped_df.json').json())
        # run the tfidf algorithm on the data
        tfidf_df = util.perform_tfidf(grouped_df)
        feature_df = util.generate_n_dataframe(tfidf_df, rank)

        with_business_id = grouped_df[['business_id','stars','name']].merge(feature_df)
        all_info = grouped_df[['business_id','categories','review_count','address']].merge(with_business_id).drop_duplicates()
        # generate N top recommendations based on the tfidf results
        output = util.output_recommendation(all_info, text, rank)
        return jsonify({'result':'success', 'data': output})
    else:
        return render_template('recommendation.html')

if __name__ == "__main__":
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run() 
