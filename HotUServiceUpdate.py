import hashlib
import os
import re
import time

import paramiko
import pymysql
from requests import get


class PutFileToFTP(object):
    def __init__(self, host="10.1.210.155", username="root", password="uKAclou#807@196", port=22):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self._transport = paramiko.Transport((self.host, self.port))
        self._transport.connect(username=self.username, password=self.password)
        self.sftp = paramiko.SFTPClient.from_transport(self._transport)

    def put_file_to_ftp(self, local_path, remount_path):
        try:
            self.sftp.put(local_path, remount_path)
        except Exception as e:
            pass

    def is_dir_exit(self, target_path='.'):
        try:
            self.sftp.listdir(target_path)
            # print("存在文件夹")
            return True
        except:
            # print("不存在文件夹")
            return False

    def make_dir(self, target_path, mode='0777'):
        self.sftp.mkdir(target_path)

    def close_ftp(self):
        self._transport.close()


class FindLocalVersion(object):

    def get_apk_size(self, temp_paht):
        size = os.path.getsize(temp_paht)
        return size

    def find_Md5(self, temp_paht):
        with open(temp_paht, 'rb') as f:
            rb_data = f.read()
        hmd5 = hashlib.md5(rb_data).hexdigest()
        return hmd5

    def find_model(self, input_sid):
        model = input_sid.split(r'_')[-2]
        return model

    def is_apkend(self, input_localapk_ptah):
        s = os.path.splitext(input_localapk_ptah)[-1]
        if s == '.zip':
            return True
        else:
            print("输入的路径有误，请重新输入正确apk路径")
            return False

    def find_version(self, input_path):
        try:
            s = os.path.split(input_path)[-1]
            r = re.compile(r'V\d.*\.\d+').findall(s)
            return r
        except Exception as e:
            print(e)

    def find_hot_version(self, input_path):
        try:
            s = os.path.split(input_path)[-1][0:-4]
            return s
        except Exception as e:
            print(e)


class MySql(object):
    def __init__(self, host='10.1.75.69', user='root', password='123456', database='wws_version_mgr'):
        self.user = user
        self.host = host
        self.password = password
        self.database = database
        self.conn = None
        self.cur = None

    # 连接数据库
    def connect_mysql(self):
        try:
            self.conn = pymysql.connect(self.host, self.user, self.password, self.database)
            # print("连接数据库成功！")
        except:
            # print("连接数据库失败！")
            return False
        self.cur = self.conn.cursor()
        return True

    # 标准执行sql语句
    def execut_mysql(self, sql, val=None):
        try:
            self.connect_mysql()
            self.cur.execute(sql, val)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print("执行数据库失败：{}".format(e))

    # 插入sid，用于升级sid插入，自动加1
    def insert_sid(self, sql, val=None):
        try:
            self.connect_mysql()
            self.cur.execute(sql, val)
            self.cur.lastrowid
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(e)

    # 查找sid
    def find_sid(self, sql):
        try:
            self.connect_mysql()
            self.cur.execute(sql)
            sid = self.cur.fetchall()[0][0]
            # print(sid)
            return sid
        except Exception as e:
            print("查询sid失败：{}".format(e))

    # 删除重复的数据
    def delete_sql(self, sql, val):
        try:
            # self.connect_mysql()
            self.cur.execut(sql, val)
            self.conn.commit()
        except Exception as e:
            print("删除数据失败：{}".format(e))

    # 如果已经打开，关闭游标，关闭数据库连接
    def close_mysql(self):
        if self.conn and self.cur:
            self.cur.close()
            self.conn.close()
        return True


