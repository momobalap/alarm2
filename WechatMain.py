#! /usr/bin/env python
# -*- coding: utf-8 -*-
# By : peterlin@royole.com
# Ver:1.3 2019/08/26 peter--due to connection fail, add exception handling, detail log and retrying codes 

#from PyFetion import *
from AlarmUtil import *
from threading import Thread
from time import sleep
from copy import copy
from datetime import datetime
import time
import sys
#import exceptions
import logging
import logging.config
import traceback
import urllib, urllib.request
import json
#import itchat
import schedule

lasttime = datetime.now()
tokentime=datetime.now()
corpid = 'ww4c1e3dab3f093bad'  # CorpID是企业号的标识
corpsecret = '_r53YrYrO0envJOqxqz3yrlIkZfDA9E1ZCZucjXTOv8'  # corpsecretSecret是管理组凭证密钥
callNums = 0
gettoken_cnt=0
applications=[]
tokens={}
token=None
logging.config.fileConfig("logger.conf")
logger = logging.getLogger("rotate")
logger.debug('start')

status=""
user=""
username=""
stopWatchdog=False

class AlarmApp:
     def __init__(self,corpid,secret,agentid):
         self.corpid=corpid
         self.secret=secret
         self.agentid=agentid
         self.token=None

     def gettoken(self):
         gettoken_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=' + self.corpid + '&corpsecret=' + self.secret
         try:
             token_file = urllib.request.urlopen(gettoken_url)
         except urllib.request.HTTPError as e:
             msg = traceback.format_exc()
             logger.error(msg)
             raise Exception("get token fail")
         except Exception as ex:
             msg = traceback.format_exc()
             logger.error(msg)
             raise Exception("get token fail") 		 
         token_data = token_file.read().decode('utf-8')
         token_json = json.loads(token_data)
         token_json.keys()
         token = token_json['access_token']
         return token

     def send_messages(self, data):
         try:
             msg=self.messages(data)
             send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + self.token
             # send_url = '%s/cgi-bin/message/send?access_token=%s' % (url, token)
             response = urllib.request.urlopen(urllib.request.Request(url=send_url, data=msg)).read()
             r=json.loads(response.decode())
             x=r['errcode']
             errmsg=r['errmsg']
             # print(x)
             if x == 0:
             #print(response)
                 return 0
             else:
                 logger.debug("error " + errmsg)
                 return x
         except Exception as ex:
             raise Exception(str(ex))

     def initToken(self):
         try:
         	   self.token=self.gettoken()
         except Exception as ex:
         	   raise(Exception(str(ex)))	   

     def messages(self,msg):
         values = {
             "touser": '@all',
             "msgtype": 'text',
             "agentid": self.agentid,  # 偷懒没有使用变量了，注意修改为对应应用的agentid
             "text": {'content': msg},
             "safe": 0
         }
         msges = (bytes(json.dumps(values), 'utf-8'))
         return msges


# def sendWeChatMsg(msg):
#     global status
#     global user,username
#     logger.debug("status: "+ status + " call sendWeChatMsg")
#     try:
#         if status=='DOWN':
#             logger.error("status: "+ status + " send...")
#             return
#             loginchat()
#             x=getChat()
#             if x=='':
#                 logger.error("not get username")
#                 return False
#             else:
#                 user=x
#         logger.debug("status: "+ status + " send...")
#         if username=='Peter':
#             user='filehelper'
#         rtn = itchat.send(msg, toUserName=user)
#         if rtn['BaseResponse']['Ret']==0:
#             logger.debug("status: "+ status + " send ok")
#             status = 'RUN'
#             return True
#         else:
#             logger.debug("status: "+ status  + " send fail " +  rtn.__str__() )
#             status='DOWN'
#             return False
#
#
#     except Exception as e:
#         status='DOWN'
#         tmpmsg=traceback.format_exc()
#         logger.error(tmpmsg)
#         return False


