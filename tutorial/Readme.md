# Launch a server

- run following command @ terminal A

        %mongod

- run following command in serv4recog directory @ terminal B

        %python app.py

# Add a sample

 - run following command @ terminal C

        %wget -O - 'http://localhost:8080/ml/my_db/test_feature/add?json_data={"feature":[0.1,0.9],"class": "class001"}' | cat

 - Above command send HTTP GET request to server. The query orders the server to add a feature vector (0.1,0.9), whose class name is "class001".
 - You can send these commands via web browser, too. Just copy the above URL to address bar, and press return key.

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
    %wget -O - 'http://localhost:8080/ml/my_db/test_feature/svc/train?json_data={"option":{"kernel":"rbf"},"name":"tutorial"}' | cat

# Predict unknown sample
    %wget -O - 'http://localhost:8080/ml/my_db/test_feature/svc/predict?json_data={"feature":[0.2,0.8],"name":"tutorial"}' | cat
 
# Clear all the samples and the trained classifier
    %wget -O - 'http://localhost:8080/ml/my_db/test_feature/clear_samples' | cat
    %wget -O - 'http://localhost:8080/ml/my_db/test_feature/svc/clear_classifier?json_data={"name":"tutorial"}' | cat
