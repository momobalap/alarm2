from subprocess import Popen
from threading import Thread
import time
import pyodbc
import os
import logging
import logging.handlers
import psutil
import sys

def initLog():   
    #logHandler=logging.handlers.RotatingFileHandler('../PyFetionLog/cdy.log', maxBytes=10*1024*1024,backupCount=5)    
    #formatter = logging.Formatter('%(asctime)-15s %(name)-5s %(levelname)-8s %(message)s')	
    #logHandler.setFormatter(formatter)
    #logger.addHandler(logHandler)
    #logger.setLevel(logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG,
                       format="%(asctime)-15s %(name)-5s %(levelname)-8s %(message)s",
                       filename='../WechatLog/manager.log')
    logger = logging.getLogger("manager")
    logger.debug('start')	
    return logger   

def checkSecondRun():
    isFound=False
    cnt=0
    lst = psutil.pids()
    
    for l in lst:
        print(l)
        p=psutil.Process(l)
        print(p.name)
        try:
            print('process_cmdline=%s'% p.cmdline())
            if len(p.cmdline())>1:
                print(p.cmdline()[1])
                if p.cmdline()[1]=='manager.py':
                    cnt=cnt+1
        except Exception as ex:
        	  print(str(ex))
       
    if cnt>1:
        isFound=True  	
    return isFound        

class ProcessManager(Thread):
    def __init__(self,log):
        self.isLive=True
        self.log=log
        self.p=None
        self.lst=[]
        Thread.__init__(self)
        
    def checkZombie(self):
        global conn 
        try:
            conn=pyodbc.connect("DRIVER={SQL Server};SERVER=10.9.255.57;DATABASE=EMS;UID=EMSADM;PWD=royo!EMS123") 
            cur=conn.cursor()
            sql = "SELECT  PID FROM WATCHDOG  where  TargetName='{0}' and datediff(ss,updatetime , getdate())>600".format("wechatApp")
            cur.execute(sql)    
            result  = cur.fetchone() 
            return result 
        except Exception as e:
            print(str(e))
            return None
        finally:
            conn.close()				
                  
		
    def run(self):
        while(self.isLive):
            result=self.checkZombie()
            now_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
            if result:
                # kill this process result[0]
                #os.kill(result[0],-9)
                self.log.debug(now_time + ' taskkill /f /pid ' + str(result[0]))				
                os.system('taskkill /f /pid ' + str(result[0]))
                                
                print(now_time + ' restart wechatApp')
                #os.system('D:\\EMS\\PyFetion\\fetionCDY.bat')
                self.p=Popen(['python','./WechatMain.py',''],shell=False)
                self.log.debug(now_time+ ' p.pid=' + str(self.p.pid))
            else:
                print (now_time + ' checkZombie ok' )	
            time.sleep(30)	
    def stop(self):
        self.isLive=False

	
if __name__=='__main__':
    now_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    olog = initLog()
    olog.debug('Watchdog Manager inilizing ....')
    isSecondRun=checkSecondRun()
    if isSecondRun:
        olog.debug(now_time + ' second run found')
        sys.exit()
    t=ProcessManager(olog)
    t.start()
    t.join()
    print('Wechat manager Exit!')
	
