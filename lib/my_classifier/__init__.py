#-*- coding:utf-8 -*-

from sample import Sample
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
    
    if not data.has_key('selector'):
        data['selector'] = {}
    if data.has_key('option'):
        # encode unicode to str.
        for key, val in data['option'].items():
            if type(val) is unicode:
                print key
                print val
                data['option'][key] = val.encode('utf-8')
    else:        
        data['option'] = {}
        
    # train, predict, testではalgorithmに対応するモジュールをimportする
    if operation in {'train','predict','test'}:
        mod = __import__(algorithm+'.classifier', fromlist=['.'])

# train
    if operation=='train':
        return mod.__dict__[operation](db,feature_type,data)

# clear_classifier
    elif operation=='clear_classifier':
        return mongointerface.clear_classifier(db, feature_type, data, algorithm)

# clear_samples
    elif operation=='clear_samples':
        return mongointerface.clear_samples(db, feature_type, data)

# band
    elif operation=='band':
        return mongointerface.band(db, feature_type, data)

# disband
    elif operation=='disband':
        return mongointerface.disband(db, feature_type, data)

# evaluate
    elif operation=='evaluate':
        return mongointerface.evaluate(db, feature_type, data, algorithm)

    # operations using sample
    else:
        check_result = check_sample_source(data)
        if not is_success(check_result):
            return check_result

        # generate sample ID automatically (can be collapse if several samples add at once)
        if not data.has_key('id'):
            data['id'] = "sample_" +  "%012d" % db[feature_type].find().count()

        sample = Sample(data)

# add
        if operation == 'add':
            return mongointerface.add(db,feature_type,sample)

# predict
        elif operation == 'predict':
            return mod.__dict__[operation](db, feature_type, sample, data)
                        
# unknown operations (error)
    return error_json('Error: unknown operation %s.' % operation)


# json_data format: {"selector":${SELECTOR},"option":#{OPTION}}
def cross_validation(db, json_data_s, feature_type, algorithm, fold_num):
    print "function: cross_validation"
    print json_data_s
    data = json.loads(json_data_s)
    
    if not data.has_key('selector'):
        data['selector'] = {}
    if data.has_key('option'):
        # encode unicode to str.
        for key, val in data['option'].items():
            if type(val) is unicode:
                print key
                print val
                data['option'][key] = val.encode('utf-8')            
    else:        
        data['option'] = {}


    cv_group_head = "__cross_validation"    
    # disband all previously taged cross_validation_groups
    for i in range(0,fold_num):
        group_name = "%s_%02d" % (cv_group_head, i)
        mongointerface.disband(db, feature_type, {'group': group_name})
    mongointerface.disband(db, feature_type, {'group': cv_group_head})
        
    collections = db[feature_type]
    samples = collections.find(data['selector'])

    # group samples into N groups randomly

    samples_count = samples.count()
    if samples_count == 0:
        return error_json("ERROR: no samples are hit.")

    group_assignment = []
    group_num = float(samples_count)/fold_num
    for i in range(0,fold_num):
        group_assignment += ["%s_%s"%(cv_group_head, i)] * (int((i+1)*group_num) - int(i*group_num))
    
    random.shuffle(group_assignment)
            
            
    # grouping samples into N group
    for i, s in enumerate(samples):
        group_name = group_assignment[i]
        groups = s['group']
        if not group_name in groups:
            groups = mongointerface.ensure_list(groups)
            groups.append(group_name)
            groups.append(cv_group_head)
            _id = s['_id']
            collections.update_one({"_id":_id},{"$set":{'group':groups}})

    mod = __import__(algorithm+'.classifier', fromlist=['.'])

    print 'train'
    # train N classifiers
    for i in range(0,fold_num):
        exclude_group = "%s%s"%(cv_group_head, i)
        _data = copy.deepcopy(data)
        _data['selector'] = {'group':{'$not':{'$all':[exclude_group]},'$all':[cv_group_head]}}
        _data['overwrite'] = True
        _data['name'] = exclude_group
        print _data
        result = mod.train(db,feature_type,_data)
        if result['status'] != 'success':
            return result

    # evaluate each group by trained classifiers    
    evaluate_results = []

# json_data format: {"selector":${SELECTOR},"option":#{OPTION}}
def leave_one_out(db, json_data_s, feature_type, algorithm):
    print "function: leave_one_out"
    print json_data_s
    data = json.loads(json_data_s)
    
    if not data.has_key('selector'):
        data['selector'] = {}
    if data.has_key('option'):
        # encode unicode to str.
        for key, val in data['option'].items():
            if type(val) is unicode:
                print key
                print val
                data['option'][key] = val.encode('utf-8')            
    else:        
        data['option'] = {}
        
    leave_one_out_clf_name = "__leave_one_out"    
            
    collections = db[feature_type]
    samples = collections.find(data['selector'])

    for s in samples:
        _data = copy.deepcopy(data)
        _data['selector'] = {'_id':{'$ne':s['_id']}}
        _data['overwrite'] = True
        _data['name'] = leave_one_out_clf_name
        print _data
        result = mod.train(db,feature_type,_data)
        if result['status'] != 'success':
            return result
    

# generate classifier's ID
def generate_clf_id(alg,feature_type,data):
    id = feature_type + "::" + alg
    if data.has_key('name') and (type(data['name']) is str):
        id = id + "::" + data['name']
    else:
        if bool(data['selector']):
#           print "generate_clf_id"
#           print selector
#           print json.dumps(selector)
            id = id + "::" + json.dumps(data['selector'])
        if bool(data['option']):
            id = id + "::" + json.dumps(data['option'])
    return id
    

#############################################
# DECORATOR
#############################################
def train_deco(algorithm):
    def recieve_func(func):
        @functools.wraps(func)
        def wrapper(db,feature_type, data):
            # 訓練に使うサンプルのqueryを作る
            selector = data['selector']
            option = data['option']

            cls_id = generate_clf_id(algorithm,feature_type,data)
                
            prev_clf = db["classifiers"].find({"_id":cls_id})
            overwrite = False
            if data.has_key("overwrite") and data["overwrite"] in ["true",1,True,"True","TRUE"]:
                overwrite = True

            if prev_clf.count()>0 and not overwrite:
                return error_json("Classifier already exist. To overwrite it, set overwrite option to be true.")
                
                
            # クラスへの分類
            samples = mongointerface.get_training_samples(db,feature_type,False,selector)
            if 1 >= samples.count():
                return error_json('Only %d samples are hit as training samples.'%samples.count())
                
            x = [[]] * samples.count()
            y = [0] * samples.count()
            class_count = collections.defaultdict(int)

            for i,s in enumerate(samples):
                x[i] = s['ft']
                y[i] = s['ground_truth']
                class_count[s['ground_truth']] += 1

            class_list = sorted(class_count.keys())


            # クラスの「重み付け」
            class_map = {}
            class_weight = {}
            for i,cls in enumerate(class_list):
                print i
                print cls
                class_map[cls] = i
                class_weight[i] = float(len(class_list) * (samples.count() - class_count[cls])) / float(samples.count())
                    
            print class_map
            for i in range(len(y)):
                
                y[i] = class_map[y[i]]


            # algorithmに応じた処理(func)を行う
            clf=func(x,y,class_weight,option)


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
        def wrapper(db,feature_type, sample, data):
            # サンプルのグループを取ってくるだけ
            # Sample … (ft,_id,type,cls,group,likelihood,weight)
            print "function: predict"
            
            clf_id = generate_clf_id(algorithm,feature_type,data) 

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
