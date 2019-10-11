#!/usr/bin/python
#coding:utf-8
from fake_useragent import UserAgent
import requests,time
import cookielib
import re
import os
import sys
import random
import math
import time
#1.获取设备列表
#2.随机选择设备
#3.判断设备是否存在monkey进程
#4.存在则重新随机，不存在则执行monkey
#开关手机wifi:adb -s 702dcbac shell svc wifi enable /adb -s 702dcbac shell svc wifi disable

ProjectName=""
APKLink=""
LastBuildNum=""
pkN = ""
apkName = ""
BL = "True"


defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)

log = None

class Log(object):
    __logfile = None
    def __init__(self, filePath, fileName):
        self.__logfile = open(filePath + os.sep + fileName, 'a+')
    def addLog(content):
        timeStr=time.ctime(time.time())
        self.__logfile.write(timeStr+"     "+content.encode('utf-8'))
        self.__logfile.write(os.linesep + '#############################' + os.linesep)
        self.__logfile.flush()
    def closeFile(self):
        self.__logfile.close()
    def setHeader(self, content):
        self.__logfile.write(content.encode('utf-8'))
        self.__logfile.write(os.linesep)
        self.__logfile.flush()
    
#print(f"user cookielib in python2.x")

session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename = "Cookies.txt")
userAgent = UserAgent().ie
#print(userAgent)
header = {
    "Referer": "http://launcher.ci.3g.net.cn/login",
    'User-Agent': userAgent,
}

def gatJenkinsCrumb(jenkinsUrl,username,password):
    crumbData = None
    try:
        crumbUrlPath = 'crumbIssuer/api/xml?xpath=concat(//crumbRequestField,":",//crumb)'
        pattern = re.compile(r'^(http://)[\w.:]+(/)')
        jenkinsHostUrl = pattern.match(jenkinsUrl).group()
        jenkinsCrumbUrl = jenkinsHostUrl + crumbUrlPath
        r_crumb = requests.get(jenkinsCrumbUrl, auth=(username, password))
        print 'r_crumb.content:%s url:%s'%(r_crumb.content, jenkinsCrumbUrl)
        crumbInfo = r_crumb.content.split(':')
        crumbKey = crumbInfo[0]
        crumbValue = crumbInfo[1]
        crumbData = {}
        crumbData[crumbKey] = crumbValue
        print crumbData
    except Exception, e:
        #logContent = 'get crumb :' + e.message
        #logContent = logContent + os.linesep + 'jenkinsUrl' + jenkinsUrl
        #lg = Log()
        #lg.addLog(logContent)
        print("Error",e)
    return crumbData

def loginGetPage(jenkinsUrl,username,password):
    global LastBuildNum
    content = ""
    try:
        print("Start login...")
        crumbData = gatJenkinsCrumb(jenkinsUrl=jenkinsUrl,username=username,password=password)
        responseRes = requests.post(jenkinsUrl,auth=(username,password),data=crumbData,headers=header)
        print(responseRes.status_code)
        #print(responseRes.text)
        content = responseRes.content
        #print("PageContent:",content)
        f = open('./HomePageContent.txt','w+')
        f.write(content)
#        f.seek(0,0) #reset point
#        while True:
#            if "Last build" in f.readline():
#                print(f.readline())
#                break
        f.close()
        str = content
        ls = str.split('Last build(#')
        LastBuildNum = ls[1].split('),')[0]
        print("Last Build:#%s" %(LastBuildNum))
        consolePageUrl = jenkinsUrl+LastBuildNum+'/console'
        print("consolePageUrl:%s" %(consolePageUrl))
        responseRes2 = requests.post(consolePageUrl,auth=(username,password),data=crumbData,headers=header)
        content2 = responseRes2.content
        g = open('./ApkPageContent.txt','w+')
        g.write(content2)
        g.close()
    except Exception, e:
        #logContent = 'other : ' + repr(e.message)
        #logContent = logContent + os.linesep + 'jenkinsUrl : ' + jenkinsUrl
        #lg = Log()
        #lg.addLog(logContent)
        print("Error:",e)

    #return content

def getApkInfo(jenkinsUrl,username,password):
    global APKLink
    loginGetPage(jenkinsUrl=jenkinsUrl,username=username,password=password) #rongyikasi,yoububaocuo
    f = open('./ApkPageContent.txt','r')
    g = open('./ApkInfo.txt','w+')
    temp=["Sending email to:","Finished:","apk size :"]
    for line in f.readlines():
        if "http://" in line and ".apk" in line:
            print("line:",line)
            APKLink = line.split("'")[1]
            print(APKLink)
            g.write("APK Link:")
            g.write(APKLink+'\n\n')
        for i in range(0,len(temp)):
            if temp[i] in line :
                g.write(line+'\n')
    
    f.close()
    g.close()

