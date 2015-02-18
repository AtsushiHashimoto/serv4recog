# -*- coding: utf-8 -*-
from sklearn import svm

import os
import sys
sys.path.append(os.path.dirname(__file__)+"../../")
import my_classifier.mongointerface
import my_classifier


#### test
def test():
	print 'test: %s' % __name__
	return my_classifier.success_json()


#### train
@my_classifier.mongointerface.access_history_log
@my_classifier.train_deco('svm_linear')
def train(x,y,class_weight):
        clf = svm.SVC(kernel='linear',probability=True,class_weight=class_weight)
        clf.fit(x,y)
	return clf


#### predict
@my_classifier.mongointerface.access_history_log
@my_classifier.mongointerface.sample_treater
@my_classifier.predict_deco('svm_linear')
def predict(clf,sample):
	return clf.predict_proba(sample.ft).tolist()[0]



if __name__ == '__main__':
	pass