def main():
    input_app_paht = input("请输入app路径所在路径（如：D:\..\demo.apk）：")
    # 获取SSID，比如：Connect_BIN_K1_998
    SSID = input("请输入SSID(如：Connect_BIN_K1_998)：")
    device_Ver = input("请输入设备当前版本号(如：V3.2.013.133)：")
    version = FindLocalVersion()
    temp_apkpath = version.is_apkend(input_app_paht)
    while True:
        if temp_apkpath:
            break
        else:
            input_app_paht = input("请输入正确的apk路径（如：D:\..\demo.apk）：")
    local_app_name = os.path.split(input_app_paht)[-1]
    MODEL = input("请输入机型（如：K1,S20i）：")
    MD5 = version.find_Md5(input_app_paht)
    SIZE = version.get_apk_size(input_app_paht)
    ftp_app_path = SSID + '/' + local_app_name
    VER = version.find_hot_version(input_app_paht)
    try:
        ftp = PutFileToFTP()
        if ftp.is_dir_exit("/var/ftp/" + SSID):
            ftp.put_file_to_ftp(input_app_paht, "/var/ftp/" + ftp_app_path)
        else:
            ftp.make_dir("/var/ftp/" + SSID)
            ftp.put_file_to_ftp(input_app_paht, "/var/ftp/" + ftp_app_path)
        ftp.close_ftp()
        print("上传版本到服务器ok！")
    except Exception as e:
        print("上传app版本到ftp失败：{}".format(e))
        raise

    mysql = MySql()

    data_software = {
        'sid': SSID,
        'model': MODEL,
        'mode': 3,
        'regdt': time.strftime('%Y-%m-%d %X', time.localtime(time.time())),
        'descr': 'update'
    }
    table_software = 'software'
    keys_software = ','.join(data_software.keys())
    values_software = ','.join(['%s'] * len(data_software))
    sql_software = 'insert into {0}({1}) values({2})'.format(table_software, keys_software, values_software)
    try:
        mysql.execut_mysql('delete from software where sid=%s', SSID)
        mysql.insert_sid(sql_software,tuple(data_software.values()))
        mysql.close_mysql()
    except:
        mysql.insert_sid(sql_software,tuple(data_software.values()))
        mysql.close_mysql()

    # 插入software，已经存在id删除重新添加，如果没存在直接插入数据
    # try:
    #     mysql.execut_mysql('delete from software where sid=%s', SSID)
    #     mysql.close_mysql()
    #     mysql.insert_sid('insert into software(sid,model,mode,regdt,descr) value(%s,%s,%s,%s,%s)',
    #                      (SSID, MODEL, 3, time.strftime('%Y-%m-%d %X', time.localtime(time.time())), "update"))
    #     mysql.close_mysql()
    # except:
    #     mysql.insert_sid('insert into software(sid,model,mode,regdt,descr) value(%s,%s,%s,%s,%s)',
    #                      (SSID, MODEL, 3, time.strftime('%Y-%m-%d %X', time.localtime(time.time())), "update"))
    #     mysql.close_mysql()
    # 获取id，后续通过该ID添加数据
    ID = mysql.find_sid('select * from software where sid="{}"'.format(SSID))
    # 填入version数据
    data_fota = {
        'sid': ID,
        'VerCUr': VER,
        'VerPre': device_Ver,
        'Tactics': 1,
        'Crc1': SIZE,
        'Crc2': SIZE,
        'Flg': 1,
        'Must': 1,
        'Ftp': ftp_app_path,
        'date': time.strftime('%Y-%m-%d %X', time.localtime(time.time())),
        'Descr': "update",
        'MdValue': MD5
    }
    table_fota = 'version_fota'
    keys_fota = ','.join(data_fota.keys())
    values_fota = ','.join(['%s'] * len(data_fota))
    sql_fota = 'insert into {0}({1}) value({2})'.format(table_fota,keys_fota,values_fota)
    mysql.execut_mysql(sql_fota,tuple(data_fota.values()))
    mysql.close_mysql()

    # try:
    #     mysql.execut_mysql(
    #         'insert into version_fota(sid,VerCUr,VerPre,Tactics,Crc1,Crc2,Flg,Must,Ftp,date,Descr,MdValue) value(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
    #         (
    #             ID, VER, device_Ver, 1, SIZE, SIZE,
    #             1, 1, ftp_app_path, time.strftime('%Y-%m-%d %X', time.localtime(time.time())), "update",
    #             MD5))
    #     mysql.close_mysql()
    # except Exception as e:
    #     print("插入描述失败：{}".format(e))
    total_version = device_Ver + "_" + VER

    data_desc={
        'Sid':ID,
        'Ver':total_version,
        'VerSize':SIZE,
        'Lan':"zh_cn",
        'Descr':"update"
    }
    table_desc = "version_desc"
    keys_desc = ','.join(data_desc.keys())
    values_desc = ','.join(['%s']*len(data_desc))
    sql_desc = "insert into {0}({1}) values({2})".format(table_desc,keys_desc,values_desc)
    mysql.execut_mysql(sql_desc,tuple(data_desc.values()))
    mysql.close_mysql()
    # try:
    #     mysql.execut_mysql('insert into version_desc(Sid,Ver,VerSize,Lan,Descr) value(%s,%s,%s,%s,%s)',
    #                        (ID, total_version, SIZE, "zh_cn", "update"))
    #     mysql.close_mysql()
    #     print("配置版本信息完成！")
    # except Exception as e:
    #     print("插入描述失败：{}".format(e))
    input_imei = input("请输入需要升级设备的imei：")
    try:
        mysql.insert_sid('insert into tactics(Sid,Ver,IsWhite,Type,Data) value(%s,%s,%s,%s,%s)',
                         (ID, total_version, 1, 1, input_imei))
        mysql.close_mysql()
    except Exception as e:
        print("插入描述失败：{}".format(e))

    t = get("http://10.1.77.36:33803/UpdateRedis")
    if t.content.decode('utf-8') == "OK":
        print("redis flush ok!")
        time.sleep(20)


if __name__ == "__main__":
    main()
    # mysql = MySql()
    # mysql.find_sid('select * from software where sid="Connect_SER_K1_2001"')
