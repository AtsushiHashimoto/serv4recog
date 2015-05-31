# About this project
Project Name: Server4recog
Verion:	      0.1
Git Repo.:    https://github.com/AtsushiHashimoto/server4recog

# What is serv4recog?
1. A web service which provides pattern recognition interface through http GET/POST requests.
2. JSON format input/output
3. Group based sample management. This enable to treat several recognition tasks at the same server process.
4. String format class ID.

# Official Support OS
OSX 10.9

# Download
    % git clone https://github.com/AtsushiHashimoto/server4recog.git

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

## Add sample
HTTP GET:

    http://localhost:8080/ml/my_db/svm_rbf/add?json_data=${SAMPLE-IN-JSON-FORMAT}

HTTP POST:
 
    http://localhost:8080/ml/my_db/svm_rbf/add
    

- json_data=$SAMPLE-IN-JSON-FORMAT
- ml      : fixed path name.
- my_db   : name of separated database for your application.
- svm_rbf : ignored for _Add_ and some other operations. For train/predict/evaluate operations, this parameter designate type of recognizer. (currently, only svm_rbf is available.)

- CAUTION: In your custome applications, '{' and ':' should be url-encoded!! Please check specification of the HTTP library used in your application.

### ${SAMPLE-IN-JSON-FORMAT}
sample has following parameters.

- feature: float array that contains feature vector
 - _ex) {"feature":[0.1,0.9,0.3,0.7,0.5,0.5]}_
- feature_type: the name of the above feature's type.
 - _ex) {"feature_type":"histogram_rgb_2bins_concatenate"}_
- id: sample ID
 - _ex) {"id":"sample00001"}_
- class: teacher signal for this sample. (optional, but required as training sample.)
 - _ex) {"class": "class001"}_
- group: characterize samples to grouping. (optional)
 - _ex) {"group":["pca","target-group"]}
 - ("pca" suppose to group all samples whose feature are filtered by PCA process.)
- likelihood: recognition results (only in output)
 - _ex) {"svm_rbf::target-group":{"class001":0.9, "class002":0.1}}_

## Train
    http://localhost:8080/ml/my_db/svm_rbf/train?json_data=$CLASSIFIER-IN-JSON-FORMAT

### ${CLASSIFIER-IN-JSON-FORMAT}
classifier has following parameters.
- feature_type: target feature type of samples.
- force: force to overwrite a trained classifier if exists. (currently, always true.)
- group: target sample groups (optional).
 - _ex) {'feature_type':feature\_type, 'multi':multi, 'force':force, 'group':group}

## Predict
    http://localhost:8080/ml/my_db/svm_rbf/predict?json_data=${SAMPLE-IN-JSON-FORMAT}

## Evaluate
    http://localhost:8080/ml/my_db/svm_rbf/evaluate?json_data=$CLASSIFIER-IN-JSON-FORMAT

## Clear Samples
    http://localhost:8080/ml/my_db/svm_rbf/clear_sample?json_data=$CLASSIFIER-IN-JSON-FORMAT

## Clear Classifier
    http://localhost:8080/ml/my_db/svm_rbf/evaluate?json_data=$CLASSIFIER-IN-JSON-FORMAT

## Group
    http://localhost:8080/ml/my_db/svm_rbf/group?json_data=${GROUP_MEMBERS}

### ${GROUP_MEMBERS}
- group_name: name of target group
- feature_type: target feature type of samples.
- class_list: a list of (new) classes that are grouped into _group\_name_ the group.
- _ex) {"group\_name":"target-group","class_list":["class001","class002","class003"]}_


# Contribution
We welocome new contributers. At first, please branch the project, edit it, and send us the editted branch!

