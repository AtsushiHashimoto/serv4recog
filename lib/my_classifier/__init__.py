import svm_rbf
from sample import Sample
import mongointerface
import json


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




if __name__ == '__main__':
	from pymongo import MongoClient

	mongo_client = MongoClient()
	db = mongo_client['test']

	returned_json = route(db, '{"test":"hoge"}','test','svm_rdf')
	print returned_json