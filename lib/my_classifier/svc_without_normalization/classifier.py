# -*- coding: utf-8 -*-
from sklearn import svm

import os
import sys
import numpy
sys.path.append(os.path.dirname(__file__)+"../../")
#import my_classifier.mongointerface
#import my_classifier

#### test
#def test():
#    print 'test: %s' % __name__
#    return my_classifier.success_json()

#### train
#@my_classifier.mongointerface.access_history_log
#@my_classifier.train_deco('svc_without_normalization')
def train(x,y,class_weight,option):
    #option['class_weight'] = class_weight
    #for key,val in option.items():
    #    option[key] = val
        
    # probability must be true in serv4recog
    option['probability'] = True
    option['class_weight'] = 'balanced'
    option['decision_function_shape'] = 'ovr'

    clf = svm.SVC(**option)
    clf.fit(x,y)

    # 不要なデータを初期化(シリアライズ化したデータを軽量化するため)
#   for k,v in clf.__dict__.items():
#        print k, ": ", v

    return clf

#### predict
#@my_classifier.mongointerface.access_history_log
#@my_classifier.mongointerface.sample_treater
#@my_classifier.predict_deco('svc_without_normalization')
def predict(clf_list,sample):
    dists =clf.decision_function(sample)
    likelihoods = []
    for dist in dists:
        likelihood = []
        for i in range(len(dist)):
            dist_i = dist[i]
            min_dist = min(list(dist)[:i]+list(dist)[(i+1):])
            likelihood.append(dist_i/(dist_i+min_dist))
        likelihoods.append(likelihood)
        print(likelihood)
    return likelihoods
    
if __name__ == '__main__':
    argvs = sys.argv
    
    option = {}
    class_weight = []
    
    x = numpy.loadtxt(argvs[1],delimiter=',')
    y = numpy.loadtxt(argvs[2],delimiter=',')
    sample = numpy.loadtxt(argvs[3],delimiter=',')
    
    clf = train(x,y,class_weight,option)
    predict(clf,sample)
