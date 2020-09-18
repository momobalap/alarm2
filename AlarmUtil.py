# -*- coding: utf-8 -*-
# coding=utf-8
from __future__ import with_statement
from contextlib import closing
import os
import sys
import logging
import smtplib
import string
import pyodbc
import time
import psutil


# 随机获取发送飞信的手机号码和密码
def getArandomSmsCode():
    global conn
    try:
        conn = pyodbc.connect("DSN=pyOdbc;UID=sa;PWD=feiyezi007")
        cur = conn.cursor()
        sql = """select sms_server_id,sms_server_key,sms_callNum from cim_cofg_sms where status = 1 and sms_callNum<500 and total_qty<10000 order by sms_callNum """
        cur.execute(sql)
        dataResult = cur.fetchone()
        print(dataResult)
        return dataResult
    except Exception as  e:
        return None
    finally:
        conn.close()
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))


def getCPUstate(interval=1):
    p = psutil.Process(os.getpid())
    return p.get_cpu_percent(interval)


def sendMail(subject, body, TO, FROM):
    # HOST = "localhost"
    s = ""
    for t in TO:
        if s == "":
            s = t
        else:
            s = s + ',' + t
    BODY = string.join((
        "From: %s" % FROM,
        "To: %s" % s,
        "Subject: %s" % subject,
        "",
        body
    ), "\r\n")
    server = smtplib.SMTP('172.30.130.61')
    server.set_debuglevel(1)
    server.sendmail(FROM, TO, BODY)
    server.quit()


def sendMailEx(subject, body):
    toAddr = ["peter.lin@ebbg-ww.com"]
    fromAddr = ["fetionmanager@ebbg-ww.com"]
    sendMail(subject, body, toAddr, fromAddr)


def initPid():
    global conn
    try:
        pid = os.getpid()
        conn = pyodbc.connect("DRIVER={SQL Server};SERVER=10.9.255.57;DATABASE=EMS;UID=EMSADM;PWD=royo!EMS123")
        cur = conn.cursor()
        sql = "delete from WATCHDOG where TargetName='WechatApp'"
        cur.execute(sql)
        conn.commit()

        sql = "insert into WATCHDOG (TargetName,PID,RefAppName) values("
        sql = sql + "'" + "WechatApp" + "',"
        sql = sql + str(pid) + ","
        sql = sql + "'" + "No" + "')"
        cur.execute(sql)
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        conn.close()


def updateExecTime():
    global conn
    try:
        conn = pyodbc.connect("DRIVER={SQL Server};SERVER=10.9.255.57;DATABASE=EMS;UID=EMSADM;PWD=royo!EMS123")
        cur = conn.cursor()
        sql = "UPDATE WATCHDOG set UpdateTime = getdate()  where TargetName='WechatApp'"
        cur.execute(sql)
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        conn.close()


# 查找SMS_LIST里面需要发送的数据
def querySmsDataBypyOdbc():
    global conn
    smsDataList = []
    try:
        conn = pyodbc.connect("DSN=pyOdbc;UID=sa;PWD=feiyezi007")
        cur = conn.cursor()

        sql = 'delete from sms_list where error_count >3 '
        cur.execute(sql)
        conn.commit()

        sql = """SELECT  code , smsmsg ,itemindex   FROM sms_list   order by issue_date_time asc"""
        cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        print(e)
    finally:
        conn.close()
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        print(now_time + '============================================= wait for service ')


# 查找SMS_LIST里面需要发送的数据
def querySmsDataBypyOdbc2(log):
    global conn
    smsDataList = []
    try:
        log.debug('this is first')
        #conn = pyodbc.connect("DSN=pyOdbc;UID=sa;PWD=feiyezi007")  #'DRIVER={SQL Server};SERVER=localhost;DATABASE=test;UID=sa;PWD=Wxp19910323'
        conn = pyodbc.connect("DRIVER={SQL Server};SERVER=10.9.255.57;DATABASE=EMS;UID=EMSADM;PWD=royo!EMS123")
        cur = conn.cursor()
        sql = 'delete from sms_list where error_count >3 '
        cur.execute(sql)
        conn.commit()
        log.debug('delete ok')
        sql = """SELECT  code , smsmsg ,itemindex   FROM sms_list   order by issue_date_time asc """
        log.debug('before select')
        cur.execute(sql)
        return cur.fetchall()
    except Exception as e:
        print(e)
        log.debug('SMS_LIST error ' + str(e))
    finally:
        conn.close()
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        print(now_time + '============================================= wait for service ')


# 处理发送失败的信息 1.发送三次失败将被删除
def processSendFailMsg(itemindex):
    global conn
    try:
        conn = pyodbc.connect("DRIVER={SQL Server};SERVER=10.9.255.57;DATABASE=EMS;UID=EMSADM;PWD=royo!EMS123")
        cur = conn.cursor()
        sql = "UPDATE sms_list set error_count = error_count + 1  where itemindex = '" + itemindex + "'"
        print("send fail , error count +1")
        cur.execute(sql)
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        conn.close()


def processNotInContactList(sender, sendto):
    global conn
    try:
        conn = pyodbc.connect("DSN=pyOdbc;UID=sa;PWD=feiyezi007")
        cur = conn.cursor()
        sql = "insert into H_SMS_FAIL (send_to,send_from,lm_time) values("
        sql = sql + "'" + sendto + "',"
        sql = sql + "'" + sender + "',"
        sql = sql + "getdate() )"
        cur.execute(sql)
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        conn.close()


