# About this project
Project Name: Server4recog
Verion:	      0.1
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

    http://localhost:8080/ml/my_db/feature_type/add?json_data=${SAMPLE-IN-JSON-FORMAT}

HTTP POST:
 
    http://localhost:8080/ml/my_db/feature_type/add
    

- json_data=$SAMPLE-IN-JSON-FORMAT
- ml      : fixed path name.
- my_db   : name of separated database for your application.
- svm_rbf : ignored for _Add_ and some other operations. For train/predict/evaluate operations, this parameter designate type of recognizer. (currently, only svm_rbf is available.)

- CAUTION: In your custome applications, '{' and ':' should be url-encoded!! Please check specification of the HTTP library used in your application.

### ${SAMPLE-IN-JSON-FORMAT}
sample has following parameters.

- feature: float array that contains feature vector
 - _ex) "feature":[0.1,0.9,0.3,0.7,0.5,0.5]_
- id: sample ID
 - _ex) "id":"sample00001"_
- class: teacher signal for this sample. (optional, but required as training sample.)
 - _ex) "class": "class001"_
- likelihood: recognition results (only in output)
 - _ex) "likelihood:{"svm_rbf::${SELECTOR}":{"class001":0.9, "class002":0.1}}_
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
    http://localhost:8080/ml/my_db/feature_type/svm_rbf/train?json_data={"selector":${SELECTOR}, "overwrite":${BOOL}
- overwrite: overwrite previously trained classifier if true (optional)

### ${BOOL}
true or false

## Predict
    http://localhost:8080/ml/my_db/feature_type/svm_rbf/predict?json_data=${SAMPLE-IN-JSON-FORMAT}

## Evaluate
    http://localhost:8080/ml/my_db/feature_type/svm_rbf/evaluate?json_data=$CLASSIFIER-IN-JSON-FORMAT

## Clear Samples
    http://localhost:8080/ml/my_db/feature_type/clear_samples?json_data={"feature_type":$FeatureType}

## Clear Classifier
    http://localhost:8080/ml/my_db/feature_type/svm_rbf/evaluate?json_data=$CLASSIFIER-IN-JSON-FORMAT

## Group
    http://localhost:8080/ml/my_db/feature_type/group?json_data={"selector":${SELECTOR}, "group":["selected_samples01"]}

# Contribution
We welocome new contributers. At first, please branch the project, edit it, and send us the editted branch!

