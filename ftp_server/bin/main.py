#!/usr/bin/env python
#_*_ coding:utf-8 _*_
# Author:bear


import os,sys,socketserver

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from core import ftp_server


if __name__ == "__main__":
    HOST, PORT = "localhost", 9999

    # Create the server, binding to localhost on port 9999
    #server = socketserver.TCPServer((HOST, PORT), MyTCPHandler) #这个是单线程的写法
    server = socketserver.ThreadingTCPServer((HOST, PORT), ftp_server.MyTCPHandler)  # 这个是多线程的写法
    #server = socketserver.ForkingTCPServer((HOST, PORT), MyTCPHandler)  # 这个是多进程的写法.在windows上不好用

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()