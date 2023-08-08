import re
import string
import random
from random import randint
import numpy as np
import glob
import os
import sys
import json
import shutil
import datetime
import time
import codecs  # 将ansi编码的文件转为utf-8编码的文件
import os
import django
import sys
# 模糊查询
import difflib
from collections import Counter
# 排序
from operator import itemgetter
from itertools import groupby
from androguard.misc import AnalyzeAPK

sys.path.append('../')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mwep.settings')

django.setup()

from common import models
from django.db.models import Q


def read_features_num():
    """
    读取知识图谱上的特征数
    """
    ans1 = models.augmenTestNode.objects.values('perList')
    ans1 = list(ans1)
    len1 = ''
    ans2 = models.augmenTestNode.objects.values('apiList')
    ans2 = list(ans2)
    len2 = ''
    for one in ans1:
        if one['perList'] != '':
            len1 = len1 + ',' + one['perList']
    len1 = list(set(len1.split(',')))
    list1 = len1[1:]
    print('per nums:', len(list1))
    for one in ans2:
        if one['apiList'] != '':
            len2 = len2 + ',' + one['apiList']
    len2 = list(set(len2.split(',')))
    list2 = len2[1:]
    print('api nums:', len(list2))

    return len(list1) + len(list2), list1, list2


def read_features_num_augment():
    """
    读取扩充后的知识图谱上的特征数
    """
    ans1 = models.augmenTestNode.objects.values('perList')
    ans1 = list(ans1)
    len1 = ''
    ans2 = models.augmenTestNode.objects.values('apiList')
    ans2 = list(ans2)
    len2 = ''
    for one in ans1:
        if one['perList'] != '':
            len1 = len1 + ',' + one['perList']
    len1 = list(set(len1.split(',')))
    list1 = len1[1:]
    print('per nums:', len(list1))
    for one in ans2:
        if one['apiList'] != '':
            len2 = len2 + ',' + one['apiList']
    len2 = list(set(len2.split(',')))
    list2 = len2[1:]
    print('api nums:', len(list2))

    return len(list1) + len(list2), list1, list2


def feature_match_ans(output):
    """处理特征匹配结果"""
    match_num = 0
    s = []
    api_record = []
    per_record = []
    num, per, api = read_features_num()
    print('dict num:', len(output))
    for key in output.keys():
        # print('key:', key)
        if key.find('permission') != -1:
            # permissions
            try:
                ans = models.PerTest.objects.get(perName=key)
                id = str(ans.perID)
                per_record.append(id)
                if id in per:
                    match_num = match_num + 1
                    s.append(key)
            except:
                print('error:', key)
        elif key.find('/') != -1:
            # apis
            try:
                ans = models.augmenTestAPi.objects.get(apiName=key)
                id = str(ans.apiID)
                api_record.append(id)
                if id in api:
                    match_num = match_num + 1
                    s.append(key)
            except:
                print('error:', key)
        else:
            print('aha:', key)
    print('match_num:', match_num)
    diff_per = list(set(per) - set(per_record))
    diff_api = list(set(api) - set(api_record))
    print('diff per:', diff_per)
    print('diff api:', diff_api)
    return match_num


def feature_match_ans_augment(output):
    """处理使用扩充后的知识图谱的特征匹配结果"""
    match_num = 0
    s = []
    api_record = []
    per_record = []
    num, per, api = read_features_num_augment()
    print('dict num:', len(output))
    for key in output.keys():
        # print('key:', key)
        if key.find('permission') != -1:
            # permissions
            try:
                ans = models.augmenTestPer.objects.get(perName=key)
                id = str(ans.perID)
                per_record.append(id)
                if id in per:
                    match_num = match_num + 1
                    s.append(key)
            except:
                print('error:', key)
        elif key.find('/') != -1:
            # apis
            try:
                ans = models.augmenTestAPi.objects.get(apiName=key)
                id = str(ans.apiID)
                api_record.append(id)
                if id in api:
                    match_num = match_num + 1
                    s.append(key)
            except:
                print('error:', key)
        else:
            print('aha:', key)
    print('match_num:', match_num)
    diff_per = list(set(per) - set(per_record))
    diff_api = list(set(api) - set(api_record))
    print('diff per:', diff_per)
    print('diff api:', diff_api)
    return match_num


