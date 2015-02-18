#-*- coding:utf-8 -*-

from sample import Sample
import mongointerface
import json

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




ensure_list = mongointerface.ensure_list
def cleaning_sample_query(json_data):
	src_keys = ['group','class','id']
	tar_keys = ['group','class','_id']	
	if json_data.has_key('group'):
		json_data['group'] = ensure_list(json_data['group'])
	return cleaning_query(json_data,src_keys,tar_keys)



def check_sample_source(data):
	req_keys = ['id','feature_type','feature']
	for key in req_keys:
		if data.has_key(key):
			continue
		return error_json("sample must contain '%s'"%key)
	return success_json()



#############################################
# MAIN FUNCTiON
#############################################

def route(db, json_data_s,operation,algorithm=None):
	print "function: route"
	print json_data_s
	data = json.loads(json_data_s)
	if operation in {'train','predict','test'}:
		mod = __import__(algorithm+'.classifier', fromlist=['.'])

# test
	if operation == 'test':
		return functions[operation]()

# train
	elif operation=='train':
		return mod.__dict__[operation](db,data)

# clear_classifier
	elif operation=='clear_classifier':
		return mongointerface.clear_classifier(db,data,algorithm)

# clear_samples
	elif operation=='clear_samples':
		return mongointerface.clear_samples(db,data)

# group
	elif operation=='group':
		return mongointerface.group(db,data)

# evaluate
	elif operation=='evaluate':
		return mongointerface.evaluate(db,data,algorithm)

	# operations using sample
	else:
		check_result = check_sample_source(data)
		if not is_success(check_result):
			return check_result
		sample = Sample(data)

# add
		if operation == 'add':
			return mongointerface.add(db,sample)

# predict
		elif operation == 'predict':
			return mod.__dict__[operation](db,sample)

# unknown operations (error)
		else:
			return error_json('Error: unknown operation %s.' % operation)



#############################################
# DECORATOR
#############################################
def train_deco(algorithm):
	def recieve_func(func):
		@functools.wraps(func)
		def wrapper(db,data):
			# データを適当な形式にする
			if not data.has_key('feature_type'):
				return my_classifier.error_json("ERROR: feature_type must be designated")
			feature_type = data['feature_type']

			group = []
			if data.has_key('group'):
				group = ensure_list(data['group'])

				
			# クラスへの分類
			samples = mongointerface.get_training_samples(db, feature_type, False, group)
			if 1 >= samples.count():
				return error_json('Too few training samples for %s.'%feature_type)

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
			record = mongointerface.create_clf_query(algorithm,feature_type,group)
			event = {'_id':record['_id'] + "::train"}
			
			record['clf'] = pickle.dumps(clf)
			record['class_name2id'] = class_map
			class_map_inv = {str(v):k for k, v in class_map.items()}
			record['class_id2name'] = class_map_inv
			try:
				record = mongointerface.remove_mongo_operator(record)
				db["classifiers"].save(record)
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
		def wrapper(db,sample):
			# サンプルのグループを取ってくるだけ
			# Sample … (ft,_id,type,cls,group,likelihood,weight)
			print "function: predict"
			feature_type = sample.type
			group = sample.group
			print group

			## algorithmに依存する部分
			query = mongointerface.create_clf_query(algorithm,feature_type,group)

			# 予測部
			collection = db["classifiers"]
			
			try:
				record = collection.find_one(query)
			except:
				return error_json(sys.exc_info()[1])
			clf = pickle.loads(record['clf'])

			# algorithmに応じた処理(func)を行う
			likelihood_list = func(clf,sample)

			likelihood_dict = {}
			for i,l in enumerate(likelihood_list):
				key = record['class_id2name'][str(i)]
				likelihood_dict[key] = l

			## algorithmに依存する部分
			ll_id = mongointerface.create_clf_likelihood_marker(algorithm,group)
			
			# 予測結果をデータベースへ追加
			sample.likelihood[ll_id] = likelihood_dict
			result = success_json()
			result['event'] = {'clf_id':query['_id']}
			result['result'] = {'id':sample._id, 'likelihood':likelihood_dict}

			mongointerface.add(db,sample)
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