def rest():
    logger.debug("status: "+ status  + " call rest")
    print('process is running')
    #logger.debug('[rest]process is running')

def updateWatchDog():
    global lasttime
    checktime = datetime.now()
    d = checktime - lasttime
    print('update Watch seconds:' + str(d.seconds))
    if d.seconds >= 90:
        lasttime = checktime
        print('>90')
        updateExecTime()
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        print(now_time + ' update watchdog')

def CheckTimeIfOverGetNewToken():
    global tokentime,tokens,gettoken_cnt,stopWatchdog
    checktime=datetime.now()
    d=checktime-tokentime
    if d.seconds>=6000:
        try:
            for key in tokens:
                tokens[key].initToken()
            tokentime=checktime
            gettoken_cnt=gettoken_cnt+1
            #token = gettoken(corpid, corpsecret)
            logger.debug("get new token. Counts:" + str(gettoken_cnt))
            stopWatchdog=False
        except Exception as ex:
            logger.error("get token fail")
            stopWatchdog=True
            raise Exception(str(ex))        	

def handleMsg():
    global user,status,token,applications,username,tokens

    lasttime = datetime.now()
    logger.debug('begin query smsdata')
    smsDataList = querySmsDataBypyOdbc2(logger)
    logger.debug('after get smsdata')
    if smsDataList:
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        # self.llog.debug('fetion_alram_service->sleep after get data')
        for d in smsDataList:
            #print('send msg to ' + d[0].encode('utf-8'))
            print('send msg to ' + d[0])
            now_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))  # add by peter ,now_time not declare
            logger.debug(now_time + '--send msg to ' + d[0] + '--msg:' + d[1])
            ### add search user code here
            try:
                if tokens.__contains__(d[0]):
                    # handle 微信企业CIM服务
                    #msgsent = messages(d[1], d[0])
                    isOk =tokens[d[0]].send_messages(d[1])
                    if isOk != 0:
                        processSendFailMsg(d[2])
                    else:
                        processSendOkMsg(d[2])
                        print(d[0] + '--success')
                        now_time = time.strftime('%Y-%m-%d %H:%M:%S',
                                                 time.localtime(time.time()))  # add by peter ,now_time not declare
                        logger.debug(now_time + d[0] + '--send wechatGroup success')
                    continue
                username=d[0]
                msgStr = d[1][:560]
                print("msgStr:" + msgStr)
                print("send to:" + d[0])
                # #send to wechat
                # if not sendWeChatMsg(msgStr):
                #     processSendFailMsg(d[2])
                #     # processSendLimit(str(self.phone.mobile_no))
                #     now_time = time.strftime('%Y-%m-%d %H:%M:%S',
                #                                  time.localtime(time.time()))  # add by peter ,now_time not declare
                #     logger.debug(now_time + d[0] + '--send sms fail !')
                #     print(d[0] + '--send sms fail !')
                #     # os.system('D:\\EMS\\PyFetion\\watchdogManager.bat')
                #     body = subject = now_time + ' send Wechat fail..msg will be delayed'
                #     logger.error(body)
                #     #sendMailEx(subject, body)
                #     #sys.exit(0)  20181120 disable by peter
                # else:
                #     processSendOkMsg(d[2])
                #     print(d[0] + '--success')
                #     now_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))  # add by peter ,now_time not declare
                #     logger.debug(now_time + d[0] + '--send success')
            except Exception as e:
                tmpmsg = traceback.format_exc()
                logger.error(tmpmsg)
                print("send error:", tmpmsg)
                # os.system('D:\\EMS\\PyFetion\\watchdogManager.bat')
                now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                body = subject = now_time + ' send sms exception exit! sms will be delayed and raise exception'
                logger.error(body)
                raise(Exception("send message fail") )
        updateWatchDog()
                #sendMailEx(subject, body)
                #sys.exit(0)



