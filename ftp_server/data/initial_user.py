#!/usr/bin/env python
#_*_ coding:utf-8 _*_
# Author:bear


import json,sys,os

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(BASE_DIR)
# print(BASE_DIR)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

acc_dic = {
    "name": "oldboy",
    "passwd": "123456",
    "size": "1024",
}

print(json.dumps(acc_dic))
username = acc_dic["name"]


with open("%s\data\%s" %(BASE_DIR,username),"w") as f:
    f.write(json.dumps(acc_dic))