def path_coverage(output):
    """
    匹配率
    由于是两两匹配的，因此对于那些没匹配上的路径，还需要人工验证
    """
    ans = models.augmenTestRel.objects.values()
    num = 0
    ans = list(ans)
    for one in ans:
        tmp = []
        tmp.append(one['sourceID'])
        tmp.append(one['targetID'])
        if tmp in output:
            num = num + 1
        else:
            print('error', tmp)
    print('covered num:', num)
    print('total num:', len(ans))
    print('coverage:', num / len(ans))


def path_coverage_augment(output):
    """
    匹配率
    由于是两两匹配的，因此对于那些没匹配上的路径，还需要人工验证
    """
    ans = models.augmenTestRel.objects.values()
    num = 0
    ans = list(ans)
    for one in ans:
        tmp = []
        tmp.append(one['sourceID'])
        tmp.append(one['targetID'])
        if tmp in output:
            num = num + 1
        else:
            print('error', tmp)
    print('covered num:', num)
    print('total num:', len(ans))
    print('coverage:', num / len(ans))


def count_behavoir(output):
    """
    统计匹配上的行为/节点总数
    """
    num = 0
    for key, value in output.items():
        num = num + value
    print('behavior count:', num)


fea_output = {"android/content/Intent;->setClass": 253, "android/app/Service;->stopSelf": 109,
              "android/telephony/TelephonyManager;->getLine1Number": 104,
              "android/media/MediaRecorder;->setOutputFormat": 15,
              "android/net/wifi/WifiManager;->getConnectionInfo": 322, "java/io/FileOutputStream;->write": 4250,
              "android.permission.WRITE_EXTERNAL_STORAGE": 96,
              "android/telephony/TelephonyManager;->getSimSerialNumber": 232, "java/lang/System;->exit": 159,
              "android.permission.ACCESS_FINE_LOCATION": 58, "android.permission.WAKE_LOCK": 70,
              "android.permission.GET_TASKS": 58, "android/telephony/SmsManager;->sendTextMessage": 262,
              "android/app/AlertDialog$Builder;->setPositiveButton": 475, "android.permission.CHANGE_WIFI_STATE": 57,
              "android.permission.INTERNET": 97, "android/telephony/SmsManager;->getDefault": 947,
              "android/os/Environment;->getExternalStorageDirectory": 928, "android/content/Intent;->getAction": 1803,
              "java/net/URL;->openConnection": 814, "android/content/BroadcastReceiver;->onReceive": 52,
              "java/io/InputStreamReader;->read": 1423, "android/telephony/PhoneStateListener;->onCallStateChanged": 1,
              "android.permission.ACCESS_NETWORK_STATE": 94, "android.permission.WRITE_CONTACTS": 9,
              "android.permission.WRITE_SMS": 47, "java/net/HttpURLConnection;->getInputStream": 1085,
              "android/view/Window;->getAttributes": 160, "android.permission.READ_CONTACTS": 31,
              "android/content/Intent$ShortcutIconResource;->fromContext": 30,
              "android/telephony/SmsMessage;->getMessageBody": 118,
              "android/net/ConnectivityManager;->getActiveNetwork": 1, "android.permission.RECEIVE_SMS": 58,
              "android/content/Context;->getContentResolver": 1492,
              "android/telephony/SmsMessage;->getOriginatingAddress": 93,
              "android/location/Location;->getLongitude": 189, "android/content/Intent;->getStringExtra": 614,
              "android.permission.SEND_SMS": 71, "android/internal/telephony/ITelephony$Stub;->endCall": 1,
              "android.permission.READ_EXTERNAL_STORAGE": 52, "java/lang/Thread;->run": 289,
              "android/content/Intent;->addFlags": 612, "android/app/admin/DevicePolicyManager;->resetPassword": 48,
              "android/view/ViewGroup;->removeView": 558, "android/telephony/TelephonyManager;->getSubscriberId": 578,
              "android/net/wifi/WifiInfo;->getMacAddress": 260, "android/content/Intent;->setAction": 498,
              "java/io/File;->getAbsoluteFile": 38, "android/media/MediaRecorder;->setOutputFile": 15,
              "android/media/AudioManager;->setVibrateSetting": 4, "android/net/wifi/WifiManager;->setWifiEnabled": 51,
              "android/content/pm/PackageManager;->getInstalledPackages": 155,
              "android/app/admin/DevicePolicyManager;->isAdminActive": 4,
              "android/content/BroadcastReceiver;->abortBroadcast": 118, "java/io/File;->createNewFile": 651,
              "android.permission.CHANGE_NETWORK_STATE": 47, "android/content/Intent;->setData": 465,
              "android/view/View;->setOnClickListener": 1185, "android/content/ContentResolver;->delete": 2382,
              "android.permission.READ_PHONE_STATE": 75, "java/lang/Object;->toString": 51906,
              "android.permission.CLEAR_APP_CACHE": 4, "android/content/Context;->getPackageManager": 2380,
              "android/content/Context;->getSystemService": 4841, "android/content/IntentFilter;->addAction": 570,
              "android/net/ConnectivityManager;->getActiveNetworkInfo": 808, "android/view/ViewGroup;->addView": 1236,
              "android/media/AudioManager;->setRingerMode": 10, "android/widget/EditText;->getText": 1053,
              "android/telephony/TelephonyManager;->getDeviceId": 738,
              "com/android/internal/telephony/ITelephony$Stub;->endCall": 15,
              "android.permission.SYSTEM_ALERT_WINDOW": 78, "android.permission.READ_SMS": 51,
              "android/telephony/TelephonyManager;->getNetworkOperator": 106,
              "android/content/ContentResolver;->registerContentObserver": 230, "java/lang/String;->equals": 12159,
              "android/net/Uri;->parse": 2041, "android/content/Intent;->setFlags": 447,
              "android/location/Location;->getLatitude": 189, "android/app/ActivityManager;->getRunningServices": 65,
              "java/util/zip/ZipOutputStream;->putNextEntry": 30, "android/app/ActivityManager;->getRunningTasks": 73,
              "android.permission.READ_CALL_LOG": 31, "android/content/Context;->registerReceiver": 644,
              "android.permission.RECEIVE_BOOT_COMPLETED": 72, "android/content/ContentResolver;->query": 1429,
              "android.permission.PROCESS_OUTGOING_CALLS": 14, "android/app/admin/DevicePolicyManager;->lockNow": 36,
              "android/content/Intent;->setDataAndType": 170, "java/io/File;->getName": 5735,
              "android.permission.CALL_PHONE": 26, "android/content/pm/PackageManager;->setComponentEnabledSetting": 19,
              "android/content/Context;->getResources": 2828, "android/media/MediaRecorder;->setAudioSource": 12,
              "android/media/MediaRecorder;->setAudioEncoder": 12, "java/lang/Math;->random": 282,
              "java/io/InputStream;->read": 3070, "android.permission.ACCESS_COARSE_LOCATION": 57,
              "com.android.launcher.permission.INSTALL_SHORTCUT": 43}
