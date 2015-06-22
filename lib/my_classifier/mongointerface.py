# -*- coding: utf-8 -*-
from pymongo import MongoClient
from datetime import datetime
import functools
import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import my_classifier.sample

import my_classifier

import json

# import for evaluation
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score

from my_classifier.sample import ensure_list

import copy

################################################
### query maker
################################################



def generate_event_id(operation,feature_type,option=None):
    array = [operation,feature_type]
    if option!=None:
        option = ensure_list(option)
        for o in option:
            array.append(str(o))
    return "::".join(array)


################################################
### decorator 
################################################
def access_history_log(func):
    @functools.wraps(func)
    def wrapper(db, feature_type, *args,**kwargs):
        result_json = func(db,feature_type, *args,**kwargs)
        if my_classifier.is_success(result_json):
            access_history = db['timestamps']
            event = result_json['event']
            time = datetime.now()
            #    print time
            event['time'] = time
            try:
                print event
                access_history.replace_one({'_id':event['_id']},event,True)
            except:
                return my_classifier.error_json(sys.exc_info()[1])
        return result_json
    return wrapper


# 単一のサンプルを扱う関数で，ブラウザに返す結果を生成する
def sample_treater(func):
    @functools.wraps(func)
    def wrapper(db,feature_type,sample,*args,**kwargs):
        result_json = func(db,feature_type,sample,*args,**kwargs)
        if my_classifier.is_success(result_json):            
            option = sample._id
            event_id = generate_event_id(func.__name__,feature_type,option)
            event = {'_id':event_id}
            result_json['event'] = event
        return result_json
    return wrapper

################################################
### sample collector
################################################
# MongDBから目的のサンプルを集める
def get_training_samples(db,feature_type, clustering = False, selector={}):
    query = selector
    if not clustering:
        query['ground_truth'] = {"$exists": True}
    return db[feature_type].find(query)


def get_any_samples(feature_type, group_all=[],selector={}):
        return get_training_samples(feature_type,True, selector)



################################################
### algorithm independent functions
################################################

@access_history_log
@sample_treater
def add(db, feature_type, sample):
    print "function: add"
    collection = db[feature_type]

    if collection.find({'_id':sample._id}).count()>0:
        return my_classifier.error_json("sample " + sample._id + " already exists.")
    
    try:
        collection.insert_one(sample.__dict__)
    except:
        return my_classifier.error_json(sys.exc_info()[0])
    return my_classifier.success_json()



@access_history_log
def clear_classifier(db, feature_type, data, algorithm):
    print "function: " + __name__
    if algorithm==None:
        return my_classifier.error_json('algorithm must be designated')


    clf_id = my_classifier.generate_clf_id(algorithm,feature_type,data)
    query = {'_id':clf_id}
    
    collection = db['classifiers']
    data_count = collection.find(query).count()
    if data_count==0:
        return my_classifier.error_json("No classifiers are hit.")
    
    try:
        db['classifiers'].remove(query)
    except:
        return my_classifier.error_json(sys.exc_info()[1])

    result = my_classifier.success_json()
    result['event'] = {'_id': generate_event_id('clear_classifier', feature_type, clf_id )}   
    return result



@access_history_log
def clear_samples(db,feature_type,data):
    print "in clear_samples"
    query = {}
    query = data['selector']
    collection = db[feature_type]
    data_count = collection.find(query).count()
    if data_count==0:
        return my_classifier.error_json("No samples are hit.")
    try:
        collection.remove(query)
    except:
        return my_classifier.error_json(sys.exc_info()[1])
    result = my_classifier.success_json()
    
    result['event'] = {'_id': generate_event_id('clear_samples',feature_type,json.dumps(query))}
    return result

######################
# band
######################
@access_history_log
def band(db,feature_type,data):
    print "function: band"
    if not data.has_key('group'):
        return my_classifier.error_json("'group' must be set.")
    group_name = data['group']
    
    selector = data['selector']
    
    collections = db[feature_type]

    samples = collections.find(selector)
    print samples
    if samples.count() == 0:
        return my_classifier.error_json("ERROR: no samples are hit.")
    for s in samples:
        groups = s['group']
        if not group_name in groups:
            groups = ensure_list(groups)
            groups.append(group_name)
            _id = s['_id']
            collections.update({"_id":_id},{"$set":{'group':groups}})
    result = my_classifier.success_json()
    result['event'] = {'_id':generate_event_id('band',feature_type,[group_name,json.dumps(selector)])}
    return result
    
######################
# disband
######################
@access_history_log
def disband(db,feature_type,data):
    print "function: disband"
    if not data.has_key('group'):
        return my_classifier.error_json("'group' must be set.")
    group_name = data['group']
    collections = db[feature_type]

    samples = collections.find({'group':{'$all':[group_name]}})
    if samples.count() == 0:
        return my_classifier.error_json("ERROR: no samples are hit.")
    for s in samples:
        groups = s['group']
        while group_name in groups:
            groups.remove(group_name)
        _id = s['_id']
        collections.update({"_id":_id},{"$set":{'group':groups}})
    result = my_classifier.success_json()
    result['event'] = {'_id':generate_event_id('disband',feature_type,group_name)}
    return result   

######################
# evaluate
######################
@access_history_log
def evaluate(db,feature_type, data,algorithm):
    print "function: evaluate"
        
    # class_name2idのために識別器のデータを呼ぶ
    clf_id = my_classifier.generate_clf_id(algorithm,feature_type,data)
    print "clf_id: " + clf_id
    print ""
    try:
        record = db["classifiers"].find_one({'_id':clf_id})
        if record == None:
            return my_classifier.error_json("No classifier was found.")
    except:
        return my_classifier.error_json(sys.exc_info()[1])
    print record

    name2id = record['class_name2id']
    y = []
    y_pred = []
    weights = []
        
    samples = db[feature_type].find({'likelihood.'+clf_id : {"$exists":True}})
    for s in samples:
        print s
        if not s['likelihood'].has_key(clf_id):
            continue
        y.append(name2id[s['ground_truth']])
        likelihood = dict(s['likelihood'][clf_id])
        pred_name = max([(v,k) for k,v in likelihood.items()])[1]
        y_pred.append(name2id[pred_name])
        weights.append(float(s['weight']))
        
    
    if not y:
        return my_classifier.error_json("ERROR: samples are not found.")

    result = my_classifier.success_json()

    result['event'] = {'_id':generate_event_id('evaluate', feature_type, clf_id)}

    id2name = record['class_id2name']
    result['class_list'] = [id2name[k] for k in sorted(id2name.keys())]

    # confution_matrix
    cm = confusion_matrix(y, y_pred)
    cm_json_searizable = []
    for line in cm:
        cm_json_searizable.append(line.tolist())
#    id2name = record['class_id2name']

    result['confusion_matrix'] = json.dumps(cm_json_searizable)

    print precision_score(y,y_pred,sample_weight=weights)
    print precision_score(y,y_pred)
    result['precision_score'] = precision_score(y,y_pred,sample_weight=weights)
    result['recall_score'] = recall_score(y,y_pred,sample_weight=weights)
    result['f1_score'] = f1_score(y,y_pred,sample_weight=weights)

    return result

if __name__ == '__main__':

    def create_test_sample():
        data = {'feature':[0,0,0], 'id':'test_sample', 'feature_type':'test_dim003', 'ground_truth':0}
        return my_classifier.Sample.Sample(data)
    
    mongo_client = MongoClient()
    db = mongo_client['test']
    sample = create_test_sample()
    result = add(db, sample)
    print result

