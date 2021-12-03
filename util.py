import pandas as pd
import numpy as np
import json
import requests
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from sklearn.metrics.pairwise import cosine_similarity

def clear_firebase_cache():
    requests.delete(url = 'https://project-3e24f-default-rtdb.firebaseio.com/.json')
    return

def get_info(df, path):
    result_dict = {}
    result_dict['file name'] = os.path.basename(path)
    result_dict['file size'] = str(int(os.path.getsize(path) / 1024**2)) + ' MB' 
    result_dict['number of attributes'] = len(df.columns)
    result_dict['number of rows'] = len(df)
    result_dict['attributes name'] = df.columns.values.tolist()
    return result_dict

def json_to_csv(review_path_in, business_path_in, test = True):
    '''convert the json file into the csv file we needed'''

    review_data = {"review_id":[],"business_id":[],"text":[],"stars":[]}
    with open(review_path_in, encoding="utf8") as fi:
        for line in fi:
            review = json.loads(line)
            review_data['review_id'].append(review['review_id'])
            review_data['business_id'].append(review['business_id'])
            review_data['text'].append(review['text'])
            review_data['stars'].append(review['stars'])
    review_df = pd.DataFrame(review_data)

    business_data = {"name":[],"business_id":[],"city":[],"categories":[], "address":[], "review_count":[], "hours":[]}
    with open(business_path_in, encoding="utf8") as f:
        for line in f:
            business = json.loads(line)
            business_data['name'].append(business['name'])
            business_data['business_id'].append(business['business_id'])
            business_data['city'].append(business['city'])
            business_data['categories'].append(business['categories'])
            business_data['address'].append(business['address'])
            business_data['review_count'].append(business['review_count'])
            business_data['hours'].append(business['hours'])
    business_df = pd.DataFrame(business_data)
    
    if test:
        test_r_df = review_df.head(1000)
        test_b_df = business_df[(business_df['business_id']).isin(test_r_df['business_id'])]
        requests.put(url = 'https://project-3e24f-default-rtdb.firebaseio.com/review.json', data = test_r_df.to_json(orient = 'records'))
        requests.put(url = 'https://project-3e24f-default-rtdb.firebaseio.com/business.json', data = test_b_df.to_json(orient = 'records'))
    else:
        requests.put(url = 'https://project-3e24f-default-rtdb.firebaseio.com/review.json', data = review_df.to_json())
        requests.put(url = 'https://project-3e24f-default-rtdb.firebaseio.com/business.json', data = business_df.to_json())
    
    
    requests.put(url = 'https://project-3e24f-default-rtdb.firebaseio.com/review_info.json', 
                 data = json.dumps(get_info(review_df, review_path_in)))
    requests.put(url = 'https://project-3e24f-default-rtdb.firebaseio.com/business_info.json',
                 data = json.dumps(get_info(business_df, business_path_in)))
              
    return

def preprocess_group_restaurant_review(review_df, business_df):
    restaurant_df = review_df[['text','stars','business_id']].groupby('business_id').agg({'text':list,
                                                                                          'stars':np.mean}
                                                                                        ).reset_index()
    restaurant_df.text = restaurant_df.text.apply(lambda t: "".join(re.sub(r'[^\w\s]',' ',str(t))).replace("\n"," "))
    return pd.merge(restaurant_df, business_df.reset_index(), on ='business_id')


def perform_tfidf(df):
    tf = TfidfVectorizer(analyzer='word', ngram_range=(1, 3), min_df=0.1, stop_words='english')
    tfidf_matrix = tf.fit_transform(df.text.apply(lambda x: x.lower()))
    cosine_sim = cosine_similarity(tfidf_matrix)
    rest_rest_df = pd.DataFrame(cosine_sim, columns=df.business_id, index=df.business_id)
    return rest_rest_df


def generate_n_dataframe(df, n):
    column = ['business_id']
    for i in range(n):
        column_name = 'Top_' + str(i)
        column.append(column_name)
    # top N recommended restaurant dataframe for all restaurants
    top_df = pd.DataFrame(columns = column)
    # iterate through all restaurants in the dataframe
    for i in df.index:
        ix = df.loc[:,i].to_numpy().argpartition(range(-1,-n,-1))
        high_recomm = df.columns[ix[-1:-(n+2):-1]]
        top_df = top_df.append(pd.Series(high_recomm.values, index = column),ignore_index=True)
    return top_df


def find_substring(record, query):
    res = 0
    for key, value in record.items():
        if query in key:
            res += value
    return res

def output_recommendation(rest, text, num):
    recomm_rest = []
    target_column = ['name','address','stars','review_count','categories','business_id']
    target_id_list = []
    index = 0
    for i in range(num):
        if index >= 5:
            break
        rank = 'Top_' + str(i)
        target_id = rest[rest.name == text][rank].value_counts().idxmax()
        if target_id in target_id_list:
            continue
        else:
            index += 1
            target_id_list.append(target_id)
            recomm_rest.append(rest[rest.business_id == target_id][target_column].values.tolist()[0])
    return recomm_rest
        
        