# feature_match_ans_augment(fea_output)
# feature_match_ans(fea_output)

path_output = [[32, 8, 24, 23], [42, 37], [56, 29, 35, 56, 55], [35, 2], [29, 35], [12, 57, 1], [13, 57], [14, 57],
               [22, 57], [19, 57], [56, 55], [56, 2], [56, 29], [1, 3, 8], [1, 32], [33, 41, 49], [33, 4], [47, 57],
               [57, 1], [32, 8], [32, 35], [18, 57], [11, 35], [52, 58], [16, 57], [41, 49], [24, 23], [32, 35, 2, 55],
               [3, 8], [32, 8, 24, 39], [42, 37], [56, 29, 35, 56, 55], [17, 35, 2], [29, 35], [12, 57, 1], [13, 57],
               [14, 57], [22, 57], [19, 57], [56, 55], [56, 2, 55], [56, 29], [1, 3, 8], [1, 32], [47, 57], [57, 1],
               [32, 8], [1, 32, 35], [18, 57], [17, 35], [17, 57], [11, 35], [16, 57], [3, 8], [24, 39], [2, 55],
               [12, 57], [13, 57], [22, 57], [47, 57], [16, 57], [1, 3], [5, 37], [42, 37], [32, 35, 56, 55],
               [11, 35, 2], [12, 57, 1], [13, 57], [14, 57], [22, 57], [19, 57], [56, 55], [56, 2, 55], [1, 3, 8],
               [1, 32], [47, 57], [57, 1], [1, 32, 8], [32, 35], [18, 57], [11, 35], [16, 57], [3, 8], [2, 55],
               [32, 35, 56, 55], [12, 57], [13, 57, 1], [22, 57], [56, 55], [1, 3], [1, 32], [57, 1], [32, 35],
               [18, 57], [17, 35], [17, 57], [11, 35], [16, 57], [24, 39], [12, 57], [13, 57], [11, 35], [16, 57],
               [32, 8, 24, 39], [42, 37], [56, 29, 35, 56, 55], [17, 35, 2], [29, 35], [12, 57, 1], [13, 57], [14, 57],
               [22, 57], [19, 57], [56, 55], [56, 2, 55], [56, 29], [1, 3, 8], [1, 32], [47, 57], [57, 1], [32, 8],
               [1, 32, 35], [18, 57], [17, 35], [17, 57], [11, 35], [16, 57], [3, 8], [24, 39], [2, 55], [42, 37],
               [17, 35, 56], [12, 57], [19, 57], [56, 55], [33, 41, 49, 48], [52, 58, 48], [47, 57], [18, 57], [17, 35],
               [17, 57], [11, 35], [16, 57], [52, 58], [41, 49], [3, 8], [49, 48], [42, 37], [54, 43], [52, 58, 6, 57],
               [12, 57], [14, 57], [22, 57], [19, 57], [33, 41], [33, 4], [58, 6], [58, 48], [18, 57], [17, 57],
               [52, 58], [3, 8], [32, 8, 24], [42, 37], [12, 57, 1], [13, 57], [14, 57], [22, 57], [1, 3, 8], [1, 32],
               [57, 1], [32, 8], [16, 57], [3, 8], [32, 8, 24, 39], [42, 37], [56, 29, 35, 56, 55], [17, 35, 2],
               [29, 35], [12, 57, 1], [13, 57], [14, 57], [22, 57], [19, 57], [56, 55], [56, 2, 55], [56, 29],
               [1, 3, 8], [1, 32], [47, 57], [57, 1], [32, 8], [1, 32, 35], [18, 57], [17, 35], [17, 57], [11, 35],
               [16, 57], [3, 8], [24, 39], [2, 55], [32, 8, 24, 39], [42, 37], [56, 29, 35, 56, 55], [17, 35, 2],
               [29, 35], [12, 57, 1], [13, 57], [14, 57], [22, 57], [19, 57], [56, 55], [56, 2, 55], [56, 29],
               [1, 3, 8], [1, 32], [47, 57], [57, 1], [32, 8], [1, 32, 35], [18, 57], [17, 35], [17, 57], [11, 35],
               [16, 57], [3, 8], [24, 39], [2, 55], [56, 29, 35, 56, 55], [11, 35, 2], [29, 35], [12, 57, 1], [13, 57],
               [14, 57], [22, 57], [56, 55], [56, 2, 55], [56, 29], [1, 32], [47, 57], [57, 1], [32, 8], [1, 32, 35],
               [11, 35], [2, 55], [56, 2], [26, 7, 26, 7], [33, 4], [26, 7], [26, 40], [26, 7, 26, 7], [26, 7],
               [26, 40], [38, 26], [38, 40], [5, 37], [32, 8, 24, 23], [42, 37], [12, 57], [13, 57], [14, 57], [22, 57],
               [19, 57], [47, 57], [32, 8], [16, 57], [24, 23], [3, 8], [42, 37], [11, 35, 56, 2], [32, 35, 2, 55],
               [12, 57], [13, 57, 1], [14, 57], [22, 57], [19, 57], [56, 55], [56, 2], [1, 3, 8], [1, 32], [33, 41],
               [47, 57], [57, 1], [1, 32, 8], [32, 35], [18, 57], [11, 35], [3, 8], [2, 55], [32, 8, 24, 39], [42, 37],
               [56, 29, 35, 56, 55], [17, 35, 2], [29, 35], [12, 57, 1], [13, 57], [14, 57], [22, 57], [19, 57],
               [56, 55], [56, 2, 55], [56, 29], [1, 3, 8], [1, 32], [47, 57], [57, 1], [32, 8], [1, 32, 35], [18, 57],
               [17, 35], [17, 57], [11, 35], [16, 57], [3, 8], [24, 39], [2, 55], [32, 8, 24, 39], [42, 37],
               [56, 29, 35, 56, 55], [17, 35, 2], [29, 35], [12, 57, 1], [13, 57], [14, 57], [22, 57], [19, 57],
               [56, 55], [56, 2, 55], [56, 29], [1, 3, 8], [1, 32], [47, 57], [57, 1], [32, 8], [1, 32, 35], [18, 57],
               [17, 35], [17, 57], [11, 35], [16, 57], [3, 8], [24, 39], [2, 55], [32, 8, 24], [42, 37],
               [56, 29, 35, 56, 55], [35, 2], [29, 35], [12, 57, 1], [13, 57], [14, 57], [22, 57], [19, 57], [56, 55],
               [56, 2], [56, 29], [1, 3, 8], [1, 32, 35], [47, 57], [57, 1], [32, 8], [32, 35], [11, 35, 2, 55],
               [16, 57], [3, 8], [2, 55], [26, 7, 26, 7], [26, 7], [26, 40], [38, 26], [38, 40], [12, 57], [13, 57],
               [14, 57], [16, 57], [24, 39], [26, 7, 26, 7], [26, 7], [26, 40], [38, 26], [38, 40], [12, 57], [13, 57],
               [22, 57], [52, 58, 48], [47, 57], [18, 57], [16, 57], [52, 58], [24, 39], [26, 7, 26, 7], [26, 7],
               [26, 40], [38, 26], [38, 40], [26, 7, 26, 7], [26, 7], [26, 40], [38, 26], [38, 40], [32, 35, 56, 2],
               [17, 35, 2], [30, 49, 6, 57], [13, 57], [22, 57], [56, 2], [32, 35], [17, 35], [17, 57], [11, 35],
               [16, 57], [24, 23], [49, 6], [30, 49], [26, 7, 26, 7], [38, 26, 40], [38, 40], [26, 7], [26, 40],
               [57, 1, 3], [57, 1], [35, 56, 2], [35, 2], [12, 57], [13, 57], [14, 57], [22, 57], [56, 2], [16, 57],
               [1, 3], [56, 29, 35, 56, 55], [32, 35, 2], [29, 35], [12, 57, 1], [22, 57], [19, 57], [56, 55], [56, 2],
               [56, 29], [1, 3], [1, 32], [47, 57], [57, 1], [32, 35], [18, 57], [17, 35], [17, 57], [11, 35],
               [56, 2, 55], [52, 58, 6, 57], [12, 57], [13, 57], [22, 57], [19, 57], [33, 4], [58, 6], [58, 48],
               [17, 57], [52, 58], [16, 57], [24, 39], [5, 37], [12, 57], [13, 57, 1], [56, 55], [47, 57], [57, 1],
               [18, 57], [12, 57], [22, 57], [19, 57], [17, 57], [32, 8, 24, 39], [42, 37], [56, 29, 35, 56, 55],
               [35, 2], [29, 35], [12, 57, 1], [13, 57], [14, 57], [22, 57], [19, 57], [56, 55], [56, 2], [56, 29],
               [1, 3, 8], [1, 32], [33, 41], [47, 57], [57, 1], [32, 8], [1, 32, 35, 2, 55], [11, 35], [16, 57],
               [24, 39], [3, 8], [2, 55], [42, 37], [35, 56, 55], [56, 29, 35], [6, 57], [12, 57], [22, 57], [19, 57],
               [56, 55], [56, 29], [58, 6, 57], [47, 57], [18, 57], [17, 35], [17, 57], [11, 35], [5, 37], [42, 37],
               [56, 29, 35, 56, 55], [35, 2], [29, 35], [12, 57, 1], [13, 57], [14, 57], [22, 57], [56, 55],
               [56, 2, 55], [56, 29], [1, 3], [1, 32, 8], [33, 41, 49], [47, 57], [57, 1], [32, 8], [32, 35],
               [11, 35, 2], [2, 55], [41, 49], [1, 3, 8], [8, 24, 23], [42, 37], [54, 43], [12, 57], [56, 29], [6, 57],
               [17, 57], [24, 23], [26, 7, 26, 7], [26, 7], [26, 40], [38, 26], [38, 40], [1, 3], [32, 8, 24, 39],
               [42, 37], [56, 29, 35, 56, 55], [17, 35, 2], [29, 35], [12, 57, 1], [13, 57], [14, 57], [22, 57],
               [19, 57], [56, 55], [56, 2, 55], [56, 29], [1, 3, 8], [1, 32], [47, 57], [57, 1], [32, 8], [1, 32, 35],
               [18, 57], [17, 35], [17, 57], [11, 35], [16, 57], [3, 8], [24, 39], [2, 55], [32, 35, 56, 2],
               [17, 35, 2], [30, 49, 6, 57], [13, 57], [22, 57], [56, 2], [32, 35], [17, 35], [17, 57], [11, 35],
               [16, 57], [24, 23], [49, 6], [30, 49], [32, 35, 56, 55], [35, 2], [12, 57, 1], [13, 57], [22, 57],
               [19, 57], [56, 55], [56, 2, 55], [1, 3], [1, 32], [47, 57], [57, 1], [32, 35], [11, 35], [16, 57],
               [24, 39], [2, 55], [16, 57], [56, 2], [26, 7, 26, 7], [33, 4], [26, 7], [26, 40], [17, 5, 37], [8, 24],
               [42, 37], [35, 56], [56, 29, 35, 2, 55], [29, 35], [12, 57], [13, 57, 1], [14, 57], [22, 57], [19, 57],
               [32, 35, 56, 55], [56, 2], [56, 29], [1, 3], [1, 32, 8], [33, 41], [52, 58, 48], [47, 57], [57, 1],
               [32, 8], [32, 35], [17, 5], [17, 35], [17, 57], [11, 35], [52, 58], [2, 55], [16, 57], [1, 3, 8],
               [41, 49], [41, 49, 48], [26, 7, 26, 7], [26, 7], [26, 40], [38, 26], [38, 40], [32, 35, 56, 2],
               [17, 35, 2], [30, 49, 6, 57], [13, 57], [22, 57], [56, 2], [32, 35], [17, 35], [17, 57], [11, 35],
               [16, 57], [24, 23], [49, 6], [30, 49], [1, 3], [32, 8, 24], [42, 37], [56, 29, 35, 56, 55], [35, 2],
               [29, 35], [12, 57, 1], [13, 57], [14, 57], [19, 57], [56, 55], [56, 2, 55], [56, 29], [1, 3],
               [1, 32, 35], [47, 57], [57, 1], [32, 8], [32, 35], [11, 35, 2], [16, 57], [1, 3, 8], [2, 55],
               [26, 7, 26, 7], [26, 7], [26, 40], [38, 26], [38, 40], [32, 8, 24, 39], [42, 37], [56, 29, 35, 56, 55],
               [11, 35, 2], [29, 35], [12, 57, 1], [13, 57], [14, 57], [22, 57], [56, 55], [56, 2, 55], [56, 29],
               [1, 3, 8], [1, 32, 35], [47, 57], [57, 1], [32, 8], [32, 35], [18, 57], [17, 35], [17, 57], [11, 35],
               [16, 57], [3, 8], [2, 55], [24, 39], [5, 37], [32, 8, 24], [42, 37], [54, 43], [56, 29, 35, 56, 55],
               [35, 2], [29, 35], [12, 57, 1], [13, 57], [14, 57], [22, 57], [19, 57], [56, 55], [56, 2], [56, 29],
               [1, 3, 8], [1, 32], [47, 57], [57, 1], [32, 8], [1, 32, 35, 2, 55], [11, 35], [16, 57], [3, 8], [2, 55],
               [26, 7, 26, 7], [26, 7], [26, 40], [38, 26], [38, 40], [26, 7, 26, 7], [26, 7], [26, 40], [38, 26],
               [38, 40], [26, 7, 26, 7], [38, 26, 40], [38, 40], [26, 7], [26, 40], [32, 8, 24, 39], [42, 37],
               [56, 29, 35, 56, 55], [17, 35, 2], [29, 35], [12, 57, 1], [13, 57], [14, 57], [22, 57], [19, 57],
               [56, 55], [56, 2, 55], [56, 29], [1, 3, 8], [1, 32], [47, 57], [57, 1], [32, 8], [1, 32, 35], [18, 57],
               [17, 35], [17, 57], [11, 35], [16, 57], [3, 8], [24, 39], [2, 55], [17, 5, 37], [12, 57], [13, 57],
               [47, 57], [6, 57], [17, 5], [17, 57], [17, 35, 56, 2], [35, 2], [30, 49, 6, 57], [13, 57], [22, 57],
               [56, 2], [17, 35], [17, 57], [49, 6], [16, 57], [24, 23], [30, 49], [32, 8, 24], [42, 37], [12, 57, 1],
               [13, 57], [14, 57], [22, 57], [1, 3, 8], [1, 32], [57, 1], [32, 8], [16, 57], [3, 8], [42, 37],
               [35, 56, 2], [56, 29, 35, 2, 55], [29, 35], [12, 57], [13, 57, 1], [14, 57], [22, 57], [19, 57],
               [56, 55], [56, 2], [56, 29], [1, 3, 8], [47, 57], [57, 1], [11, 35], [3, 8], [2, 55], [56, 2], [33, 4],
               [42, 37], [17, 35, 56, 2], [56, 29, 35, 2, 55], [29, 35], [12, 57], [13, 57, 1], [14, 57], [22, 57],
               [19, 57], [56, 55], [56, 2], [56, 29], [1, 3, 8], [1, 32], [47, 57], [57, 1], [32, 8], [1, 32, 35],
               [18, 57], [17, 35], [17, 57], [16, 57], [11, 35], [2, 55], [3, 8], [56, 29, 35, 56, 55], [29, 35],
               [56, 55], [56, 29], [17, 35], [26, 7, 26, 7], [38, 26, 40], [38, 40], [26, 7], [26, 40], [42, 37],
               [17, 35, 56, 2], [56, 29, 35, 2, 55], [29, 35], [12, 57], [13, 57, 1], [14, 57], [56, 55], [56, 2],
               [56, 29], [1, 3, 8], [47, 57], [57, 1], [18, 57], [17, 35], [17, 57], [11, 35], [2, 55], [3, 8],
               [3, 8, 24, 39], [42, 37], [12, 57], [13, 57], [22, 57], [19, 57], [47, 57], [24, 39], [3, 8], [16, 57],
               [3, 8, 24], [42, 37], [56, 29, 35, 56, 55], [35, 2], [29, 35], [12, 57, 1], [13, 57], [14, 57], [22, 57],
               [19, 57], [56, 55], [56, 2], [56, 29], [1, 3], [47, 57], [57, 1], [18, 57], [17, 35], [17, 57], [16, 57],
               [11, 35, 2, 55], [2, 55], [3, 8], [32, 8, 24], [42, 37], [12, 57], [13, 57], [32, 8], [3, 8], [16, 57],
               [42, 37], [11, 35, 56], [56, 29, 35], [12, 57], [13, 57, 1], [14, 57], [22, 57], [19, 57], [56, 55],
               [56, 29], [1, 3], [47, 57], [57, 1], [11, 35], [1, 3, 8], [42, 37], [12, 57], [13, 57, 1], [14, 57],
               [1, 3, 8], [57, 1], [3, 8], [42, 37], [35, 56], [12, 57, 1], [13, 57], [14, 57], [19, 57], [56, 55],
               [1, 3], [1, 32, 8], [47, 57], [57, 1], [32, 8], [32, 35], [16, 57], [1, 3, 8], [12, 57], [13, 57],
               [14, 57], [22, 57], [19, 57], [33, 41], [33, 4], [58, 48], [47, 57], [17, 57], [41, 49, 48], [16, 57],
               [52, 58, 48], [41, 49], [32, 35, 56], [35, 56], [12, 57], [22, 57], [47, 57], [16, 57], [56, 55],
               [56, 2, 55], [56, 29], [2, 55], [26, 7, 26, 7], [26, 7], [26, 40], [38, 26], [38, 40], [32, 8, 24, 39],
               [42, 37], [56, 29, 35, 56, 55], [17, 35, 2], [29, 35], [12, 57, 1], [13, 57], [14, 57], [22, 57],
               [19, 57], [56, 55], [56, 2, 55], [56, 29], [1, 3, 8], [1, 32], [47, 57], [57, 1], [32, 8], [1, 32, 35],
               [18, 57], [17, 35], [17, 57], [11, 35], [16, 57], [3, 8], [24, 39], [2, 55]]

