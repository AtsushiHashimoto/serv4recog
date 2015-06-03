# -*- coding: utf-8 -*-
from bottle import Bottle, request, run, error, template
from bson import json_util
from pymongo import MongoClient
import os
import sys
import json

sys.path.append(os.path.abspath(os.path.dirname(__file__)) + '/lib')
import my_classifier


# Configuration
app = Bottle()
app.config['root'] = os.path.dirname(os.path.abspath(__file__))
app.config.load_config("%s/myapp.conf" % app.config['root'])


# Connect to Mongo
mongo_client = MongoClient(app.config['myapp.mongo_host'],int(app.config['myapp.mongo_port']))


@error('404')
def error404(error):
	return '{"status": "Error", "message":"No such algorithm"}'

def parse_params(params):
	hash = {}
	for key, val in params.items():
		hash[key] = val
	return hash

# operation: add, clear, train, predict
@app.route('/ml/<database>/<feature_type>/<algorithm>/<operation>', ['GET', 'POST'])
def route_machine_learning_basic(database, feature_type, algorithm, operation):
	print 'function: route'
	params = parse_params(request.params)
	if params.has_key('json_data'):
		json_data_s = params['json_data']
	else:
		json_data_s = "{}"
	print "param: " + json_data_s
	db = mongo_client[database]
	result = my_classifier.route(db, json_data_s, operation, feature_type, algorithm)
	print result
	return json.dumps(result,default=json_util.default)


# algorithmの指定なくてもサンプルは追加可能
@app.route('/ml/<database>/<feature_type>/add')
def get_add(database):
	if request.params.__dict__.has_key('json_data'):
		json_data_s = request.params.json_data
	else:
		return my_classifier.error_json("parameter 'json_data' must be set.")
	db = mongo_client[database]
	result = my_classifier.route(db,json_data_s,'add')
	print "result" + result
	return json.dumps(result,default=json_util.default)


@app.route('/ml/<database>/<feature_type>/clear_samples')
def get_clearsamples(database):
	if request.params.__dict__.has_key('json_data'):
		json_data_s = request.params.json_data
	else:
		return my_classifier.error_json("parameter 'json_data' must be set.")
	db = mongo_client[database]
	result = my_classifier.route(db,json_data_s,'clear_samples')
	print "result" + result
	return json.dumps(result,default=json_util.default)




#	one-out-leave
@app.get('/ml/<database>/<feature_type>/<algorithm>/one-out-leave/<data_id>')
def get_one_out_leave(database,algorithm,data_id):
	db = mongo_client[database]
	pass

# cross-validation
@app.get('/ml/<database>/<feature_type>/<algorithm>/cross-validation/<fold_num:int>')
def get_cross_validation(database,algorithm,fold_num):
	db = mongo_client[database]
	pass


if app.config['myapp.env']=='development':
	print 'run in development mode'
	run(app, host='localhost', port=8080,debug=True, reloader=True)
else:
	print 'run in production mode'
	run(app, host='localhost',port=8080)