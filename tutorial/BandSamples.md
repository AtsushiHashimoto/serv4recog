# Prerequirement
- Add samples along to instruction in ./Readme.md before this tutorial.
- Add more classes
    python script/generate_samples.py class003 [11.1,11.9] [0.5,0.5] 40
    python script/generate_samples.py class004 [-11.1,-11.9] [0.5,0.5] 40

# Band samples at uploading
- http://localhost:8080/ml/my_db/test_feature/add?json_data={$SAMPLE, "group":"my_group_name"}

# Band uploaded samples
- http://localhost:8080/ml/my_db/test_feature/band?json_data={"group":"my_group_name",${SELECTOR}}
-- _e.g.) http://localhost:8080/ml/my_db/test_feature/band?json_data={"group":"my_group_name","selector":{"ground_truth":{"$in":["class001","class002"]}}}_
- You can choose the samples by 'ground_truth', other 'group' names, or 'id'. 
-- check out mongo operators: http://docs.mongodb.org/manual/reference/operator/query/

# How to select the banded features
- After banding samples by ${SELECTOR}, the selected samples can be called by following query.
-- _e.g.) http://localhost:8080/ml/my_db/test_feature/svc/train?json_data={"selector":{"group":{"$all":["my_group_name"]}}}_


# Disband samples
- http://localhost:8080/ml/my_db/test_feature/disband?json_data={"group":"my_group_name"}
