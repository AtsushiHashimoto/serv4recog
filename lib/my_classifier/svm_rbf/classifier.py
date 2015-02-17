# -*- coding: utf-8 -*-
import numpy as np
from sklearn import svm

import copy
import os
import sys
sys.path.append(os.path.dirname(__file__)+"../../")
import my_classifier.mongointerface
import my_classifier.sample
import my_classifier

import pickle
import collections

import functools

#### test
def test():
	print 'test: %s' % __name__
	return my_classifier.success_json()


#### train
#### デコレータを用いた版に修正

def train_deco(func):
	@functools.wraps(func)
	def wrapper(db,data):
		# データを適当な形式にする
		if not data.has_key('feature_type'):
			return my_classifier.error_json("ERROR: feature_type must be designated")
		feature_type = data['feature_type']

		group = []
		if data.has_key('group'):
			group = my_classifier.ensure_list(data['group'])


		# クラスへの分類
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

	       	class_list = sorted(class_count.keys())


		# クラスの「重み付け」
		class_map = {}
		class_weight = {}
		for i,cls in enumerate(class_list):
			class_map[cls] = i
			class_weight[i] = float(len(class_list) * (samples.count() - class_count[cls])) / float(samples.count())

		for i in range(len(y)):
			y[i] = class_map[y[i]]


		#アルゴリズムに依存する部分
		clf=func(x,y,class_weight)

		#結果を保存
		record = my_classifier.mongointerface.create_clf_query('svm_rbf',feature_type,group)
		event = {'_id':record['_id'] + "::train"}

		record['clf'] = pickle.dumps(clf)
		record['class_name2id'] = class_map
		class_map_inv = {str(v):k for k, v in class_map.items()}
		record['class_id2name'] = class_map_inv
		try:
			record = my_classifier.mongointerface.remove_mongo_operator(record)
			db["classifiers"].save(record)
		except:
			return my_classifier.error_json(sys.exc_info()[1])
		result = my_classifier.success_json()
		result['event'] = event
		return result
	return wrapper


#train_svm=my_classifier.mongointerface.access_history_log(train_deco(train_svm))
@my_classifier.mongointerface.access_history_log
@train_deco
def train(x,y,class_weight):
        clf = svm.SVC(kernel='rbf',probability=True,class_weight=class_weight)
        clf.fit(x,y)
	return clf


### predict
### デコレータを用いた版に修正
def predict_deco(method):
	def recieve_func(func):
		@functools.wraps(func)
		def wrapper(db,sample):
			# サンプルのグループを取ってくるだけ
			# Sample … (ft,_id,type,cls,group,likelihood,weight)
			print "function: predict"
			feature_type = sample.type
			group = sample.group
			print group

			## method(svm_rbf)に依存する部分その1
			query = my_classifier.mongointerface.create_clf_query(method,feature_type,group)

			# 予測部
			collection = db["classifiers"]
			
			try:
				record = collection.find_one(query)
			except:
				return my_classifier.error_json(sys.exc_info()[1])
			clf = pickle.loads(record['clf'])


			## method(svm_rbf)に依存する部分その2
			likelihood_list = func(clf,sample)

			likelihood_dict = {}
			for i,l in enumerate(likelihood_list):
				key = record['class_id2name'][str(i)]
				likelihood_dict[key] = l

			## method(svm_rbf)に依存する部分その3
			ll_id = my_classifier.mongointerface.create_clf_likelihood_marker(method,group)
			
			# 予測結果をデータベースへ追加
			sample.likelihood[ll_id] = likelihood_dict
			result = my_classifier.success_json()
			result['event'] = {'clf_id':query['_id']}
			result['result'] = {'id':sample._id, 'likelihood':likelihood_dict}

			my_classifier.mongointerface.add(db,sample)
			return result 
		return wrapper
	return recieve_func



@my_classifier.mongointerface.access_history_log
@my_classifier.mongointerface.sample_treater
@predict_deco('svm_rbf')
def predict(clf,sample):
	return clf.predict_proba(sample.ft).tolist()[0]



if __name__ == '__main__':
	pass
