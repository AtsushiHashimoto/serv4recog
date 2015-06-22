# About this project
Project Name: Server4recog
Verion:	      0.2
Git Repo.:    https://github.com/AtsushiHashimoto/serv4recog

# What is serv4recog?
1. A web service which provides pattern recognition interface through http GET/POST requests.
2. JSON format input/output
3. Group based sample management. This enable to treat several recognition tasks at the same server process.
4. String format class ID.

# Official Support OS
OSX 10.9

# Download
    % git clone https://github.com/AtsushiHashimoto/serv4recog.git

# Requirements
mongodb:			2.6.4
http://docs.mongodb.org/manual/tutorial/install-mongodb-on-os-x/

python:       2.7.8
http://docs.python-guide.org/en/latest/starting/install/osx/

python packages: execute following commands at the cloned directory.

    % pip install -r packages_requirements.txt

# Settings
rename 'myapp.conf.example' to 'myapp.conf' and edit the contents for your environment.

    %cp myapp.conf.example myapp.conf

# Execute
At the serv4recog directory on a terminal, start up mongod.

    % mongod --dbpath ./db

Then, start up the server on another terminal

    % python app.py

# Test
execute the test script.

    % python script/serv4recog_tester.py

If you got recognition result without error, all the instlation processes completed.
Congratulation!!

# Tutorial
 
- https://github.com/AtsushiHashimoto/serv4recog/blob/master/tutorial/Readme.md

# Protocol
## Add sample
HTTP GET:

    http://localhost:8080/ml/my_db/my_feature/add?json_data=${SAMPLE}

HTTP POST:
 
    http://localhost:8080/ml/my_db/my_feature/add
- json_data: parameters dumped as a json-format string. 
- ml      : fixed path name (you can not change).
- my_db   : name of database. You can use different name for each of your application.
- my_feature : name of feature_type. You can use any string for each type of feature vector. (e.g. rgb_histogram, hu_moment, SIFT, et al.)

- CAUTION: In your custome applications, '{' and ':' in URL string should be url-encoded!! Please check specification of the HTTP library used in your application.

### ${SAMPLE}
sample has following parameters.

- feature: float array that contains feature vector
 - _ex) "feature":[0.1,0.9,0.3,0.7,0.5,0.5]_
- id: sample ID
 - _ex) "id":"sample00001"_
- class: teacher signal for this sample. (optional, but required as training sample.)
 - _ex) "class": "class001"_
- likelihood: recognition results (only in output)
 - _ex) "likelihood:{"svc::${SELECTOR}":{"class001":0.9, "class002":0.1}}_
- group: group tag that is used in ${SELECTOR}
 - _ex) "group":["group01","test_samples"]_

### ${SELECTOR}
Selector limits samples involved in the calculation.

- id: limit samples by its ID.
 - _ex) {"$or":[{"id":"sample00001"},{"id":"sample00002"}]}_
- class: limit samples by its class
 - _ex) {"$or":[{"cls":"class001"},{"cls":"class002"}]}_
- group: limit samples by its group
 - _ex) {"group":{"$all":["group01"]}}"_

The format follows to pymongo. For more detail, please see online documentation
    http://docs.mongodb.org/manual/reference/operator/query/


## Train
    http://localhost:8080/ml/my_db/my_feature/svc/train?json_data={"selector":${SELECTOR}, "overwrite":${BOOL}, ${CLASSIFIER-PARAMS}}
- svc: name of classifier. currently, only svc is supported.
- overwrite: overwrite previously trained classifier if true (optional)

### ${CLASSIFIER-PARAMS}
${CLASSIFIER-PARAMS} has following parameters.

- selector: limit training samples. (optional)
- option: argument used in classifier training. (optional)
    http://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html
- name: Name of trained classifier data. This is used to identified trained classifier at prediction. (optional)

### ${BOOL}
true or false

### ${OPTION}
A hash identifying argment name and its value for training. For SVC, refer scikit-learn SVC
page
    http://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html

## Predict
    http://localhost:8080/ml/my_db/my_feature/svc/predict?json_data={${SAMPLE}, ${CLASSIFIER-PARAMS}}

## Evaluate
    http://localhost:8080/ml/my_db/my_feature/svc/evaluate?json_data=${CLASSIFIER-PARAMS}

## Clear Samples
    http://localhost:8080/ml/my_db/my_feature/clear_samples?json_data={"selector":${SELECTOR}}

## Clear Classifier
    http://localhost:8080/ml/my_db/my_feature/classifier/evaluate?json_data=$CLASSIFIER-PARAMS

## Group
    http://localhost:8080/ml/my_db/my_feature/group?json_data={"selector":${SELECTOR}, "group":["selected_samples01"]}

# Contribution
We welocome new contributers. At first, please branch the project, edit it, and send us the editted branch!

