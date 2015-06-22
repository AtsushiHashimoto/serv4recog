# -*- coding: utf-8 -*-
import json
import sys
import os
import glob
import commands
import re
import requests

import argparse


if __name__ == '__main__':
	usage = "USAGE: # python %(prog)s tar_dir feature_name \"feature_extractor [options]\""
	description = "Upload samples stored in directory."
	parser = argparse.ArgumentParser(description=description,usage=usage)
	
	parser.add_argument('tar_dir', metavar='FILE',help='target directory')
	parser.add_argument('feature_name', metavar='STR',help='feature name')
	
	parser.add_argument("-e", "--extract_script", dest="feature_extractor",default=None,
								help="exe path for feature extraction", metavar="FILE")
	parser.add_argument("-s", "--servername", dest="servername",default="localhost",
								help="server name for serv4recog", metavar="DOMAIN/IP_ADDRESS")
	parser.add_argument("-p", "--port", dest="port",default="8080",
										help="server port for serv4recog", metavar="INT")
	parser.add_argument("-d", "--dbname", dest="dbname",default="test",
										help="dbname for samples", metavar="DB_NAME")

	args = parser.parse_args()


	dat_pat = re.compile("(.*)_%s.dat"%args.feature_name)


	# 指定されたディレクトリ(tar_dir)以下を解析し，(必要であれば特徴抽出をし，)サーバに投げる
	# 途中にgroups.dat(各行1グループ名)があれば，それを配下のディレクトリの全サンプルに追加する
  # ディレクトリ構成例)
	# tar_dir
	# ├── group01
	# │   ├── groups.dat
	# │   ├── group01_01
	# │   │   └── class00X
	# │   │       ├── groups.dat
	# │   │       ├── sample00001.png
	# │   │       └── featureA-sample00002.dat
	# │   └── group01_02
	# └── group02

	# sample0001.pngに対する処理
	# 1. 特徴(featureA)を抽出 -> featureA-sample00001.datへ出力
	#		tar_dir/group01/group01_01/class00X/featureA-sample00001.dat
	#		--- 以下，ファイルの内容 ---
	#			0.1
	#			0.9
	#			0.3
	#			0.7
	#			0.5
	#			0.5
	#
	# 2. featureA-sample00001.datの内容をサーバに投げる
	#		 http://localhost:8080/ml/test_db/svm_rbf/add?{"feature":[0.1,0.9,0.3,0.7,0.5,0.5],"id":"sample00001","ground_truth":"class00X","group":["group01","group01_01"]}

	def send_sample(conn,file,groups):
		path, ext = os.path.splitext(file)
		m = dat_pat.match(file)
		if m == None:
			if not args.feature_extractor:
				print "ERROR: no feature extractor was designated."
				sys.exit()
			dat_file = "%s_%s.dat" % (path,args.feature_name)
			if os.path.exists(dat_file):
				return
			command = args.feature_extractor + " " + file + " > " + dat_file
			commands.getoutput(command)
			file = dat_file
		feature = []
		with open(file, 'r') as f:
			for line in f:
				feature.append(float(line))
		url_path = "/ml/%s/any_algorithm/add" % (args.dbname)
		print url_path

		class_name = groups[-1]
		id = class_name + "_" + os.path.basename(m.group(1))

		json_data = json.dumps({"feature_type":args.feature_name,"id":id,"ground_truth":class_name,"group":groups[0:-1],"feature":feature})
		print json_data
		response = conn.request('POST',url_path,{"json_data":json_data})
				#		response = session.post(url, params={"json_data":json_data})
				#		print response.text
		print response.data

	def load_group_list_file(file):
		groups = []
		with open(file, 'r') as f:
			for line in f:
				groups.append(line.strip())

	group_list_file = "groups.dat"

	def main_process(conn,dir,groups):		
		if os.path.exists(dir+"/"+group_list_file):			
			groups + load_group_list_file(dir+"/"+group_list_file)
		for file in glob.glob(dir + "/*"):
			if file == group_list_file: # 読み込み済み
				continue
			if os.path.isfile(file):
				send_sample(conn,file,groups)
				continue
			if not os.path.isdir(file):
				continue
			group_name = os.path.basename(file)
			main_process(conn,file,groups + [group_name])


	a = requests.adapters.HTTPAdapter()
	conn = a.get_connection(args.servername+":"+args.port)

	for file in glob.glob(str(args.tar_dir) + "/*"):
		groups = []
		if os.path.isfile(file):
			continue
		if not os.path.isdir(file):
			continue
		group_name = os.path.basename(file)
		main_process(conn,file,groups + [group_name])
			










