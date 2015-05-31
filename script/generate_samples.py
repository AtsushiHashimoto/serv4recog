# -*- coding: utf-8 -*-
import random
import json
from sys import exit

if __name__ == '__main__':
    import sys
    import requests
    
    # 引数の解析
    args = sys.argv
    argc = len(args)
    
    if argc < 4:
        print "USAGE: # python %s class_name mean_vector std_dev_vector sample_num" % args[0]
        sys.exit()
    
    class_name = args[1]
    mean_vector= json.loads(args[2])
    std_dev_vector = json.loads(args[3])
    sample_num = int(args[4])

 

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
     
    # serv4recogの接続設定
    a = requests.adapters.HTTPAdapter()
    conn = a.get_connection("http://localhost:8080")
    
    database = 'my_db'
    algorithm = 'svm_rbf'
    url_path = "/ml/%s/%s/" % (database,algorithm)
    feature_type = 'test_feature'
    # IDのためのランダムな文字列生成
    id_base = class_name + "".join([random.choice("abcdefghijklmnopqrstuvwxyz") for x in xrange(10)])

    operation = 'add'

    for i in range(sample_num):
        # サンプル生成
        feature_vec = generate_sample(mean_vector, std_dev_vector)

    	# 生成した特徴量を認識用サーバに投げて登録する
        sample = {'id':id_base+'-'+`i`, 'class': class_name, 'feature': feature_vec, 'feature_type': feature_type, 'groups':'a'}
        print sample
        try:
            response = conn.request('POST',url_path + operation, {'json_data': json.dumps(sample)})
        except:
            for message in sys.exc_info():
                print message
            exit()
        print response.data
