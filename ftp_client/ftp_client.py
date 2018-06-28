#!/usr/bin/env python
#_*_ coding:utf-8 _*_
# Author:bear

import socket
import os,sys,time
import json,hashlib
import ShowProcess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
print(BASE_DIR)
#声明socket类型，同时生成socket连接对象

class FtpClient(object):
    def __init__(self):
        self.client = socket.socket() #默认地址簇是AF_INET就是IPV4，type是TCP/IP，proto=0，fileno=None

    def help(self):
        """在用户输入ftp未定义的指令时显示给用户"""
        msg = """
        ls
        pwd
        cd ../..
        get filename
        put filename
        """
        print(msg)

    def connect(self,ip_port):
        self.client.connect(ip_port)

    def authenticate(self):
        """用户登录认证，把用户名和密码发送给server端进行认证"""
        i = 0
        while i < 3:
            user_name = input("请输入用户名：").strip()
            user_passwd = input("请输入密码：").strip()
            if len(user_name) == 0 or len(user_passwd) == 0:
                print("输入的用户名或密码不能为空！请重新输入！")
                i += 1
            else:
                self.client.send(user_name.encode())
                auth_name_flag = self.client.recv(1024)
                if auth_name_flag.decode() == "True":
                    self.client.send(user_passwd.encode())
                    auth_passwd_flag = self.client.recv(1024)
                    print(auth_name_flag,auth_passwd_flag)
                    if auth_passwd_flag.decode() == "True":
                        print("欢迎登录ftp系统！")
                        self.interactive()
                    else:
                        print("用户密码输入不正确！")
                        i += 1
                else:
                    print("用户名输入不正确！")
                    i += 1
        else:
            print("您输入的用户名或密码错误次数过多，程序退出！")
            exit()

    def interactive(self):
        """认证后登录的ftp主程序，根据用户输入的内容反射调用相关的方法"""
        # self.authenticate()#登录认证的方法
        while True:
            cmd = input(">>>:").strip()
            if len(cmd) == 0:continue
            if cmd == "get" or cmd == "put" or cmd == "cd":
                cmd_str = cmd.split()
                if len(cmd_str) == 1:
                    print("少一个参数")
                    continue
            cmd_str = cmd.split()[0]
            if hasattr(self,"cmd_%s" %cmd_str):
                func = getattr(self,"cmd_%s" %cmd_str)
                func(cmd)
            else:
                self.help()

    def cmd_put(self,*args):
        """上传到ftp文件"""
        cmd_split = args[0].split()
        if len(cmd_split) > 1:
            filename = cmd_split[1]
            if os.path.isfile(filename):
                filesize = os.stat(filename).st_size
                msg_dic = {
                    "action":"put",
                    "filename":filename,
                    "size":filesize,
                    "overidden":True  #这个是如果重名覆盖
                }
                self.client.send( json.dumps(msg_dic).encode() )
                #为了防止粘包，等服务器确认
                server_response = self.client.recv(1024)
                if server_response.decode() == "True":
                    f = open(filename,"rb")
                    process = 0
                    send_size = 0
                    m = hashlib.md5()
                    for line in f:
                        self.client.send(line)
                        m.update(line)
                        send_size += len(line)
                        process_bar = ShowProcess.ShowProcess(send_size, filesize, 50, process)
                        res = process_bar.show_process()
                        process = res
                    else:
                        print("文件上传完成！")
                        f.close()
                        print("put,文件md5", m.hexdigest())
                        self.client.recv(1024)
                        self.client.send(m.hexdigest().encode())
                        put_md5 = self.client.recv(1024)
                        print("上传文件一致性校验结果：",put_md5.decode())
                else:
                    print("上传文件过大，请重新选择文件！")
            else:
                print(filename,"is not exit")

    def cmd_get(self,*args):
        """下载ftp文件"""
        while True:
            cmd_split = args[0].split()
            if len(cmd_split) > 1:
                filename = cmd_split[1]
                msg_dic = {
                    "action": "get",
                    "filename": filename,
                    "overidden": True  # 这个是如果重名覆盖
                }
                self.client.send( json.dumps(msg_dic).encode()) #发送给server端文件name和动作 one
                self.server_response = self.client.recv(1024).strip()  #接收server端的返回文件是否存在及文件信息  two
                file_dic = json.loads(self.server_response.decode())
                print(file_dic)
                if file_dic["flag"] == True:
                    filesize = file_dic["size"]
                    if os.path.isfile(filename):
                        f = open(filename + ".new", "wb")
                    else:
                        f = open(filename, "wb")
                    self.client.send(b"client ok") #three
                    recived_size = 0
                    process = 0
                    m = hashlib.md5()
                    while recived_size < filesize:
                        data = self.client.recv(1024) #four
                        m.update(data)
                        f.write(data)
                        recived_size += len(data)
                        process_bar = ShowProcess.ShowProcess(recived_size,filesize,50,process)
                        res = process_bar.show_process()
                        process = res
                    else:
                        new_file_md5 = m.hexdigest()
                        print("新文件md5",new_file_md5)
                        print("文件下载完成！%s" % filename)
                        f.close()
                    self.client.send("接收文件完成，请进行md5文件一致性校验！".encode())
                    server_file_md5 = self.client.recv(1024).decode()
                    print("服务端文件md5值：%s\n客户端文件md5值：%s" %(server_file_md5,new_file_md5))
                    if new_file_md5 == server_file_md5:
                        print("下载文件一致性校验成功")
                    else:
                        print("下载文件一致性校验失败，请删除文件从新下载！")
                    break
                else:
                    print("您要下载的文件不存在,请重新输入!")
                    break

    def cmd_dir(self,*args):
        """查看目录信息"""
        cmd_split = args[0].split()
        if len(cmd_split) == 1:
            msg_dic = {
                "action": "dir",
            }
            self.client.send(json.dumps(msg_dic).encode()) #one
            cmd_res_size = self.client.recv(1024) #two 接收大小
            print("返回结果的大小：",cmd_res_size)
            self.client.send("准备好接收了，server可以发送结果了".encode("utf-8")) #three
            received_size = 0
            received_data = b""
            while received_size < int(cmd_res_size.decode()):
                data = self.client.recv(1024)  #four
                received_size += len(data)  # 每次收到的有可能小于1024，所以必须用len判断
                # print(data.decode())
                received_data += data
            else:
                print("cmd res recive done...", received_size)
                print(received_data.decode())
        else:
            self.help()

    def cmd_cd(self,*args):
        """用户在自己的家目录中切换目录,windows不好使"""
        cmd_split = args[0].split()
        directory_name = cmd_split[1]
        if len(cmd_split) == 2:
            msg_dic = {
                "action": "cd",
                "directory":directory_name
            }
            self.client.send(json.dumps(msg_dic).encode()) #one
            cmd_res_size = self.client.recv(1024).decode() #two 接收大小
            if cmd_res_size != "False":
                print("返回结果的大小：",cmd_res_size)
                self.client.send("准备好接收了，server可以发送结果了".encode("utf-8")) #three
                received_size = 0
                received_data = b""
                while received_size < int(cmd_res_size):
                    data = self.client.recv(1024)  #four
                    received_size += len(data)  # 每次收到的有可能小于1024，所以必须用len判断
                    # print(data.decode())
                    received_data += data
                else:
                    print("切换目录没有数据返回", received_size)
                    print(received_data.decode())
            else:
                print("您没有权限访问,或目录不存在")
        else:
            self.help()

    def cmd_pwd(self,*args):
        """查看当前路径，windows没有pwd命令,dir可以看到前当前目录"""
        cmd_split = args[0].split()
        if len(cmd_split) == 1:
            msg_dic = {
                "action": "pwd",
            }
            self.client.send(json.dumps(msg_dic).encode()) #one
            cmd_res_size = self.client.recv(1024) #two 接收大小
            print("返回结果的大小：",cmd_res_size)
            self.client.send("准备好接收了，server可以发送结果了".encode("utf-8")) #three
            received_size = 0
            received_data = b""
            while received_size < int(cmd_res_size.decode()):
                data = self.client.recv(1024)  #four
                received_size += len(data)  # 每次收到的有可能小于1024，所以必须用len判断
                # print(data.decode())
                received_data += data
            else:
                print("cmd res recive done...", received_size)
                print(received_data.decode())
        else:
            self.help()

if __name__ == "__main__":
    ip_port = ("localhost",9999)        #服务端ip、端口
    ftp = FtpClient()            #创建客户端实例
    ftp.connect(ip_port)
    ftp.authenticate()

