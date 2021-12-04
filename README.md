# DSCI-551-Project

#### Project topic:

For this project, I built the recommender system that allows users to upload the restaurant file and business file for analysis and make recommendations based on the restaurant they are interested in. The analyzing algorithm primarily focuses on the text reviews analysis through TF-IDF (term frequency-inverse document frequency).  And from the website the user could filter the city and number of recommendations based on their own choices.


#### Team Member

Shenghan Liu

#### Project Architecture

![alt text](https://github.com/Lannnnnnn/DSCI-551-Project/blob/main/static/architecture.png)



#### Project Implementation

1. Static: Save the JS and CSS for website front-end
2. Templates: All the html templates for the website
3. util: functions used in flask to solve the problem

## Before You Run:
* In order to use Yelp's academic dataset, you will need to go to their [Website](https://www.yelp.com/dataset) and agree to the Terms of Use Agreement before you download the dataset. 

#### Project Running Instruction

1. Upload the yelp_academic_dataset_business.json and yelp_academic_dataset_review.json File to the webstie (this might takes around 2 mins)
2. Choose the City interested in
3. Check the Restaurant Information and File Information
4. Choose the Restaurant Interested and Number of Recommendations
5. See the Recommendation Results