# path_coverage_augment(path_output)
# path_coverage(path_output)

behav = {"1": 16, "2": 9, "3": 82, "4": 66, "5": 25, "6": 10, "7": 61, "8": 38, "9": 9, "10": 27, "11": 91, "12": 44,
         "13": 18, "14": 10, "15": 17, "16": 40, "17": 16, "18": 9, "19": 30, "20": 73, "21": 90, "22": 22, "23": 47,
         "24": 67, "25": 55, "26": 1, "27": 10, "28": 41, "29": 6, "30": 57, "31": 97, "32": 29, "33": 7, "34": 6,
         "35": 15, "36": 93, "37": 43, "38": 1, "39": 11, "40": 1, "41": 57, "42": 44, "43": 52, "44": 13, "45": 18,
         "46": 91, "47": 16, "48": 3, "49": 0, "50": 29, "51": 92, "52": 95, "53": 32, "54": 6, "55": 8, "56": 16,
         "57": 95, "58": 4, "59": 87, "60": 87, "61": 87, "62": 72, "63": 72, "64": 77, "65": 56, "66": 45, "67": 92,
         "68": 92, "69": 69, "70": 87, "71": 44, "72": 23, "73": 86, "74": 95, "75": 74, "76": 87, "77": 92, "78": 60,
         "79": 74, "80": 95, "81": 70, "82": 38, "83": 73, "84": 61, "85": 75, "86": 95, "87": 69, "88": 96, "89": 90,
         "90": 36, "91": 77}