def DevicesGet():
    devices = []
    os.system("adb devices >> ./devices.txt")
    f = open("./devices.txt",'r')
    n = len(f.readlines())
    #print(f.readlines())
    f.close()
    g = open("./devices.txt",'r')
    for i in range(0,n):
        s = g.readline()
        if "List of devices attached" in s:
            continue
        elif s == '':
            continue
        elif s == '\n':
            continue
        else:
            devices.append(s.split('\t')[0])
    print("Devices list:",devices)
    g.close()
    os.system("rm ./devices.txt")
    return devices
def monkey_Device():
    global BL
    dv = DevicesGet()
    if dv != []:
    	n = []
    	for i in range(0,len(dv)):
            while True:
            	num = int(math.floor(random.random()*len(dv)))
            	if num not in n:
                    n.append(num)
                    break
            	else:
                    continue
            str = os.popen("adb -s %s shell ps|grep com.android.commands.monkey" %dv[num]).read()
            if str == '':
            	print("Selected device:",dv[num])
            	return dv[num]
            	break
            else:
            	if i == len(dv)-1:
                     BL = "False"
            	print("%s existed monkey Thread !!" %dv[num])
            	continue
    else:
	BL = "False"
	print("Devices list is empty!")

def downloadApk(username,password):
    global BL
    if BL == "True":
        os.system("touch BuildNum.txt")
        f = open("./BuildNum.txt","r")
        if f.readline() != LastBuildNum:
            try:
                f.close()
                g = open("./BuildNum.txt","w+")
                g.write(LastBuildNum)
                g.close()
                filename = "Test.apk"
                print("APKDownloadLink:%s" %APKLink)
                file = requests.get(APKLink,auth=(username,password))
                apk = open(filename,'wb+')
                apk.write(file.content)
                apk.close()
                print("Download APK Success")
            except Exception, e:
                print("Download APK Fail:",e)
                BL = "False"
        else:
            print("No new version, give up downloading！")
            BL = "False"
    else:
        print("No devices free,give up downloading! ")


def device_Info(device):
    global BL
    if BL == "True":
        Info = []
        #print("中文测试"+os.popen("adb -s %s shell getprop ro.build.version.release" %device).read())
        Info.append(os.popen("adb -s %s shell getprop ro.build.version.release" %device).read()) #版本
        Info.append(os.popen("adb -s %s shell getprop ro.product.brand" %device).read()) #品牌
        Info.append(os.popen("adb -s %s shell getprop ro.product.name" %device).read()) #设备名
        Info.append(os.popen("adb -s %s shell getprop ro.product.board" %device).read()) #处理器
        Info.append(os.popen("adb -s %s shell getprop ro.product.model" %device).read()) #型号
        Info.append(os.popen("adb -s %s shell dumpsys battery|grep level" %device).read().split(': ')[1])    #电量
        Info.append(os.popen("adb -s %s shell wm size" %device).read().split(': ')[1].split('\n')[0]+'\n')  #分别率
	try:
            Info.append(os.popen("adb -s %s shell dumpsys meminfo|grep 'Total RAM:'" %device).read().split(': ')[1].split(' (')[0]+'\n')    #总内存
            Info.append(os.popen("adb -s %s shell dumpsys meminfo|grep 'Free RAM'" %device).read().split(': ')[1].split(' (')[0]+'\n') #剩余内存
	except Exception,e:
	    print("get RAM fail,Igrone!!")
        print(Info)
        name = ["版本：","品牌：","设备名：","处理器：","型号：","电量：","分别率：","总内存：","剩余内存："]
        f = open('./DeviceInfo.txt','w+')
        for i in range(0,len(Info)):
            f.write(name[i]+Info[i])
        f.close()
    else:
        print("Not need,give up device_Info!! ")
def package_Info():
    global pkN
    global apkName
    dir = "./"
    Info = []
    files = os.listdir(dir)
    for i in range(1,len(files)):
        if os.path.splitext(files[i])[1] == ".apk":
            apkName = files[i]
            print("APK:%s" %files[i])
            break
    Info.append(os.popen("aapt dump badging %s|grep 'application-label-en:'" %apkName).read().split(':')[1].split('\n')[0])   #应用名
    Info.append(os.popen("aapt dump badging %s|grep 'package: name='" %apkName).read().split("'")[1])   #包名
    Info.append(os.popen("aapt dump badging %s|grep 'package: name='" %apkName).read().split("'")[3])  #版本号
    Info.append(os.popen("aapt dump badging %s|grep 'package: name='" %apkName).read().split("'")[5])  #版本名
    print(Info)
    pkN = Info[1]
    name = ["应用名: ","包名: ","版本号: ","版本名: "]
    f = open('./ApkInfo.txt','a+')
    for i in range(0,4):
        f.write(name[i]+Info[i]+'\n')
    f.close()

