# -*- coding: utf-8 -*-
from sklearn import svm

import os
import sys
import numpy as np
sys.path.append(os.path.dirname(__file__)+"../../")
import my_classifier.mongointerface
import my_classifier

#### test
def test():
    print 'test: %s' % __name__
    return my_classifier.success_json()

#### train
@my_classifier.mongointerface.access_history_log
@my_classifier.train_deco('svc_without_normalization')
def train(x,y,class_weight,option):
    _train(x,y,class_weight,option)
    
def _train(x,y,class_weight,option):
    #option['class_weight'] = class_weight
    #for key,val in option.items():
    #    option[key] = val
        
    # probability must be true in serv4recog
    option['probability'] = True
    option['class_weight'] = 'balanced'
    option['decision_function_shape'] = 'ovr'

    clf = svm.SVC(**option)
    clf.fit(x,y)

    return clf

#### predict
@my_classifier.mongointerface.access_history_log
@my_classifier.mongointerface.sample_treater
@my_classifier.predict_deco('svc_without_normalization')
def predict(clf_list,sample):
    _predict(clf_list,sample)
        
def _predict(clf_list,sample):
    dfs =clf.decision_function(sample)
    likelihoods = []
    for df in dfs:
        likelihood = []
        for i in range(len(df)):
            df_i = df[i]
            max_df = max(list(df)[:i]+list(df)[(i+1):])
            likelihood.append(df_i/(df_i+max_df))
        likelihoods.append(likelihood)
    return 1/(1+np.exp(-np.array(likelihoods)))
    
if __name__ == '__main__':
    argvs = sys.argv
    
    option = {}
    class_weight = []
    
    x = np.loadtxt(argvs[1],delimiter=',')
    y = np.loadtxt(argvs[2],delimiter=',')
    sample = np.loadtxt(argvs[3],delimiter=',')
    
    clf = _train(x,y,class_weight,option)
    print _predict(clf,sample)
