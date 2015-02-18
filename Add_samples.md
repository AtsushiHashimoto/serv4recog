# アルゴリズムの変更方法

## アルゴリズムの追加

svm_rbfの設定をコピーする。

% cp -r ./lib/my_classifier/svm_rbf/ ./lib/my_classifier/svm_${algorithm}

コピーしたsvm_${algorithm}.py内のtrain関数の定義(21行目)を次の様に変更する。

`clf = svm.SVC(kernel='${algorithm}',probability=True,class_weight=class_weight)`

## テスト方法
svm_rbfのテスト用スクリプトをコピーする。

% cp ./script/serv4recog_tester_rbf.py  ./script/serv4recog_tester_${algorithm}.py


コピーしたserv4recog_tester_${algorithm}.pyのアルゴリズムの指定(77行目)を次の様に変更する。

`algorithm = 'svm_${algorithm}'`

mongod,app.pyを起動し、スクリプトを実行する。

% mongod --dbpath ./db

% python app.py

% python script/serv4recog_tester_${algorithm}.py
