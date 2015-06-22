# -*- coding: utf-8 -*-
import json
def ensure_list(elem):
    if isinstance(elem,list):
        return elem
    else:
        if elem:
            return [elem]
        else:
            return []


            
class Sample:            
        def __init__(self, json_data):
		if json_data.has_key('feature'):
			self.ft = json_data['feature']
		elif json_data.has_key('ft'):
			self.ft = json_data['ft']
		if json_data.has_key('id'):
			self._id = json_data['id']
		elif json_data.has_key('_id'):
      			self._id = json_data['_id']
		if json_data.has_key('ground_truth'):
			self.ground_truth = json_data['ground_truth']
		if json_data.has_key('group'):
			self.group = ensure_list(json_data['group'])
		else:
			self.group = []
		self.likelihood = {}
		if json_data.has_key('likelihood'):
			self.likelihood = json_data['likelihood']
		self.weight = 1.0
		if json_data.has_key('weight'):
			self.weight = json_data['weight']
      
if __name__ == '__main__':
	json_data = json.loads('{"feature":[0,0,0,0]}')
												 #"{'feature':[1.2,3,0.2,-1], 'id':'2014RC01_S020::frame0000001::blob001::0003','class':'tomato'}")
	sample = Sample(json_data)
	#print sample