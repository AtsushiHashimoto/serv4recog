#-*- coding:utf-8 -*-

from sample import Sample
import mongointerface
import json
import sys
import functools

import pickle
import collections

# for cross_validation
import random

import re
import copy

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

def init_data(data):
    if not data.has_key('selector'):
        data['selector'] = {}
    if data.has_key('option'):
        # encode unicode to str.
        for key, val in data['option'].items():
            if type(val) is unicode:
                data['option'][key] = val.encode('utf-8')
    else:        
        data['option'] = {}
    if not data.has_key('class_remap'):
        data['class_remap'] = {}
        
    
#############################################
# MAIN FUNCTiON
#############################################

def route(db, json_data_s, operation, feature_type, algorithm=None):
    print "function: route"
    print "operation => " + operation
    print json_data_s
    data = json.loads(json_data_s)
    
    init_data(data)
            
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


def generate_group_name(header,i):
    return "%s_%02d" % (header,i)
# json_data format: {"selector":${SELECTOR},"option":#{OPTION}}
    
def merge_confusion_matrix(mat1,mat2):
    mat_new = []
    for j, array1 in enumerate(mat1):
        array2 = mat2[j]
        mat_new.append([])
        for i,val1 in enumerate(array1):
            val2 = array2[i]
            mat_new[j].append(val1+val2)
    return mat_new

def cross_validation(db, json_data_s, feature_type, algorithm, fold_num):
    print "function: cross_validation"
    data = json.loads(json_data_s)
    init_data(data)

    cv_group_head = "__cross_validation"    
    # disband all previously taged cross_validation_groups
    for i in range(0,fold_num):
        group_name = generate_group_name(cv_group_head, i)
        mongointerface.disband(db, feature_type, {'group': group_name})
    mongointerface.disband(db, feature_type, {'group': cv_group_head})
        
    collections = db[feature_type]
    selector = data['selector']
    data['selector']['ground_truth'] = {"$exists": True}
    samples = collections.find(selector)

    # group samples into N groups randomly

    samples_count = samples.count()
    if samples_count == 0:
        return error_json("ERROR: no samples are hit.")

    group_assignment = []
    remainder = samples_count % fold_num
    quotient = int(samples_count / fold_num)
    for i in range(0,fold_num):
        n = quotient
        if i < remainder:
            n = n+1
        print "group_count[%02d] = %d" % (i,n)
        group_assignment += [generate_group_name(cv_group_head, i)] * n
    random.shuffle(group_assignment)
                
    # grouping samples into N group
    for i in range(samples_count):
        s = samples[i]
        group_name = group_assignment[i]
        #print group_name

        groups = s['group']
        if not group_name in groups:
            groups = mongointerface.ensure_list(groups)
            groups.append(group_name)
            groups.append(cv_group_head)
            _id = s['_id']
            collections.update_one({"_id":_id},{"$set":{'group':groups}})

    mod = __import__(algorithm+'.classifier', fromlist=['.'])

    #print 'train and evaluation'
    # evaluate each group by trained classifiers    
    confusion_matrices = []
    # train, predict, and evaluate N classifiers
    for i in range(0,fold_num):
        ## train ##
        exclude_group = generate_group_name(cv_group_head, i)
        #print exclude_group
        _data = copy.deepcopy(data)
        _data['selector'] = {'group':{'$not':{'$all':[exclude_group]},'$all':[cv_group_head]},'ground_truth':{"$exists": True}}
        _data['overwrite'] = True
        _data['name'] = exclude_group
        #print _data
        result = mod.train(db,feature_type,_data)
        if result['status'] != 'success':
            return result
            
        ## predict ##
        selector = {'group':{'$all':[exclude_group]}}        
        group_samples = mongointerface.get_training_samples(db,feature_type,False,selector)
        for s in group_samples:
            result = mod.predict(db,feature_type, Sample(s), _data)
            if result['status'] != 'success':
                return result
        _data['selector'] = selector
        ## evaluate ##

        result = mongointerface.evaluate(db, feature_type, _data, algorithm)
        if result['status'] != 'success':
            return result
        confusion_matrices.append(result['confusion_matrix'])
    
    cmat = None
    for m in confusion_matrices:
        if bool(cmat):
            cmat = merge_confusion_matrix(cmat,json.loads(m))
        else:
            cmat = json.loads(m)
    result = success_json()
    result['confusion_matrix'] = cmat
    cls_id = generate_clf_id(algorithm,feature_type,data)
    result['event'] = {'_id':"cross_validation::" + cls_id}
    return result

