# -*- coding: utf-8 -*-
import numpy as np
from sklearn import svm

import copy
import os
import sys
sys.path.append(os.path.dirname(__file__)+"/../../")
import my_classifier.mongointerface
import my_classifier.sample
import my_classifier

import pickle
import collections

#### test
def test():
	print 'test: %s' % __name__
	return my_classifier.success_json()

#### train
@my_classifier.mongointerface.access_history_log
def train(db,data):
	if not data.has_key('feature_type'):
		return my_classifier.error_json("ERROR: feature_type must be designated")
	feature_type = data['feature_type']
	
	group = []
	if data.has_key('group'):
		group = my_classifier.ensure_list(data['group'])
	
	samples = my_classifier.mongointerface.get_training_samples(db, feature_type, False, group)
	
	if 1 >= samples.count():
		return my_classifier.error_json('Too few training samples for %s.'%feature_type)

	x = [[]] * samples.count()
	y = [0] * samples.count()
	class_count = collections.defaultdict(int)
	
	for i,s in enumerate(samples):
		x[i] = s['ft']
		y[i] = s['cls']
		class_count[s['cls']] += 1



	# クラス名と番号の対応を取る
	class_list = sorted(class_count.keys())

	class_map = {}
	class_weight = {}
	for i,cls in enumerate(class_list):
		class_map[cls] = i
		#		print "float(%d *(%d - %d))/float(%d)"%(len(class_list),samples.count(),class_count[cls],samples.count())
		class_weight[i] = float(len(class_list) * (samples.count() - class_count[cls])) / float(samples.count())

#	print class_count
#	print samples.count()
#	print class_weight
#	exit()
	for i in range(len(y)):
		y[i] = class_map[y[i]]

	clf = svm.SVC(kernel='rbf', probability=True,class_weight=class_weight)
	clf.fit(x,y)
	
	record = my_classifier.mongointerface.create_clf_query('svm_rbf',feature_type,group)
	event = copy.deepcopy(record)
	record['clf'] = pickle.dumps(clf)
	record['class_name2id'] = class_map
	class_map_inv = {str(v):k for k, v in class_map.items()}
	record['class_id2name'] = class_map_inv
	try:
		db["classifiers"].save(record)
	except:
		return my_classifier.error_json(sys.exc_info()[1])
	result = my_classifier.success_json()
	result['event'] = event
	return result

#### predict
@my_classifier.mongointerface.access_history_log
@my_classifier.mongointerface.sample_treater
def predict(db, sample):
	print "function: predict"
	feature_type = sample.type
	group = sample.group
	print group
	
	collection = db["classifiers"]
	query = my_classifier.mongointerface.create_clf_query('svm_rbf',feature_type,group)
	try:
		record = collection.find_one(query)
	except:
		return my_classifier.error_json(sys.exc_info()[1])
	clf = pickle.loads(record['clf'])
	
	# サンプルが1個だけだが，predict_probaは複数サンプルがあるかのように
	# 2次元配列でlikeihoodを返す
	likelihood_list = clf.predict_proba(sample.ft).tolist()[0]
	
	likelihood_dict = {}
	for i,l in enumerate(likelihood_list):
			key = record['class_id2name'][str(i)]
			likelihood_dict[key] = l


	ll_id = my_classifier.mongointerface.create_clf_likelihood_marker('svm_rbf',group)

	sample.likelihood[ll_id] = likelihood_dict
	result = my_classifier.success_json()
	result['event'] = query
	result['result'] = {'id':sample._id, 'likelihood':likelihood_dict}

	my_classifier.mongointerface.add(db,sample)
	return result


if __name__ == '__main__':
	pass
