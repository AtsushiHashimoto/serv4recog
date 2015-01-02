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


################################################
### query maker
################################################
def ensure_list(elem):
	if isinstance(elem,list):
		return elem
	else:
		return [elem]

def create_clf_likelihood_marker(alg,group):
	id = alg
	if group:
		id += "::" + "-".join(group)
	return id

def create_clf_query(alg,feature_type,group=[]):
	id = feature_type + "::" + create_clf_likelihood_marker(alg,group)
	
	hash = {'algoritm':alg,'feature_type':feature_type}
	group = ensure_list(group)
	if group:
		id += "::" + "-".join(group)		
		hash['group'] = {'$all':group}
	hash['_id'] = id
	return hash



################################################
### decorator 
################################################
def access_history_log(func):
	@functools.wraps(func)
	def wrapper(db,*args,**kwargs):
		result_json = func(db,*args,**kwargs)
		if my_classifier.is_success(result_json):
			access_history = db['timestamps']
			event = result_json['event']
			time = datetime.now()
			#	print time
			event['time'] = time
			try:
				access_history.save(event)
			except:
				return my_classifier.error_json(sys.exc_info()[1])
		return result_json
	return wrapper


def get_event_id_sample(sample,event_name, algorithm=None):
	temp = [sample.type]
	if sample.cls>=0:
		if isinstance(sample.cls,int):
			temp.append("%04d"%sample.cls)
		else:
			temp.append(sample.cls)
	if algorithm:
		temp.append(algorithm)
	temp.append(event_name)

	return "::".join(temp)

def sample_treater(func):
	@functools.wraps(func)
	def wrapper(db,sample,*args,**kwargs):
		result_json = func(db,sample,*args,**kwargs)
		if my_classifier.is_success(result_json):
			access_id = get_event_id_sample(sample,func.__name__)
			event = {'_id':access_id, 'cls':sample.cls, 'sample_id':sample._id}
			if sample.__dict__.has_key('cls'):
				event['cls'] = sample.cls
			if sample.group:
				event['group'] = sample.group
			result_json['event'] = event
		return result_json
	return wrapper

################################################
### sample collector
################################################
# MongDBから目的のサンプルを集める
def get_samples_query(feature_type,group=[]):
	query = {}
	# 指定されたgroup(複数の場合は全て)を含むsampleのみを選ぶ
	if group:
		query['group'] == {'$all':group}
	return query


def get_training_samples(db,feature_type, clustering = False, group = []):
	query = get_samples_query(feature_type,group)
	
	# 学習用サンプルなのでクラスラベルがないものは除外
	if not clustering:
		query['cls'] = {"$ne": None}
	
	return db[feature_type].find(query)

def get_predicted_samples(db,feature_type,algorithm,group=[]):
	query = get_samples_query(feature_type,group)
	
	l_key = create_clf_likelihood_marker(algorithm,group)
	query = {'likelihood':{'$exists':l_key}}#:{'$ne':None}}}
	#	print query
	return db[feature_type].find(query)


################################################
### algorithm independent functions
################################################

@access_history_log
@sample_treater
def add(db, sample):
	print "function: add"
	print sample
	collection = db[sample.type]
	try:
		collection.insert(sample.__dict__)
	except:
		return my_classifier.error_json(sys.exc_info()[0])
	return my_classifier.success_json()


def get_event_id_query(query,feature_type,name):
	array = [feature_type]
	for key in sorted(query.keys()):
		array.append(query[key])
	array.append(name)
	return "::".join(array)

@access_history_log
def clear_classifier(db, data, algorithm):
	print "function: " + __name__
	if algorithm==None:
		return my_classifier.error_json('algorithm must be designated')

	if not data.has_key['feature_type']:
		return my_classifier.error_json('feature_type must be designated.')
	
	query = my_classifier.cleaning_classifier_query(data,feature_type,algorithm)
	print query
	try:
		db.remove(query)
	except:
		return my_classifier.error_json(sys.exc_info()[0])
	result = my_classifier.success_json()
	result['event'] = query
	result['event']['_id'] = get_event_id_query(query,'clear_classifier')

	return result

@access_history_log
def clear_samples(db,data):
	query = my_classifier.cleaning_sample_query(data)
	#print query
	if not data.has_key('feature_type'):
		return my_classifier.error_json('feature_type must be designated.')
	feature_type = data['feature_type']
	collection = db[feature_type]
	try:
		collection.remove(query)
	except:
		return my_classifier.error_json(sys.exc_info()[1])
	result = my_classifier.success_json()
	result['event'] = query
	result['event']['_id'] = get_event_id_query(query,feature_type,'clear_samples')
	return result

def train(func):
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		pass		
	return wrapper

def predict(func):
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		pass		
	return wrapper



###########
# evaluate
@access_history_log
def evaluate(db,data,algorithm):
	if not data.has_key('feature_type'):
		return my_classifier.error_json("ERROR: feature_type must be designated")
	feature_type = data['feature_type']




	group = []
	if data.has_key('group'):
		group = my_classifier.ensure_list(data['group'])
	
	samples = get_predicted_samples(db, feature_type, algorithm, group)

	
	# class_name2idのために識別器のデータを呼ぶ
	query = my_classifier.mongointerface.create_clf_query(algorithm,feature_type,group)
	try:
		record = db["classifiers"].find_one(query)
	except:
		return my_classifier.error_json(sys.exc_info()[1])

	name2id = record['class_name2id']
	print name2id

	l_marker = create_clf_likelihood_marker(algorithm,group)

	y = []
	y_pred = []
	weights = []

	for s in samples:
		if not s['likelihood'].has_key(l_marker):
			continue
		y.append(name2id[s['cls']])
		likelihood = dict(s['likelihood'][l_marker])
		pred_name = max([(v,k) for k,v in likelihood.items()])[1]
		y_pred.append(name2id[pred_name])
		weights.append(float(s['weight']))
		
	
	if not y:
		return my_classifier.error_json("ERROR: samples are not found.")

	result = my_classifier.success_json()

	query = create_clf_query(algorithm,feature_type,group)
	result['event'] = {'_id':query['_id']}

	# confution_matrix
	cm = confusion_matrix(y, y_pred)
	cm_json_searizable = []
	for line in cm:
		cm_json_searizable.append(line.tolist())
#	id2name = record['class_id2name']

	result['confusion_matrix'] = json.dumps(cm_json_searizable)

	print precision_score(y,y_pred,sample_weight=weights)
	print precision_score(y,y_pred)
	result['precision_score'] = precision_score(y,y_pred,sample_weight=weights)
	result['recall_score'] = recall_score(y,y_pred,sample_weight=weights)
	result['f1_score'] = f1_score(y,y_pred,sample_weight=weights)

	return result

if __name__ == '__main__':

	def create_test_sample():
		data = {'feature':[0,0,0], 'id':'test_sample', 'feature_type':'test_dim003', 'class':0}
		return Sample.Sample(data)
	
	mongo_client = MongoClient()
	db = mongo_client['test']
	sample = create_test_sample()
	result = add(db, sample)
	print result

