# json_data format: {"selector":${SELECTOR},"option":#{OPTION}}
def leave_one_out(db, json_data_s, feature_type, algorithm):
    print "function: leave_one_out"
    print json_data_s
    data = json.loads(json_data_s)
    init_data(data)
        
    leave_one_out_clf_name = "__leave_one_out"    
    data['name'] = leave_one_out_clf_name
    
    collections = db[feature_type]
    selector = data['selector']
    data['selector']['ground_truth'] = {"$exists": True}
    samples = collections.find(selector)

    mod = __import__(algorithm+'.classifier', fromlist=['.'])

    for s in samples:
        ## train ##
        print s
        _data = copy.deepcopy(data)
        _data['selector'] = {'_id':{'$ne':s['_id']}}
        _data['overwrite'] = True
        _data['name'] = leave_one_out_clf_name
        # print _data
        print "train"
        result = mod.train(db,feature_type,_data)
        if result['status'] != 'success':
            return result
        print "predict"
        ## predict ##
        result = mod.predict(db,feature_type, Sample(s), _data)
        if result['status'] != 'success':
            return result

    
    print "evaluate"
    ## evaluate ##
    result = mongointerface.evaluate(db, feature_type, data, algorithm)
    if result['status'] != 'success':
        return result
    cls_id = generate_clf_id(algorithm,feature_type,data)
    result['event'] = {'_id':"leave_one_out::" + cls_id}
    return result


# generate classifier's ID
def generate_clf_id(alg,feature_type,data):
    id = feature_type + "::" + alg

    typ = None
    if data.has_key('name'):
        typ = type(data['name'])
    
    if typ is str or typ is unicode:
        id = id + "::" + data['name']
    else:
        if bool(data['selector']):
#           print "generate_clf_id"
#           print selector
#           print json.dumps(selector)
            id = id + "::" + json.dumps(data['selector'])
        if bool(data['option']):
            id = id + "::" + json.dumps(data['option'])
        if bool(data['class_remap']):
            id = id + "::" + json.dumps(data['class_remap'])
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
            # 学習用関数に渡すパラメタ
            option = data['option']          
            # クラスのパターンが記述されていれば，それを使う
            class_remap = data['class_remap']
            
            # 処理前に入力内容を記録
            record = {}
            if bool(selector):
                print "selector"
                print selector
                record['selector'] = copy.deepcopy(selector)
            if bool(option):
                print "option"
                print option
                record['option'] = copy.deepcopy(option)
            if bool(class_remap):
                record['class_remap'] = copy.deepcopy(class_remap)


            cls_id = generate_clf_id(algorithm,feature_type,data)
            print type(data['name'])
            print "classifier ID: %s"%cls_id

            prev_clf = db["classifiers"].find({"_id":cls_id})
            overwrite = False
            if data.has_key("overwrite") and data["overwrite"] in ["true",1,True,"True","TRUE"]:
                overwrite = True

            if prev_clf.count()>0 and not overwrite:
                return error_json("Classifier already exist. To overwrite it, set overwrite option to be true.")
                
                
            # クラスへの分類
            samples = []
            sample_count = 0
            if not class_remap:
                samples = mongointerface.get_training_samples(db,feature_type,False,selector)
                sample_count = samples.count()
            else:
                # class_remap毎にサンプルを集める
                for gt,pat in class_remap.items():
                    selector['ground_truth'] = re.compile(pat)
                    _samples = mongointerface.get_training_samples(db,feature_type,False,selector)
                    if 1>= _samples.count():
                        return error_json('No samples are hit by regular expression "%s"'%pat)
                    for s in _samples:
                        s['ground_truth'] = gt
                        samples.append(s)
                    sample_count += _samples.count()
            if 1 >= sample_count:
                return error_json('Only %d samples are hit as training samples.'%sample_count)

            # shuffle??            
            x = [[]] * sample_count
            y = [0] * sample_count
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
                #print i
                #print cls
                class_map[cls] = i
                class_weight[i] = float(len(class_list) * (sample_count - class_count[cls])) / float(sample_count)
                    
            #print class_map
            for i in range(len(y)):
                
                y[i] = class_map[y[i]]


            # algorithmに応じた処理(func)を行う
            clf=func(x,y,class_weight,option)


            # 結果を保存
            ## algorithmに依存する部分
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
            #print "function: predict"
            
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
                
            # selector等をチェックする
            if record.has_key('selector'):
                if data.has_key('selector') and record['selector'] != data['selector']:
                    return error_json('selector does not match to the trained condition.')
                if data.has_key('option') and record['option'] != data['option']:
                    return error_json('option does not match to the trained condition.')
                if data.has_key('class_remap') and record['class_remap'] != data['class_remap']:
                    return error_json('option does not match to the trained condition.')
                

            # algorithmに応じた処理(func)を行う
            likelihood_list = func(clf,sample)

            likelihood_dict = {}
            for i,l in enumerate(likelihood_list):
                key = record['class_id2name'][str(i)]
                likelihood_dict[key] = l

                        
            # 予測結果をデータベースへ追加
            sample.likelihood[clf_id] = likelihood_dict

            collections = db[feature_type]
            if collections.find_one(sample._id):
                collections.update_one({"_id":sample._id},{"$set":{'likelihood':sample.likelihood}})
                sub_result = {'update::%s'%sample._id}
            else:
                sub_result = mongointerface.add(db,feature_type,sample)
            
            result = success_json()
            result['event'] = {'_id':"predict::"+clf_id+"::"+str(sample._id), 'sub_event':sub_result}
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
