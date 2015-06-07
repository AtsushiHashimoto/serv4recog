# Launch a server

- run following command @ terminal A

        %mongod

- run following command in serv4recog directory @ terminal B

        %python app.py

# Add a sample

 - run following command @ terminal C

        %wget -O - 'http://localhost:8080/ml/test_db/svm_rbf/add?json_data={"feature":[0.1,0.9],"feature_type":"test_feature","id":"test001","class": "class001"}'

 - Above command send HTTP GET request to server. The query orders the server to add a feature vector (0.1,0.9), whose class name is "class001".
 - feature_type is a string which distinguished, for example, rgb histogram from hu moment.
 - id is a string which determine this sample feature.
 - You can add the sample via web browser, too. Just copy the above URL to address bar, and press return key.
 - CAUTION: you cannot add features of the same ID. From the second attempt, it will return 500 error.

## Check the added sample

- you can check the samples via mongo interface

        %mongo
        >use my_db
        >db.test_feature.find()[0]

## Add more samples to execute training.
    %python script/generate_samples.py class001 [0.1,0.9] [0.1,0.1] 39
    %python script/generate_samples.py class002 [-0.2,1.1] [0.1,0.1] 20
    %python script/generate_samples.py class002 [0.5,0.5] [0.1,0.1] 20

# Train Classifier
        %wget -O - 'http://localhost:8080/ml/test_db/svm_rbf/train?json_data={"feature_type":"test_feature"}'

# Predict unknown sample
        
 