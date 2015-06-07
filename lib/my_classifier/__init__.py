#-*- coding:utf-8 -*-

from sample import Sample
from sample import ensure_list
import mongointerface
import json
import sys
import functools

import pickle
import collections

################################################
### result dict. 
################################################
def error_json(message):
    return {'status':'error', 'message':message}

def success_json():
    return {'status':'success'}

def is_success(json):
    if json['status'] == 'success':
        return True
    return False




def check_sample_source(data):
    req_keys = ['feature']
    for key in req_keys:
        if data.has_key(key):
            continue
        return error_json("sample must contain '%s'"%key)
    return success_json()



#############################################
# MAIN FUNCTiON
#############################################

def route(db, json_data_s, operation, feature_type, algorithm=None):
    print "function: route"
    print "operation => " + operation
    print json_data_s
    data = json.loads(json_data_s)
        
    # train, predict, testではalgorithmに対応するモジュールをimportする
    if operation in {'train','predict','test'}:
        mod = __import__(algorithm+'.classifier', fromlist=['.'])

# train
    if operation=='train':
        return mod.__dict__[operation](db,feature_type,data)

# clear_classifier
    elif operation=='clear_classifier':
        return mongointerface.clear_classifier(db, feature_type, data, feature_type, algorithm)

# clear_samples
    elif operation=='clear_samples':
        return mongointerface.clear_samples(db, feature_type, feature_type, data)

# group
    elif operation=='group':
        return mongointerface.group(db, feature_type, data)

# evaluate
    elif operation=='evaluate':
        return mongointerface.evaluate(db, feature_type, data, algorithm)

    # operations using sample
    else:
        check_result = check_sample_source(data)
        if not is_success(check_result):
            return check_result
        sample = Sample(data)

# add
        if operation == 'add':
            return mongointerface.add(db,feature_type,sample)

# predict
        elif operation == 'predict':
            return mod.__dict__[operation](db, feature_type, data)
            
# unknown operations (error)
    return error_json('Error: unknown operation %s.' % operation)


# generate classifier's ID
def generate_clf_id(alg,feature_type,selector):
    id = feature_type + "::" + alg
    if bool(selector):
        print "generate_clf_id"
        print selector
        print json.dumps(selector)
        id = id + "::" + json.dumps(selector)
    return id
    

#############################################
# DECORATOR
#############################################
def train_deco(algorithm):
    def recieve_func(func):
        @functools.wraps(func)
        def wrapper(db,feature_type, data):
            # 訓練に使うサンプルのqueryを作る
            selector = {}
            if data.has_key('selector'):
                selector = data['selector']
            
            cls_id = generate_clf_id(algorithm,feature_type,selector)
            prev_cls = db["classifiers"].find({"_id":cls_id})
            overwrite = False
            if data.has_key("overwrite") and data["overwrite"]=="true":
                overwrite = True

            if prev_cls and not overwrite:
                return error_json("Classifier already exist. To overwrite it, set overwrite option to be true.")
                
                
            # クラスへの分類
            samples = db[feature_type].find(selector)
            if 1 >= samples.count():
                return error_json('Only %d samples are found.'%samples.count())
                
            x = [[]] * samples.count()
            y = [0] * samples.count()
            class_count = collections.defaultdict(int)

            for i,s in enumerate(samples):
                x[i] = s['ft']
                y[i] = s['cls']
                class_count[s['cls']] += 1

            class_list = sorted(class_count.keys())


            # クラスの「重み付け」
            class_map = {}
            class_weight = {}
            for i,cls in enumerate(class_list):
                class_map[cls] = i
                class_weight[i] = float(len(class_list) * (samples.count() - class_count[cls])) / float(samples.count())
                    
            for i in range(len(y)):
                y[i] = class_map[y[i]]


            # algorithmに応じた処理(func)を行う
            clf=func(x,y,class_weight)


            # 結果を保存
            ## algorithmに依存する部分
            record = {}
            record['_id'] = cls_id
            event = {'_id':"train::" + record['_id']}
            
            record['clf'] = pickle.dumps(clf)
            record['class_name2id'] = class_map
            class_map_inv = {str(v):k for k, v in class_map.items()}
            record['class_id2name'] = class_map_inv
            try:
                db["classifiers"].replace_one({"_id":cls_id},record,True)
            except:
                return error_json(sys.exc_info()[1])

            result = success_json()
            result['event'] = event
            return result
        return wrapper
    return recieve_func


def predict_deco(algorithm):
    def recieve_func(func):
        @functools.wraps(func)
        def wrapper(db,feature_type, data):
            # サンプルのグループを取ってくるだけ
            # Sample … (ft,_id,type,cls,group,likelihood,weight)
            print "function: predict"

            selector = {}
            if data.has_key('selector'):
                selector = data.pop('selector')
            sample = Sample(data)

            ## algorithmに依存する部分
            clf_id = generate_clf_id(algorithm,feature_type,selector)

            # 予測部
            collection = db["classifiers"]            
            
            try:
                record = collection.find_one({'_id':clf_id})
                if record == None:
                    return error_json("No classifier was found.")
                clf = pickle.loads(record['clf'])
            except:
                
                return error_json(sys.exc_info()[1])
            

            # algorithmに応じた処理(func)を行う
            likelihood_list = func(clf,sample)

            likelihood_dict = {}
            for i,l in enumerate(likelihood_list):
                key = record['class_id2name'][str(i)]
                likelihood_dict[key] = l


            ## algorithmに依存する部分
            clf_id = generate_clf_id(algorithm,feature_type,selector)
                        
            # 予測結果をデータベースへ追加
            sample.likelihood[clf_id] = likelihood_dict
            
            add_result = mongointerface.add(db,feature_type,sample)
            
            result = success_json()
            result['event'] = {'_id':"predict::"+clf_id+"::"+str(sample._id), 'sub_event':add_result}
            result['result'] = {'id':sample._id, 'likelihood':likelihood_dict}
            
            return result 
        return wrapper
    return recieve_func



#テスト用
if __name__ == '__main__':
    from pymongo import MongoClient

    mongo_client = MongoClient()
    db = mongo_client['test']

    returned_json = route(db, '{"test":"hoge"}','test','svm_rdf')
    print returned_json
