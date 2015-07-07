# Purpose of the function "class_remap"

class_remap is a function to remap ground_truth labels into other class names.
This is used typically for the case that the ground_truth label is given in a hierarchical manner. 
- i.e. "ground_truth":"animal/mammal/human" or "ground_truth":"animal/bird/pigion".

By remapping ground_truth label using regular expression syntax, you can train a classifier with any depth of the label.

# Prerequirement
- Add hirarchical classes
    python script/generate_samples.py animal/mammal/human [11.1,11.9] [0.5,0.5] 20
    python script/generate_samples.py animal/mammal/elephant [101.1,51.9] [0.5,0.5] 20
		python script/generate_samples.py animal/bird/pegion [1.1,0.3] [0.2,0.1] 20
    python script/generate_samples.py animal/bird/eagle [1.5,0.9] [0.2,0.2] 20

# Train classifier in mammal/bird level
- _http://localhost:8080/ml/my_db/test_feature/svc/train?json_data={"class_remap":{"mammal":".*/mammal/.*", "bird":".*/bird/.*"}, "name":"class_map_tutorial"}_

# Predict
- _http://localhost:8080/ml/my_db/test_feature/svc/predict?json_data={"feature":[12.6,12.1],"name":"class_map_tutorial"}_