# 处理发送成功的信息：1. 日、月累计发送信息的条数加一  2.删除已经发送的信息 3.如果达到日或者月的最大值 将重新选择号码发送
def processSendOkMsg(itemindex):
    global conn
    try:
        print('connect DB')
        conn = pyodbc.connect("DRIVER={SQL Server};SERVER=10.9.255.57;DATABASE=EMS;UID=EMSADM;PWD=royo!EMS123")
        cur = conn.cursor()

        # write history
        try:
            sql = "INSERT INTO SMS_HISTORY"
            sql = sql + "(TID,CODE,USERINDEX,SENDER,ACTION,CONTENT,ISSUE_DATE_TIME,DEADLINE,SMSMSG,EVENTINDEX "
            sql = sql + ",RID,JOBFLG,TOOLID,ALARMCODE,EVENTLEVEL,NEEDCLOSE "
            sql = sql + ",itemindex,lm_time,error_count) "
            sql = sql + "select TID,CODE,USERINDEX,SENDER,ACTION,CONTENT,ISSUE_DATE_TIME,DEADLINE,SMSMSG,EVENTINDEX "
            sql = sql + ",RID,JOBFLG,TOOLID,ALARMCODE,EVENTLEVEL,NEEDCLOSE "
            sql = sql + ",itemindex,lm_time,error_count from sms_list where itemindex = '" + itemindex + "'"
            cur.execute(sql)
            conn.commit()
            print('after moving to history')
        except Exception as e:
            print(e)
            # delete msg
        sql = "delete FROM sms_list where itemindex = '" + itemindex + "'"
        print('delete success !')
        cur.execute(sql)
        print('1')
        conn.commit()



    except Exception as e:
        print(e)
    finally:
        conn.close()


# 自动检查飞信的状态，如果SMS_LIST table里面有20分钟以前的信息没有发送的话，程序将重启
def checkFetionStatus():
    global conn
    global work_status
    try:
        conn = pyodbc.connect("DSN=pyOdbc;UID=sa;PWD=feiyezi007")
        cur = conn.cursor()
        sql = """SELECT  itemindex FROM sms_list  where  datediff(mi,issue_date_time , getdate())>20 """
        cur.execute(sql)
        results = cur.fetchall()
        if results:
            work_status = False  # smsDataList.app
        else:
            work_status = True
        return work_status
    except Exception as e:
        print(e)
        return False
    finally:
        conn.close()
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        print(now_time + '============================================= fetion work status: ' + str(work_status))


def checkSMSListCount():
    global conn
    global cnt
    try:
        cnt = 0
        conn = pyodbc.connect("DRIVER={SQL Server};SERVER=10.9.255.57;DATABASE=EMS;UID=EMSADM;PWD=royo!EMS123")
        cur = conn.cursor()
        sql = """SELECT  count(itemindex) as cnt  FROM sms_list """
        cur.execute(sql)
        results = cur.fetchone()
        if not results:
            print('not result')  # smsDataList.app
        else:
            cnt = results[0]
        return cnt
    except Exception as e:
        print(e)
        return 0
    finally:
        conn.close()


def processLoginfail(mobile_no):
    global conn
    try:
        conn = pyodbc.connect("DSN=pyOdbc;UID=sa;PWD=feiyezi007")
        cur = conn.cursor()
        sql = "update cim_cofg_sms set status = 0,lm_time=getdate(),lm_user='EMS_Background'  where sms_server_id='" + mobile_no + "'"
        cur.execute(sql)
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        conn.close()


def processNoticeSMScodeError(cd, msg):
    # msg = "moon test ,code need check login code !"
    insertSql = "insert into subject_data(content,http,date_time,eventid,sender,deadline,phonemsg,informtype,msg_key,siteid, toolid,alarmcode,detailmsg,mailsubject,mailbody,smsbody)"
    insertSql += " values(    'test','',getdate(),'SMS_FAIL_NOTICE','Python',getdate(),'',0,'','1T','','XXXX','','SMS Code Login Need Check Code.','" + msg + "','" + msg + "')"
    # insertSql = " INSERT INTO SMS_LIST (TID,CODE ,USERINDEX,SENDER,ACTION,CONTENT,ISSUE_DATE_TIME ,DEADLINE ,SMSMSG ,EVENTINDEX,JOBFLG,TOOLID ,ALARMCODE ,EVENTLEVEL,NEEDCLOSE) "
    # VALUES( '00','"+cd+"','1','1',3,'1',getdate(),getdate(),'"+msg+"','1','1','1','0','4','0' )"
    global conn
    try:
        conn = pyodbc.connect("DSN=pyOdbc;UID=sa;PWD=feiyezi007")
        cur = conn.cursor()
        cur.execute(insertSql)
        conn.commit()
        processShowMsgDeskop(msg)
    except Exception as e:
        print(e)
    finally:
        conn.close()


def processShowMsgDeskop(msg):
    ipList = []
    ipList.append("172.30.31.23")
    ipList.append("172.30.31.203")
    ipList.append("172.30.31.207")
    ipList.append("172.30.31.125")
    for ip in ipList:
        pingResult = os.system("ping -n 1 " + ip)
        if pingResult == 0:
            try:
                os.system(" net send " + ip + "  \"" + msg + "\"")
            except Exception as e:
                pass
        else:
            pass