# count_behavoir(behav)

def count_data_type():
    """
    对于由genome drebin amd和google play组成的混合型数据集，分别统计每一种数据集的大小
    它们分别以以下字符开头：
    genome drebin amd gp
    """
    input_folder = '/media/wuyang/WD_BLACK/AndroidMalware/malware_test'
    names = os.listdir(input_folder)  # 这将返回一个所有文件名的列表
    a = b = c = d = 0
    for name in names:
        if name.find('genome') != -1:
            a = a + 1
            # Your process code
        elif name.find('drebin') != -1:
            b = b + 1
        elif name.find('amd') != -1:
            c = c + 1
        else:
            d = d + 1
    ret = {}
    ret['genome'] = a
    ret['drebin'] = b
    ret['amd'] = c
    ret['gp'] = d
    print(ret)

# count_data_type()


def make_new_dataset():
    """
    由于原有的数据集过大，因此限制每种类型的样本数量为1200
    """
    input_folder = '/media/wuyang/WD_BLACK/AndroidMalware/malware'
    output_folder = '/media/wuyang/WD_BLACK/AndroidMalware/malware_test'  # 运行程序前先手动清空该文件夹

    names = os.listdir(input_folder)  # 这将返回一个所有文件名的列表
    a = b = c = d = 0
    for name in names:
        print('name:', name)
        if name.find('genome') != -1 and a <= 1200:
            a = a + 1
            # file = os.path.split(name)[1]
            file = glob.glob(input_folder + '/' + name)
            shutil.copy(file[0], output_folder)
        elif name.find('drebin') != -1 and b <= 1200:
            b = b + 1
            file = glob.glob(input_folder + '/' + name)
            shutil.copy(file[0], output_folder)
        elif name.find('amd') != -1 and c <= 1200:
            c = c + 1
            file = glob.glob(input_folder + '/' + name)
            shutil.copy(file[0], output_folder)
        elif name.find('gp') != -1 and d <= 1200:
            d = d + 1
            file = glob.glob(input_folder + '/' + name)
            shutil.copy(file[0], output_folder)
        else:
            pass
            print('make new dataset: error')

        # 以下代码用于补充数量不足的样本
        # if name.find('gp_ICSE22')!=-1:
        #     if os.path.exists(output_folder+'/'+name):
        #         pass
        #     else:
        #         if a<1:
        #             print('name:', name)
        #             a=a+1
        #             file = glob.glob(input_folder + '/' + name)
        #             shutil.copy(file[0], output_folder)

# make_new_dataset()
