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
	group = ensure_list(group)
	id = feature_type + "::" + create_clf_likelihood_marker(alg,group)
	
	hash = {'algorithm':alg,'feature_type':feature_type}
	if group:
		hash['group'] = group #{'$all':group}
	hash['_id'] = id
	return hash

def get_event_id(query,feature_type,event_name):
	array = [feature_type]
	for key in sorted(query.keys()):
		if isinstance(query[key],list):
			array.append("-".join(query[key]))
		else:
			array.append(query[key])
	array.append(event_name)
	return "::".join(array)

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


##########################
### query cleaner
##########################

def remove_mongo_operator(hash):
	#{foo: {$ne:{$all:{hoge:huga}}}}
	for key1, val1 in hash.items():
		#key1 = foo,  val1 = {$ne:{$all:{hoge:huga}}}
		if not isinstance(val1,dict):
			continue
		
		for key2,val2 in val1.items():
			# key2 = $ne, val2 = {$all:{hoge:huga}}
			if not key2[0] == '$':
				continue
			# val1 must be single key dict.
			if len(val1.keys()) > 1:
				return hash
			
			if isinstance(val2,dict):
				temp = {key1: val2}
				# {foo, {$all:{hoge:huga}}}
				remove_mongo_operator(temp)
				# {foo, {hoge:huga}}
				hash[key1] = temp
			else:
				hash[key1] = val2
	return hash


def cleaning_query(data,src_keys,tar_keys=None, required_keys=[]):
	if tar_keys==None:
		tar_keys = src_keys
	query = {}
	for skey,tkey in zip(src_keys,tar_keys):
		if data.has_key(skey):
			if isinstance(data[skey],list):
				query[tkey] = {'$all':data[skey]}
			else:
				query[tkey] = data[skey]	
		elif skey in required_keys:
			return None
	return query

def cleaning_clf_query(json_data,algorithm):
	src_keys = ['feature_type','group']
	tar_keys = ['feature_type','group']
	
	if json_data.has_key('group'):
		json_data['group'] = ensure_list(json_data['group'])
	
	query = cleaning_query(json_data,src_keys,tar_keys)
	if None == query:
		return None
	query['algorithm'] = algorithm
	return query




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
def generate_samples_query(group=[]):
	query = {}
	# 指定されたgroup(複数の場合は全て)を含むsampleのみを選ぶ
	if group:
		query['group'] = {'$all':group}
	return query


def generate_training_samples_query(clustering=False, group=[]):
	query = generate_samples_query(group)
	
	# clustering==False: 教師あり学習用のサンプル
	# → クラスラベルがないものは除外
	if not clustering:
		query['cls'] = {"$ne": None}
	return query


def generate_any_saples_query(group=[]):
	return generate_training_samples_query(True, group)


def get_training_samples(db,feature_type, clustering = False, group = []):
	query = generate_training_samples_query(clustering, group)
	return db[feature_type].find(query)


def get_any_samples(feature_type, group=[]):
	return get_training_samples(featur_type,True, group)


def get_predicted_samples(db,feature_type,algorithm,group=[]):
	query = generate_samples_query(group)
	
	l_key = create_clf_likelihood_marker(algorithm,group)
	query = {'likelihood.'+l_key:{"$exists":True}}#:{'$ne':None}}}
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



@access_history_log
def clear_classifier(db, data, algorithm):
	print "function: " + __name__
	if algorithm==None:
		return my_classifier.error_json('algorithm must be designated')

	if not data.has_key('feature_type'):
		return my_classifier.error_json('feature_type must be designated.')

	feature_type = data['feature_type']
	query = cleaning_clf_query(data,algorithm)
	print query
	try:
		db['classifiers'].remove(query)
	except:
		return my_classifier.error_json(sys.exc_info()[1])

	query = remove_mongo_operator(query)
	result = my_classifier.success_json()
	result['event'] = query
	result['event']['_id'] = get_event_id(query,feature_type,'clear_classifier')

	return result

@access_history_log
def clear_samples(db,data):
	if not data.has_key('feature_type'):
		return my_classifier.error_json('feature_type must be designated.')
	feature_type = data['feature_type']
	group = []
	if data.has_key('group'):
		group = ensure_list(data['group'])
	query = generate_any_saples_query(group)

	collection = db[feature_type]
	try:
		samples = collection.find(query)
	except:
		return my_classifier.error_json(sys.exc_info()[1])

	for s in samples:
		if s['group'] == group:
			collection.remove(s)
		else:
			for g in group:
				s['group'].remove(g)
				for key,val in s['likelihood'].items():
					flag = False
					for _g in key.split("::")[1].split("-"):
						if _g == g:
							flag = True
							break
					if flag:
						s['likelihood'].pop(key)
			collection.save(s)

	query = remove_mongo_operator(query)
	result = my_classifier.success_json()
	result['event'] = query
	result['event']['_id'] = get_event_id(query,feature_type,'clear_samples')
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


######################
# group
######################
@access_history_log
def group(db,data):
	print "function: group"
	group_name = data['group_name']
	class_list = data['class_list']
	feature_type = data['feature_type']
	
	collections = db[feature_type]

	samples = collections.find({"cls":{"$in": class_list}})
	print samples
	counter = {cls:0 for cls in class_list} 
	if samples.count() == 0:
		return my_classifier.error_json("ERROR: no samples are hit.")
	for s in samples:
		groups = s['group']
		if not group_name in groups:
			groups.append(group_name)
			_id = s['_id']
			counter[s['cls']]+=1
			collections.update({"_id":_id},{"$set":{'group':groups}})
	result = my_classifier.success_json()
	event_id = "group::%s::%s" % (group_name,"-".join(sorted(class_list)))
	result['event'] = {'_id':event_id,'counter':counter}
	return result
	


######################
# evaluate
######################
@access_history_log
def evaluate(db,data,algorithm):
	print "function: evaluate"
	if not data.has_key('feature_type'):
		return my_classifier.error_json("ERROR: feature_type must be designated")
	feature_type = data['feature_type']




	group = []
	if data.has_key('group'):
		group = my_classifier.ensure_list(data['group'])
	
	samples = get_predicted_samples(db, feature_type, algorithm, group)
	print samples.count()
	
	# class_name2idのために識別器のデータを呼ぶ
	query = my_classifier.mongointerface.create_clf_query(algorithm,feature_type,group)
	try:
		record = db["classifiers"].find_one(query)
	except:
		return my_classifier.error_json(sys.exc_info()[1])
	#print record

	name2id = record['class_name2id']
	l_marker = create_clf_likelihood_marker(algorithm,group)
	print l_marker
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
	result['event'] = {'_id':query['_id']+"::evaluate"}

	id2name = record['class_id2name']
	result['class_list'] = [id2name[k] for k in sorted(id2name.keys())]

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

















