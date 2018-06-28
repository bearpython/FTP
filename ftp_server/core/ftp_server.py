#!/usr/bin/env python
#_*_ coding:utf-8 _*_
# Author:bear

import socketserver
import socket
import os,sys,hashlib
import json


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from conf import setting

class JSONDecodeError(Exception):
    """自定义异常，用自定义异常后程序运行卡住了"""
    def __init__(self, msg):
        self.message = msg

    # def __str__(self): #不写也可以
    #     return self.message

class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    def put(self,*args):
        """接收客户端文件"""
        try:
            # raise JSONDecodeError('连接非正常关闭')
            cmd_dic = args[0]
            filename = "%s/%s" %(self.user_current_path,cmd_dic["filename"])
            filesize = cmd_dic["size"]
            print("上传限制：",self.account_dic["size"])
            file_limit = self.account_dic["size"]
            if filesize <= int(file_limit):
                if os.path.isfile(filename):
                    f = open(filename + ".new","wb")
                else:
                    f = open(filename,"wb")
                self.request.send(b"True")
                recived_size = 0
                m = hashlib.md5()
                while recived_size < filesize:
                    try:
                        data = self.request.recv(1024)
                        m.update(data)
                        f.write(data)
                        recived_size += len(data)
                    except ConnectionResetError as e:
                        print("客户端断开连接",e)
                        break
                else:
                    print("文件接收完成！%s" %filename)
                    new_file_md5 = m.hexdigest()
                    print("新文件md5", new_file_md5)
                    f.close()
                self.request.send("接收文件完成，请进行md5文件一致性校验！".encode())
                client_file_md5 = self.request.recv(1024).decode()
                print("客户端文件md5值：%s\n服务端文件md5值：%s" % (client_file_md5,new_file_md5))
                if new_file_md5 == client_file_md5:
                    self.request.send("上传文件md5一致性校验成功".encode())
                else:
                    self.request.send("上传文件md5一致性校验失败".encode())
            else:
                print("用户上传文件超过限制！")
                self.request.send(b"False")
        except (ConnectionResetError) as e:
            print("客户端断开连接",e)

    def get(self,*args):
        """发送给客户端需要下载的文件"""
        try:
            cmd_dic = args[0]
            filename = "%s\%s" %(self.user_current_path,cmd_dic["filename"])
            if os.path.isfile(filename):
                filesize = os.stat(filename).st_size
                msg_dic_t = {
                    "filename":filename,
                    "size":filesize,
                    "flag":True,
                }
                print("下载文件server端大小：",filesize)
                self.request.send(json.dumps(msg_dic_t).encode()) #two
                client_response = self.request.recv(1024).strip() #three
                print("客户端接状态：",client_response.decode())
                f = open(filename, "rb")
                m = hashlib.md5()
                for line in f:
                    self.request.send(line) #four
                    m.update(line)
                else:
                    print("文件发送完成！")
                    f.close()
                    print("get,文件md5",m.hexdigest())
                    self.request.recv(1024)
                    self.request.send(m.hexdigest().encode())
            else:
                msg_dic_f = {
                    "flag": False
                }
                self.request.send(json.dumps(msg_dic_f).encode())
                print("server端，文件不存在")
        except (ConnectionResetError) as e:
            print("客户端断开连接",e)

    def auth(self):
        pass

    def handle(self):
        # self.request is the TCP socket connected to the client
        Flag = True
        while Flag:
            try:
                self.user_name = self.request.recv(1024).strip()
                user_name = self.user_name.decode()
                print("用户名:",user_name)
                account_file = "%s\%s" %(setting.DATA_PATH,user_name)
                print(account_file)
                if os.path.isfile(account_file):
                    self.request.send(b"True")
                    self.passwd = self.request.recv(1024).strip()
                    user_passwd = self.passwd.decode()
                    print("密码：",user_passwd)
                    with open(account_file, "r") as f:
                        self.account_dic = json.load(f)
                        print("用户文件中储存的密码：",self.account_dic["passwd"])
                    if self.account_dic["passwd"] == user_passwd:
                        self.request.send(b"True")
                        self.user_home_path = "%s\%s" % (setting.USER_PATH, user_name)
                        self.user_current_path = "%s\%s" % (setting.USER_PATH, user_name)
                        while True:
                            try:
                                self.data = self.request.recv(1024).strip() #one
                                print("{} wrote:".format(self.client_address[0]))
                                print(self.data)
                                #print("handle方法循环内部的用户当前目录：",self.user_current_path)
                                cmd_dic = json.loads(self.data.decode())
                                action = cmd_dic["action"]
                                if hasattr(self, action):
                                    func = getattr(self, action)
                                    func(cmd_dic)
                            except ConnectionResetError as e:
                                print("客户端断开连接", e)
                                break
                                Flag = False
                    else:
                        self.request.send(b"False")
                else:
                    self.request.send(b"False")
            except ConnectionResetError as e:
                print("客户端断开连接",e)
                break

    def User_Disk(self):
        """用来判断用户的磁盘配额的，用户上传文件限制（应该是用户的磁盘总额有一个初始值，每次上传或者删除都更新一下用户的账户数据，太麻烦了）"""
        pass

    def dir(self,*args):
        """用户查看目录信息"""
        try:
            cmd_dic = args[0]
            user_path = self.user_current_path
            print("用户目录:",user_path)
            dir_res = os.popen("dir %s"%user_path).read()
            print("before send", len(dir_res))
            if len(dir_res) == 0:
                dir_res = "当前目录为空或指令执行错误"
            server_res = dir_res.encode()
            self.request.send(str(len(server_res)).encode()) #two
            client_ack = self.request.recv(1024)  #three
            print("客户端返回状态：",client_ack.decode())
            self.request.send(server_res) #four
        except ConnectionResetError as e:
            print("客户端断开连接", e)

    def cd(self,*args):
        """用户切换目录，只允许在自己家目录下进行切换"""
        try:
            cmd_dic = args[0]
            print("切换前目录:",self.user_current_path)
            directory_name = cmd_dic["directory"]
            dir_path = "%s\%s" %(self.user_current_path,directory_name)
            if directory_name == ".." and len(self.user_current_path) > len(self.user_home_path):
                self.user_current_path = os.path.dirname(self.user_current_path)
                server_res = "切换后录为：%s" % (self.user_current_path)
                self.request.send(str(len(server_res)).encode())
                client_ack = self.request.recv(1024)
                print("客户端返回状态：", client_ack.decode())
                self.request.send(server_res.encode())
            elif directory_name != ".." and os.path.isdir(dir_path):
                self.user_current_path = dir_path
                server_res = "切换后目录为：%s" %(self.user_current_path)
                self.request.send(str(len(server_res)).encode()) #two
                client_ack = self.request.recv(1024)  #three
                print("客户端返回状态：",client_ack.decode())
                self.request.send(server_res.encode()) #four
            else:
                self.request.send(b"False")
        except ConnectionResetError as e:
            print("客户端断开连接", e)

    def pwd(self,*args):
        """用户查看目录信息"""
        try:
            cmd_dic = args[0]
            os.chdir(self.user_home_path)
            pwd_res = self.user_current_path
            print("before send", len(pwd_res))
            if len(pwd_res) == 0:
                dir_res = "当前目录为空或指令执行错误"
            server_res = pwd_res.encode()
            self.request.send(str(len(server_res)).encode()) #two
            client_ack = self.request.recv(1024)  #three
            print("客户端返回状态：",client_ack.decode())
            self.request.send(server_res) #four
        except ConnectionResetError as e:
            print("客户端断开连接", e)

# if __name__ == "__main__":
#     HOST, PORT = "localhost", 9999
#
#     # Create the server, binding to localhost on port 9999
#     #server = socketserver.TCPServer((HOST, PORT), MyTCPHandler) #这个是单线程的写法
#     server = socketserver.ThreadingTCPServer((HOST, PORT), MyTCPHandler)  # 这个是多线程的写法
#     #server = socketserver.ForkingTCPServer((HOST, PORT), MyTCPHandler)  # 这个是多进程的写法.在windows上不好用
#
#     # Activate the server; this will keep running until you
#     # interrupt the program with Ctrl-C
#     server.serve_forever()