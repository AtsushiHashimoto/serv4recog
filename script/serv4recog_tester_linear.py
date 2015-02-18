# -*- coding: utf-8 -*-
import random
import json


if __name__ == '__main__':
	import sys
	
	# 引数の解析
	args = sys.argv
	argc = len(args)
	
	if argc < 4:
		print "USAGE: # python %s class_num feature_dim sample_num" % args[0]
		exit()
	
	classes = [{}] * int(args[1])
	feature_dim = int(args[2])
	sample_num = json.loads(args[3])
	if isinstance(sample_num, int):
		sample_num = [int(args[3])] * len(classes)
	else:
		if len(sample_num) != len(sample_num):
			print "ERROR: sample_num must be equal to class_num."
			exit()


	# 各クラスのサンプルをガウス分布に基づいてランダムに生成
	def generate_sample(average_vec,sigma_vec):
		dim = len(average_vec)
		if dim != len(sigma_vec):
			print "ERROR: different length of average and sigma vec."
			exit()
		sample_feature = [0.0] * dim
		for i, (ave,sigma) in enumerate(zip(average_vec, sigma_vec)):
			sample_feature[i] = random.gauss(ave,sigma)
		return sample_feature

	y = []
	x = []

	# 各クラスの核となる代表サンプル+揺らぎをランダムに生成する種
	seed_ave = [random.uniform(0.0, 5.0)] * feature_dim
	seed_sigma = [1.0] * feature_dim

	cores = {'ave':[],'sigma':[]}

	for i, (cls, num) in enumerate(zip(classes,sample_num)):
		# 代表サンプル+揺らぎの生成
		core_ave = generate_sample(seed_ave, seed_sigma)
		cores['ave'].append(core_ave)
		core_sigma = generate_sample(seed_ave, seed_sigma)
		cores['sigma'].append(core_sigma)

		# クラス番号を追加
		y += ['class_%02d'%i] * num
		temp = [[]] * num
		# サンプル毎に特徴量をランダム生成
		for j in range(num):
			temp[j] = generate_sample(core_ave,core_sigma)
		x += temp

#	print y
#	print x

	# 生成した特徴量を認識用サーバに投げて登録する
	import requests
	# testする際の経路
	test_by_post = False # True ならpost形式で投げる


	a = requests.adapters.HTTPAdapter()
	conn = a.get_connection("http://localhost:8080")
	
	database = 'test'
	# ここでalgorithm(ディレクトリ名)を指定する
	algorithm = 'svm_linear'

	# groupを指定するテスト 
	group = ['target_group']
	# group = []

	url_path = "/ml/%s/%s/" % (database,algorithm)

	feature_type = 'test_dim%03d' % feature_dim

	# まず，以前の内容を消去する
	operation = 'clear_samples'
	print operation

	params = {'json_data':json.dumps({'feature_type':feature_type,'group':group})}
	try:
		response = conn.request('POST',url_path + operation, params)
	except:
		for message in sys.exc_info():
			print message
		exit()

	result = json.loads(response.data)
	print result

	if result['status'] != 'success':
		print "ERROR: failed to clear samples"
		exit()

	operation = 'clear_classifier'
	print operation
	
	params = {'json_data':json.dumps({'feature_type':feature_type,'group':group})}
	try:
		response = conn.request('POST',url_path + operation, params)
	except:
		for message in sys.exc_info():
			print message
		exit()

	result = json.loads(response.data)
	print result
	
	if result['status'] != 'success':
		print "ERROR: failed to clear classifier"
		exit()


	# 1つずつサンプルを追加
	operation = 'add'
	print operation

	for i, (_y, _x) in enumerate(zip(y,x)):
		sample = {'id':i, 'class': _y, 'feature': _x, 'feature_type': feature_type, 'group': group}
		print sample
		try:
			response = conn.request('POST',url_path + operation, {'json_data': json.dumps(sample)})
		except:
			for message in sys.exc_info():
				print message
			exit()
		print response.data
		result = json.loads(response.data)
		print result


	# 学習をさせる
	operation = 'train'
	print operation

	multi = True
	force = False

	# order: 学習させる際のオプション 
	# order.force: trueなら学習済みの識別器があっても再度学習をし直す．省略時はFalse(未実装)
	order = {'feature_type':feature_type, 'force':force, 'group':group}
	response = conn.request('POST',url_path + operation, {'json_data':json.dumps(order)})
	result = json.loads(response.data)
	print result


	# 識別テストをする
	operation = 'predict'
	print operation

	test_num = 100
	offset = len(x)
	y = []
	likelihood = []
	for i in range(test_num):
		class_id = random.randrange(0,len(classes))		
		class_name = "class_%02d"%class_id
		
		
		feature = generate_sample(cores['ave'][class_id],cores['sigma'][class_id])
		sample = {'id':offset+i, 'class': class_name, 'feature': feature, 'feature_type': feature_type, 'group': group}
		
		try:
			response = conn.request('POST',url_path + operation, {'json_data':json.dumps(sample)})
		except:
			for message in sys.exc_info():
				print message
			exit()

		result = json.loads(response.data)
		print result
		y.append('class_%02d'%class_id)
		#likelihood.append(result['likelihood'])

	# 識別結果の精度を問い合わせる
	operation = 'evaluate'
	order = {'feature_type':feature_type,'group':group}
	response = conn.request('POST', url_path + operation, {'json_data':json.dumps(order)})
	result = json.loads(response.data)
	print "class_list: %s"% " ".join(result['class_list'])
	for key,val in result.items():
		if key=='class_list':
			continue
		print "==== %s ===="%key
		print val
		print ""
