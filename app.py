# -*- coding: utf-8 -*-
from bottle import Bottle, request, run, error#, template
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


# algorithmの指定なくても可能な操作
@app.route('/ml/<database>/<feature_type>/<operation>', ['GET', 'POST'])
def route_sample_treatment(database,feature_type,operation):
    # add, clear_samples, band, disband
    if operation not in ['add','clear_samples','band','disband']:
        return {"status": "Error", "message":"operation '%s' without algorithm in the url is not allowed" % operation}
    
    params = parse_params(request.params)
    if params.has_key('json_data'):
        json_data_s = params['json_data']
    else:
        json_data_s = "{}"
    db = mongo_client[database]
    result = my_classifier.route(db,json_data_s,operation,feature_type)
    print result
    return json.dumps(result,default=json_util.default)





# leave-one-out
@app.get('/leave_one_out/<database>/<feature_type>/<algorithm>/')
def get_one_out_leave(database,feature_type,algorithm):
    params = parse_params(request.params)
    if params.has_key('json_data'):
        json_data_s = params['json_data']
    else:
        json_data_s = {}
    db = mongo_client[database] 
    result = my_classifier.leave_one_out(db,json_data_s,feature_type,algorithm)
    return json.dumps(result,default=json_util.default)


# cross-validation
@app.get('/cross_validation/<database>/<feature_type>/<algorithm>/<fold_num:int>')
def get_cross_validation(database,feature_type,algorithm,fold_num):
    params = parse_params(request.params)
    if params.has_key('json_data'):
        json_data_s = params['json_data']
    else:
        json_data_s = {}
    db = mongo_client[database]
    result = my_classifier.cross_validation(db,json_data_s,feature_type,algorithm,fold_num)
    return json.dumps(result,default=json_util.default)


if app.config['myapp.env']=='development':
         print 'run in development mode'
         run(app, host='localhost', port=8080,debug=True, reloader=True)
else:
         print 'run in production mode'
         run(app, host='localhost',port=8080)