def selfTest():
    global stopWatchdog
    try:
        CheckTimeIfOverGetNewToken()
        logger.info("send test")
        isOk = tokens['1000002'].send_messages("Plz Ignore! Alarm healthy test....")
        if isOk != 0:
            logger.info("Self test fail!")
    except Exception as ex:
        logger.error(str(ex))
        logger.error("selfTest stop wathdog!")
        stopWatchdog=True
       
def main():
    global stopWatchdog
    cnt = checkSMSListCount()
    if cnt > 0:
        if stopWatchdog==True:
            logger.info("stop handle message under stopwatchdog")
        else:
            try:
                CheckTimeIfOverGetNewToken()
                handleMsg()
            except Exception as ex:
                logger.error("stopWachdog!")      
                logger.error(str(ex))
                stopWatchdog=True              
    elif cnt == 0:
        #logger.error("fail")
        if stopWatchdog==False:
            updateWatchDog()
            print('no data found!!')
        else:
            print('Under stopWatchdog....')

def iniTokens():
    global tokens,stopWatchdog
    try:
        bcApp=AlarmApp('ww4c1e3dab3f093bad','daKLWNjNP2tjhKc2vKtQFbuIhHdA41DGlZkPJ1JopuQ','1000003')
        bcApp.initToken()
        tokens[bcApp.agentid]=bcApp
        mesApp=AlarmApp('ww4c1e3dab3f093bad','z4snjBWk0VU-y2A4v3lD2CjT0hzIAaYca7DcPioCZBc','1000005')
        mesApp.initToken()
        tokens[mesApp.agentid] = mesApp
        reportApp=AlarmApp('ww4c1e3dab3f093bad','oLILZXKKmkBcbF5VGeexOig5ccY2H4bU9OpQfB0bLSw','1000004')
        reportApp.initToken()
        tokens[reportApp.agentid] = reportApp
        mcsApp = AlarmApp('ww4c1e3dab3f093bad', 'tP1vlSPd4WGZQJurZFykulukWBatabsOTKBc7_KOcGo', '1000006')
        mcsApp.initToken()
        tokens[mcsApp.agentid] = mcsApp
        cimApp=AlarmApp('ww4c1e3dab3f093bad', '_r53YrYrO0envJOqxqz3yrlIkZfDA9E1ZCZucjXTOv8', '1000002')
        cimApp.initToken()
        tokens[cimApp.agentid] = cimApp
        upsApp = AlarmApp('ww4c1e3dab3f093bad', 'AQsuKupcTMriL_rG2h4XTaFzCOHKf_IKd8HdLvSNaPE', '1000007')
        upsApp.initToken()
        tokens[upsApp.agentid] = upsApp
        electricApp = AlarmApp('ww4c1e3dab3f093bad', '4WW00o2qmPdjTdL32P6etSznYTYbOohvFlVwgBBcBmQ', '1000008')
        electricApp.initToken()
        tokens[electricApp.agentid] = electricApp
        cdsApp = AlarmApp('ww4c1e3dab3f093bad', 'fOxSSLYHMD2f8ehXiXAojwmTfKj4s6jwNuvQhCB8DEI', '1000009')
        cdsApp.initToken()
        tokens[cdsApp.agentid] = cdsApp
        cr1App = AlarmApp('ww4c1e3dab3f093bad', 'zigrApv18RuWGO1NKo1Mi35QwaBAJMJTl8DEjEOrXrs', '1000010')
        cr1App.initToken()
        tokens[cr1App.agentid] = cr1App
        cr2App = AlarmApp('ww4c1e3dab3f093bad', 'MRlEm1MsrZYxtK7qx6-Bn5qu-RF4216ohm1Qvl7TGRg', '1000011')
        cr2App.initToken()
        tokens[cr2App.agentid] = cr2App
        exhApp = AlarmApp('ww4c1e3dab3f093bad', 'BD9SPzbySfASpBQTaD_JHuJKT3haqtVbvMdkNVnYmV4', '1000012')
        exhApp.initToken()
        tokens[exhApp.agentid] = exhApp
        gmsApp = AlarmApp('ww4c1e3dab3f093bad', 'iV3LKBMjYCKOLxAHnkWCBnbIT25ekMGlloqLmx4CIRY', '1000013')
        gmsApp.initToken()
        tokens[gmsApp.agentid] = gmsApp
        ma1App = AlarmApp('ww4c1e3dab3f093bad', '46mDsI-RsooCTOTW48yWU72FyZPjvxr0ivAGRoccGf4', '1000014')
        ma1App.initToken()
        tokens[ma1App.agentid] = ma1App
        ma2App = AlarmApp('ww4c1e3dab3f093bad', '6Y4kuSdQPWaI5aChFQOTYXO3WzPHyHAcJYOA7rk-DKk', '1000015')
        ma2App.initToken()
        tokens[ma2App.agentid] = ma2App
        pcwApp = AlarmApp('ww4c1e3dab3f093bad', 'XoW1C2njz1gRCiv6S3Ia9oBwWwIMCflzyJCMvM2gBNw', '1000016')
        pcwApp.initToken()
        tokens[pcwApp.agentid] = pcwApp
        upwApp = AlarmApp('ww4c1e3dab3f093bad', '2trqG0siC0goVgUTGNwFXViI9ALf6As9g8XfL6gFUI0', '1000017')
        upwApp.initToken()
        tokens[upwApp.agentid] = upwApp
        wwtApp = AlarmApp('ww4c1e3dab3f093bad', '5Aa6C0pVBFmoDP81X4cWrfqKX4j9nE2YpsVQ4W9Ok6U', '1000018')
        wwtApp.initToken()
        tokens[wwtApp.agentid] = wwtApp
        tempApp = AlarmApp('ww4c1e3dab3f093bad', 'FnfN_DfpB_H-RPbmG6j4-jG9ic7J-o5dt5UY-7AjE9c', '1000019')
        tempApp.initToken()
        tokens[tempApp.agentid] = tempApp
        cr3App = AlarmApp('ww4c1e3dab3f093bad', 'FgE2b08hy1etqfzgFeouuz893-E9u_2jwJa5R25bMTU', '1000020')
        cr3App.initToken()
        tokens[cr3App.agentid] = cr3App
        cdapvApp = AlarmApp('ww4c1e3dab3f093bad', 'eoWU2LbepRHA-QHsBk7X-JgRtNxbQVqT7NVeSlyr98g', '1000021')
        cdapvApp.initToken()
        tokens[cdapvApp.agentid] = cdapvApp
        cgsApp = AlarmApp('ww4c1e3dab3f093bad', 'akbwSmtAaoUJ7rbgCJZ6YPn-ZFZ9gkkTd-iUkGRr_Bw', '1000022')
        cgsApp.initToken()
        tokens[cgsApp.agentid] = cgsApp
        faApp = AlarmApp('ww4c1e3dab3f093bad', 'qzezQvIh0M0j6RqKxa7qEmn55r7jN7N3VyV4_G4xj2U', '1000023')
        faApp.initToken()
        tokens[faApp.agentid] = faApp
    except Exception as ex:
        logger.error("initoken from beginning fail!")
        stopWatchdog=True 

if __name__ == "__main__":
    logger.info("begin..")
    #applications.append('1000002')
    iniTokens()
    initPid()
    #itchat.auto_login(hotReload=False)
    status='RUN'
    myself='filehelper'
    #myself=getChat('Peter')
    #if myself=='':
    #    logger.error('cannot get Peter')
    #schedule.every(1).day.at("19:10").do(pushinfo)
    schedule.every(1).minutes.do(main)
    #schedule.every(3).minutes.do(loginchat)
    schedule.every(60).minutes.do(selfTest)
    while True:
        schedule.run_pending()
