# -*- coding: utf-8 -*-
from sklearn import svm

import os
import sys
import numpy
sys.path.append(os.path.dirname(__file__)+"../../")
import my_classifier.mongointerface
import my_classifier


#### test
def test():
    print 'test: %s' % __name__
    return my_classifier.success_json()


#### train
@my_classifier.mongointerface.access_history_log
@my_classifier.train_deco('svc')
def train(x,y,class_weight,option):
    #option['class_weight'] = class_weight
    #for key,val in option.items():
    #    option[key] = val
        
    # probability must be true in serv4recog
    option['probability'] = True
    option['class_weight'] = 'auto'
    clf = svm.SVC(**option)
    clf.fit(x,y)

    # 不要なデータを初期化(シリアライズ化したデータを軽量化するため)
    clf.__dict__["support_"]=numpy.array([numpy.int32(0)])
    clf.__dict__["support_vectors_"]=numpy.array([numpy.array([numpy.float64(0)])])

    return clf


#### predict
@my_classifier.mongointerface.access_history_log
@my_classifier.mongointerface.sample_treater
@my_classifier.predict_deco('svc')
def predict(clf,sample):
    return clf.predict_proba(sample.ft).tolist()[0]



if __name__ == '__main__':
    pass
