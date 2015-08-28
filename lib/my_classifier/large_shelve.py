# -*- coding: utf-8 -*-
import shelve
import os

try:
   import cPickle as pickle
except:
   import pickle


            
class LShelve:
    def __init__(self, shelve_dir):
        if not os.path.exists(shelve_dir):
            os.makedirs(shelve_dir)
        self.shelve = shelve.open("%s/shelve"%shelve_dir)
        self.cache_dir = "%s/cache"%shelve_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        self.cache = [None]*len(self.shelve.keys())
        
    def cache_file_name(self,index):
        return "%s/%s.dump"%(self.cache_dir,index)
        
    def shallow_set_item(self,index,obj):
        if index in self.shelve.keys():
            idx=self.shelve[index]
            self.cache[idx]=obj
        else:
            idx=len(self.cache)
            self.cache.append(obj)
            self.shelve[index] = idx
    def recover_item(self,index,file):
        if index in self.shelve.keys():
            return self.shelve[index]
        obj = pickle.load(open(file))
        self[index] = obj
        return self.shelve[index]

    def __getitem__(self,index):
        if index not in self.shelve.keys():
            file = self.cache_file_name(index)
            if os.path.exists(file):
                idx = self.recover_item(index,file)
            else:
                raise KeyError("'%s' is not found in keys of LShelve")    
        else:
            idx = self.shelve[index]
        if self.cache[idx]==None:
            obj = pickle.load(open(self.cache_file_name(index)))
            self.cache[idx] = obj
            return obj
        return self.cache[idx]        
    def __setitem__(self,index,obj):
        self.shallow_set_item(index,obj)
        dirname = os.path.dirname(index)
        if dirname:
            dirname = "%s/%s"%(self.cache_dir,dirname)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
        filename = self.cache_file_name(index)
        pickle.dump(obj,open(filename,"wb"))

    def __delitem__(self,index):
        idx = self.shelve[index]
        # データ本体を削除
        del self.cache[idx]
        del self.shelve[index]
        os.remove(self.cache_file_name(index))
        # インデックスを修正
        for k,v in self.shelve.items():
            if v>idx:
                self.shelve[k] = v-1
            print "self.shelve[%s]=%d"%(k,self.shelve[k])
    def keys(self):
        return self.shelve.keys()
      
if __name__ == '__main__':
    import sys
    param = sys.argv
    if len(param) < 3 or (not param[1] in ['save','load','delete','size']):
        print "Usage: python large_shelve.py save|load|delete|size index"
        sys.exit(0)
    
    index = param[2]
    print "open LShelve"
    lshelve = LShelve("./lshelve")

    if param[1] == 'save':
        print "priparing a large object"
        large_object = index * 1000 * 1000
        print "storing the object"
        lshelve[index] = large_object
        print "the large object data is stored as '%s'"%lshelve.cache_file_name(index)
        print "check the size of dump file."
    elif param[1] == 'load':
        print "loading the directed object"
        large_object = lshelve[index]
    elif param[1] == 'size':
        print "len(lshelve[%s])=%d"%(index,len(lshelve[index]))
    else:
        print "delete '%s'"%index
        del lshelve[index]                