def install_APK(device):
    global BL
    if BL == "True":
        try:
            os.system("adb uninstall %s" %pkN)
            print("installing APK !!")
            os.system("adb -s %s install -r %s" %(device,apkName))
        except Exception, e:
            print("install fail !!")
            f = open("./install_fail_log.txt","w")
            f.write(e)
            f.close()
            BL = "False"
    else:
        print("Not need,give up install! ")

def monkey_Start(device,path):
    global BL
    os.system("rm monkey_log.txt")
    os.system("adb -s %s shell rm -r %s" %(device,path))
    if BL == "False":
        print("Not need, give up monkey!!")
    else:
        print("monkey device:%s" %device)
        print("monkey Start...")
        try:
            os.system("adb -s %s shell monkey -p %s --ignore-crashes --ignore-timeouts --monitor-native-crashes -v -v -v 500 >> monkey_log.txt" %(device,pkN))
        except Exception, e:
            print("monkey fail !!")
            f = open("./monkey_fail_log.txt","w")
            f.write(e)
            f.close()
            BL = "False"

def monkey_Info():
    global BL
    stats = ""
    Info = []
    if BL == "False":
        print("Not need, give up monkey_Info!!")
    else:
        f = open("./monkey_log.txt","r")
        for line in f.readlines():
            if "Network stats:" in line:
                stats = line
                break
            else:
                continue
        f.close()
        name = ["总运行时间：","数据流量：","无线网：","无网络连接："]
        Info.append(stats.split('time=')[1].split(' (')[0])
        Info.append(stats.split(' (')[1].split(' mobile')[0])
        Info.append(stats.split('mobile, ')[1].split(' wifi')[0])
        Info.append(stats.split('wifi, ')[1].split(' not connected')[0])
        print(Info)
        g = open('./MonkeyInfo.txt','w+')
        for i in range(0,4):
            g.write(name[i]+Info[i]+'\n')
        g.close()
def crash_anr_get(device,path,crashN):
    global BL
    if BL == "False":
        print("No new crash and anr!!")
    else:
        erro = 0
        os.system("mkdir anr anr2 %s" %crashN)
        #os.system("mkdir anr&&mkdir anr2&&mkdir %s" %crashN)
        os.system("rm -r anr2/* %s/*" %crashN)
        files = os.listdir("./anr")
        os.system("adb -s %s pull /data/anr ./" %device)
        os.system("adb -s %s pull %s ./" %(device,path))
        os.system("adb -s %s shell rm -r %s" %(device,path))
        dir1 = "./anr"
        dir2 = crashN
        files1 = os.listdir(dir1)
        files2 = os.listdir(dir2)
        #f.write("ANR: "+str(len(files1)-len(files))+'\n')
        for i in range(0,len(files1)):
            if files1[i] not in files:
                os.system("cp ./anr/%s ./anr2" %files1[i])
            else:
                continue
        f = open("./MonkeyInfo.txt","a+")
        f.write("ANR: "+str(len(os.listdir("./anr2")))+'\n')
        f.write("CRASH："+str(len(files2))+'\n')
        erro = len(os.listdir("./anr2"))+len(files2)
        g = open("./error.txt","w+")
        g.write(str(erro))
        g.close()
        f.close()
def send_Email():
    global BL
    usr = ["raomingqiang@gomo.com,raomm88@gmail.com,qiangqiang310@gmail.com,raomingqiang123@163.com"]
    dev = ["raomingqiang@gomo.com"]
    if BL == "False":
        f = open("Email.txt","w+")
        f.write(dev[0])
        f.close()
    else:
        f = open("Email.txt","w+")
        f.write(usr[0])
        f.close()


def AutoTestStart():
    device = monkey_Device()
    path = "sdcard/GOMusic/logs"
    crashN = "logs"
    downloadApk(username,password)
    package_Info()
    device_Info(device)
    install_APK(device)
    monkey_Start(device,path)
    monkey_Info()
    crash_anr_get(device,path,crashN)
    send_Email()



if __name__ == "__main__":
    jenkinsUrl = "http://launcher.ci.3g.net.cn/job/build_gomusic_1.0/"
    username = "raomingqiang"
    password = "Hello123"
    getApkInfo(jenkinsUrl,username,password)
    AutoTestStart()

#os.system("adb -s %s shell monkey -p com.jiubang.go.music --ignore-crashes --ignore-timeouts --monitor-native-crashes -v -v 1000" %device)
#adb -s 702dcbac shell monkey -p com.jiubang.go.music  --ignore-crashes --ignore-timeouts --monitor-native-crashes -v -v 100 >>home/Documents/music_monkey_log.txt
#adb -s 702dcbac shell pm list packages
