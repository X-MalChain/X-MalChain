import string
import glob
import os
import json
import codecs  # 将ansi编码的文件转为utf-8编码的文件

from django.shortcuts import render
from django.http import HttpResponse

import csv
from common.models import augmenTestAPi, PerTest, KgTest, relTest

# Create your views here.
testApk_path = 'D:\\testAPK.txt'
# apiFeature_path = ''
perFeature_path = 'verify/input/perFeature.txt'  # 单独存放kg的permission特征
apiFeature_path = 'verify/input/apiFeature.txt'  # 单独存放kg的api特征
kgFeatures_path = 'verify/input/kgFeatures.txt'  # 存放kg的所有特征

report_path = "D:\\reportKG_1_v1.txt"
# report_path = "D:\\reportKG_vs1.txt"    # 之前的实验
input_path = "E:\\PyCharm\\featureGen\\eval_apk\\apk_output1"  # 输入文件，所有apk的特征文件
# input_path="E:\\PyCharm\\featureGen\\eval_apk\\apk_output_vs1"  # 之前的实验

flag = 0
fileID = 0

# 在写入映射报告前，先清空txt文件，防止报告重复
with open(report_path, "a", encoding='utf-8') as report:
    report.truncate(0)


# # 在写入映射失败的特征前，先清空txt文件，防止记录重复
# with open("verify/output/nmapFetures.txt", "a", encoding='utf-8') as nmapFeatureFile:
#     nmapFeatureFile.truncate(0)

def mainTask(request):
    # ********** 数据准备 *************
    # 分别读取api和per的txt文件，将apis和permissions分别放到list中
    perList = []
    apiList = []
    kgFeaturesList = []
    perFeatureFile = open(perFeature_path, 'r', encoding='utf-8', newline="")
    apiFeatureFile = open(apiFeature_path, 'r', encoding='utf-8', newline="")
    kgFeaturesFile = open(kgFeatures_path, 'r', encoding='utf-8', newline="")
    for row in perFeatureFile.readlines():
        perList.append(row.strip())
    for row in apiFeatureFile.readlines():
        apiList.append(row.strip())
    for row in kgFeaturesFile.readlines():
        kgFeaturesList.append(row.strip())
    perFeatureFile.close()
    apiFeatureFile.close()
    kgFeaturesFile.close()

    kgModel = KgTest.objects.values()
    kgList = list(kgModel)  # 图谱上的节点数

    # 在写入映射失败的特征前，先清空txt文件，防止记录重复
    with open("verify/output/nmapFetures.txt", "a", encoding='utf-8') as nmapFeatureFile:
        nmapFeatureFile.truncate(0)

    # ********** 依次匹配每一个文件 *************
    with open(report_path, "a", encoding='utf-8') as report:
        # 读取APK的特征文件
        global fileID
        global flag
        files = glob.glob(input_path + '/*.txt')
        fileID = 0

        fullMapNodeStatistic = []  # 对于所有的APK文件，统计KG上每个节点的映射情况，对应的是完全匹配的情况
        partMapNodeStatistic = []  # 对于所有的APK文件，统计KG上每个节点的映射情况，对应的是部分匹配的情况

        for f in files:  # f形如D:/input\3F540538550DD3AF7D1CAE776C08D815.apk_api.txt
            fileID = fileID + 1
            flag = 0
            filePathAndName = os.path.split(f)  # 返回值为元组：（path, file name）
            fileName = filePathAndName[1]
            report.write("****************** APK " + str(fileID) + " ******************\n")  # 记录当前APK的名字
            report.write("文件名：" + fileName + '\n')  # 记录当前APK的名字

            # 在写入映射成功的特征前，先清空映射成功的txt文件，防止记录重复
            with open("verify/output/mapFeatures.txt", "a", encoding='utf-8') as mapFeatureFile:
                mapFeatureFile.truncate(0)

            # 首先读取某个APK的特征文件
            apkFile = open(f, 'r', encoding='utf-8', newline="")
            apkFeatures = []  # 存放该APK的特征
            # global flag
            for row in apkFile.readlines():
                # print("line:"+line)
                line = row.strip()
                if line == "perStart":
                    # 操作
                    flag = 1
                    continue
                elif line == 'perEnd':
                    flag = 0
                    continue
                elif line == 'apiStart':
                    # 操作
                    flag = 1
                    continue
                elif line == 'apiEnd':
                    flag = 0
                    break
                else:
                    pass
                if flag == 1:
                    # if line.find("permission") or line.find(";"):     # 修改符号;->或者;.
                    apkFeatures.append(line)  # 删除开头的“L”

            # *******1. 计算某个APK的特征覆盖率，这里的映射关系是：KG->某个APK特征文件，查看KG特征的完整性*******
            mapCount = 0
            nmapCount = 0

            # 测试所有特征的覆盖率
            for feature in apkFeatures:  # 对于apk的feature，都去数据表中查看是否有对应的
                tmp = feature.strip()
                judge = tmp.find("(")
                if judge != -1:
                    tmp = tmp[:judge]
                if tmp.find("."):
                    tmp1 = tmp.split(".")
                    tmp = ".".join(tmp1)
                elif tmp.find(";"):
                    tmp1 = tmp.split(";")
                    tmp = ";".join(tmp1)
                if tmp in str(kgFeaturesList):
                    mapCount = mapCount + 1
                    # print('映射成功的为：', feature)
                    # 将映射成功的写入本地文件mapFeatures.txt中，以为节点匹配做准备
                    with open("verify/output/mapFeatures.txt", "a", encoding='utf-8') as outfile:  # 这种方法会自动关闭文件
                        outfile.write(feature + '\n')
                else:
                    nmapCount = nmapCount + 1
                    # print('映射失败的为：', feature)
                    # 将映射失败的写入本地文件nmapFeatures.txt中
                    with open("verify/output/nmapFetures.txt", "a", encoding='utf-8') as outfile:  # 这种方法会自动关闭文件
                        outfile.write(feature + '\n')
            if mapCount > 0:
                mapRate = mapCount / (mapCount + nmapCount)
                ret1 = '特征映射成功率(映射上的特征数/总的特征数)：' + str(round(mapRate, 4) * 100) + '%'  # 以70.34%的形式输出
                # ret1 = '特征映射成功率：' + str('%.2f' % mapRate) + '%'  # 以70.34%的形式输出
                # with open(report_path, "a", encoding='utf-8') as outfile:  # 这种方法会自动关闭文件
                #     outfile.write(ret1 + '\n')
                report.write(ret1 + '\n')
            else:
                pass

            # *******2. 计算某个APK覆盖的节点 *******
            # 打开映射成功的txt文件，去数据表中找匹配的api
            mapFeatures = open("verify/output/mapFeatures.txt", 'r', encoding='utf-8', newline="")
            apiIdList = []  # 记录下匹配成功的api的id
            perIdList = []  # 记录下匹配成功的per的id

            # 记录下匹配到的api的id
            for row in mapFeatures.readlines():
                line = row.strip()
                # 将字符串拆分后然后再再重组，不然可能出现匹配不上的问题
                if line.find(";") != -1:  # 说明处理的是api
                    tmp1 = line.split(';')
                    tmp = ';'.join(tmp1)
                    ans = augmenTestAPi.objects.filter(apiName__icontains=tmp)
                    if ans:
                        ans = list(ans)
                        for one in ans:
                            # apiList.append({'id':one.id,'name':one.apiName})
                            apiIdList.append(one.id)
                    else:
                        pass
                else:
                    continue

            # 读取一次后，需要先暂时关闭然后重新读取，不然下面的遍历代码不会生效
            mapFeatures.close()
            mapFeatures = open("verify/output/mapFeatures.txt", 'r', encoding='utf-8', newline="")

            # 记录下匹配到的permission的id
            for row in mapFeatures.readlines():
                line = row.strip()
                if line.find(".") != -1:
                    tmp1 = line.split('.')
                    tmp = '.'.join(tmp1)
                    ans = PerTest.objects.filter(perName__icontains=tmp)
                    if ans:
                        ans = list(ans)
                        for one in ans:
                            # perList.append({'id':one.id, 'name':one.perName})
                            perIdList.append(one.id)
                    else:
                        pass
                else:
                    continue

            partNode = []  # 匹配上了部分特征的节点，存储着这些节点的id
            fullNode = []  # 完全匹配上的节点，存储着这些节点的id
            # kgModel = KgTest.objects.values()
            # kgList = list(kgModel)

            # **************根据api来匹配节点**********************
            for apiId in apiIdList:
                # count=0 # 统计匹配上的api特征数量
                for one in kgList:
                    apiStr = one['apiList']
                    if apiStr == '':
                        continue
                    else:
                        if apiStr.find("'"):
                            apiStr = apiStr.replace("'", '')
                        if apiStr.find(','):
                            apiStr2List = apiStr.split(',')  # 数组中每个元素的数据类型是str
                        else:
                            apiStr2List = apiStr
                        apiStr2List = list(map(int, apiStr2List))  # 将值为数字的字符串数组转变为数值数组
                    if apiId in apiStr2List:
                        partNode.append(one['nodeID'])

            # 根据per来匹配节点
            # **************查看能匹配上的节点**********************
            for perId in apiIdList:
                # count=0 # 统计匹配上的api特征数量
                for one in kgList:
                    perStr = one['perList']
                    if perStr == '':
                        continue
                    else:
                        if perStr.find("'"):
                            perStr = perStr.replace("'", '')
                        if perStr.find(','):
                            perStr2List = perStr.split(',')  # 数组中每个元素的数据类型是str
                        else:
                            perStr2List = perStr
                        perStr2List = list(map(int, perStr2List))  # 将值为数字的字符串数组转变为数值数组
                    if perId in perStr2List:
                        partNode.append(one['nodeID'])
            # 去重和排序
            partNode = list(set(partNode))
            partNode = sorted(partNode)
            # print("partNode:", partNode)
            for node in partNode:
                partMapNodeStatistic.append(node)

            # **************查看完整匹配的节点**********************
            for nodeId in partNode:  # 这里面存放的是部分特征映射的节点的ID
                ans = KgTest.objects.get(nodeID=nodeId)
                ans = object_to_json(ans)
                kgPerList = str2list(ans['perList'])
                kgApiList = str2list(ans['apiList'])
                perMapCount = 0
                apiMapCount = 0

                # 遍历一个节点的perList，查看先前特征匹配上的permission是否有与之对应的
                for one in kgPerList:
                    if one in perIdList:
                        perMapCount = perMapCount + 1
                for one in kgApiList:
                    if one in apiIdList:
                        apiMapCount = apiMapCount + 1
                rate = (perMapCount + apiMapCount) / (len(kgPerList) + len(kgApiList))
                if rate == 1:  # 这些是完全特征匹配的
                    fullNode.append(ans['nodeID'])

            # 去重和排序
            fullNode = list(set(fullNode))
            fullNode = sorted(fullNode)
            # print("fullnode:", fullNode)
            for node in fullNode:
                fullMapNodeStatistic.append(node)

            allMapNum = len(kgList)
            # 计算部分特征匹配的节点覆盖率
            partMapNum = len(partNode)
            partMapRate = partMapNum / allMapNum
            ret2 = '部分特征映射的节点覆盖率(部分映射节点数/KG节点总数)：' + str(
                round(partMapRate, 4) * 100) + '%'  # 以70.34%的形式输出
            # 计算完全特征匹配的节点覆盖率
            fullMapNum = len(fullNode)
            if partMapNum > 0:
                fullMapRate = fullMapNum / allMapNum
                fullMapRatePlus = fullMapNum / partMapNum
            else:
                fullMapRate = 0
                fullMapRatePlus = 0
            ret3 = '完全特征映射的节点覆盖率(完全映射节点数/KG节点总数)：' + str(
                round(fullMapRate, 4) * 100) + '%'  # 以70.34%的形式输出
            ret4 = '完全特征映射的节点覆盖率(完全映射节点数/映射节点数)：' + str(round(fullMapRatePlus, 4) * 100) + '%'
            report.write(ret2 + '\n')
            report.write(ret3 + '\n')
            report.write(ret4 + '\n')
            report.write("完全匹配上的节点:" + ','.join(str(i) for i in fullNode) + '\n')

            # ************3.路径匹配 ***********
            """
            算法步骤（以部分匹配为例）：
                首先记录APK的特征文件中哪些可以连通的路径，并记录那些单独存在的节点。有一个保存路径的列表。
                遍历访问该APK的部分特征匹配节点列表：
                1）访问数据库，查看该列表是否有图谱中的邻节点
                2）如果有邻节点，判断该节点是否也存在于APK的匹配节点列表中
                    2.1)如果存在，则将该邻节点加入到路径列表中
                    2.2)如果没有（图谱有但是APK没有）则跳过
                3）如果没有邻节点，则该节点是单独节点，记录下该节点
            """
            # 遍历访问该APK的部分特征匹配节点列表
            fullNodeIdList = fullNode[:]  # 复制列表，其中存储的是ID
            for one in fullNodeIdList:
                one = int(one)
            pathList = []  # 保存路径序列，即匹配上的路径
            isolatedNode = []  # 单独节点
            test = []
            tmp = []  # 暂时存放一条路径
            for nodeId in fullNodeIdList:
                # 1）访问数据库，查看该列表是否有图谱中的该节点的邻节点
                ans = relTest.objects.filter(sourceID=nodeId)
                if ans:
                    if len(tmp) == 0 or tmp[-1] != nodeId:
                        tmp.append(nodeId)  # 加入源节点
                    ans = list(ans)
                    for one in ans:
                        # 2）如果有邻节点，判断邻节点是否也存在于APK的匹配节点列表中
                        if one.targetID in fullNodeIdList:
                            # 2.1)如果存在，则将该邻节点加入到路径列表中
                            # print("匹配上的路径节点为：",str(nodeId)+"->"+str(one.targetID))
                            tmp.append(one.targetID)
                        else:
                            # 2.2)如果没有则跳过（因为一般来说不存在这种情况）
                            # print("有图谱上的邻节点但是邻节点不存在APK的匹配节点列表中")
                            # tmp=[]
                            if tmp:
                                tmp.pop()
                            test.append(nodeId)
                else:
                    # 3）如果没有邻节点，则该节点是单独节点，记录下该节点
                    # print("该节点为单独节点：",nodeId)
                    isolatedNode.append(nodeId)
                    if len(tmp) > 1:
                        pathList.append(tmp)
                    tmp = []
            isolatedNode = list(set(isolatedNode))
            # 下面的print为调试信息
            # print("fullNodeIdList:", fullNodeIdList)
            # print("pathList:", pathList)
            # print("isolatedNode:", isolatedNode)
            # print("test:",list(set(test)))
            report.write("基于完全匹配节点的匹配路径:" + ';'.join(str(i) for i in pathList) + '\n\n\n')

    # ******* 返回图谱的统计信息 *******
    # for one in fullMapNodeStatistic:
    #     print("one:",one)
    #     ans=KgTest.objects.get(nodeID=one)
    #     ans=object_to_json(ans)
    #     name=str2list(ans['actionName'])
    #     strAns="ID:"+one+", Action:"+name
    #     with open("verify/output/partMapNodes.txt","a", encoding='utf-8') as outfile:
    #         outfile.write(strAns + '\n')
    # for one in partMapNodeStatistic:
    #     ans=KgTest.objects.get(nodeID=one)
    #     ans=object_to_json(ans)
    #     name=str2list(ans['actionName'])
    #     strAns="ID:"+one+", Action:"+name
    #     with open("verify/output/fullMapNodes.txt","a", encoding='utf-8') as outfile:
    #         outfile.write(strAns + '\n')
    partMapNodeStatisticCopy = partMapNodeStatistic.copy()
    fullMapNodeStatisticCopy = fullMapNodeStatistic.copy()
    statistics1 = numberCount(partMapNodeStatistic)
    ret5 = "KG上被部分匹配的节点及次数：" + json.dumps(statistics1)
    # fullMapNodeStatistic.sort()
    statistics2 = numberCount(fullMapNodeStatistic)
    # statistics2 = sorted(statistics2.items(), key=lambda item: item[0])
    ret6 = "KG上被完全匹配的节点及次数：" + json.dumps(statistics2)
    partMapAllApkRate = len(list(set(partMapNodeStatisticCopy))) / len(kgList)
    ret7 = "KG上被部分匹配的节点覆盖率(部分匹配节点数/KG节点总数)：" + str(round(partMapAllApkRate, 4) * 100) + '%'
    fullMapAllApkRate = len(list(set(fullMapNodeStatisticCopy))) / len(kgList)
    ret8 = "KG上被完全匹配的节点覆盖率(完全匹配节点数/KG节点总数)：" + str(round(fullMapAllApkRate, 4) * 100) + '%'

    with open(report_path, "a", encoding='utf-8') as outfile:  # 这种方法会自动关闭文件
        outfile.write("\n\n****************** KG Statistics ******************\n")
        outfile.write(ret5 + '\n')
        outfile.write(ret6 + '\n')
        outfile.write(ret7 + '\n')
        outfile.write(ret8 + '\n')

    return HttpResponse("hello world")


# *********************** 一、粒度：特征 ***************************
def verifyByFeature(request):
    # 分别读取api和per的txt文件，将apis和permissions分别放到list中
    perList = []
    apiList = []
    kgFeaturesList = []
    perFeatureFile = open(perFeature_path, 'r', encoding='utf-8', newline="")
    apiFeatureFile = open(apiFeature_path, 'r', encoding='utf-8', newline="")
    kgFeaturesFile = open(kgFeatures_path, 'r', encoding='utf-8', newline="")
    for row in perFeatureFile.readlines():
        perList.append(row.strip())
    for row in apiFeatureFile.readlines():
        apiList.append(row.strip())
    for row in kgFeaturesFile.readlines():
        kgFeaturesList.append(row.strip())
    perFeatureFile.close()
    apiFeatureFile.close()
    kgFeaturesFile.close()

    """
    首先读取某个APK的特征文件。
    给APK的特征文件人工添加permission特征组和API特征组的开始和结束字符，如perStart\perEnd\apiStart\apiEnd
    """
    apkFile = open(testApk_path, 'r', encoding='utf-8', newline="")
    apkFeatures = []  # 存放APK的特征
    global flag
    for row in apkFile.readlines():
        # print("line:"+line)
        line = row.strip()
        if line == "perStart":
            # 操作
            flag = 1
            continue
        elif line == 'perEnd':
            flag = 0
            continue
        elif line == 'apiStart':
            # 操作
            flag = 1
            continue
        elif line == 'apiEnd':
            flag = 0
            break
        else:
            pass
        if flag == 1:
            apkFeatures.append(line.lstrip("L"))  # 删除开头的“L”

    # 1. 计算某个APK的特征覆盖率，这里的映射关系是：KG->某个APK特征文件，查看KG特征的完整性
    mapCount = 0
    nmapCount = 0

    # 在写入映射失败的特征前，先清空txt文件，防止记录重复
    with open("verify/output/nmapFetures.txt", "a", encoding='utf-8') as nmapFeatureFile:
        nmapFeatureFile.truncate(0)

    # 在写入映射成功的特征前，先清空txt文件，防止记录重复
    with open("verify/output/mapFeatures.txt", "a", encoding='utf-8') as mapFeatureFile:
        mapFeatureFile.truncate(0)
    # 单独测试permission的覆盖率
    # for feature in apkFeatures:  # 对于apk的每个per feature，都去数据表中查看是否有对应的
    #     # tmp='%'+feature+'%'
    #     if feature in perList:  # permission的匹配度
    #         mapCount=mapCount+1
    #         # print('映射成功的为：', feature)
    #     else:
    #         nmapCount=nmapCount+1
    #         # print('映射失败的为：', feature)
    #         # 将映射失败的写入本地文件nmapFeatures.txt中
    #         with open("verify/output/nmapFetures.txt", "a", encoding='utf-8') as outfile: # 这种方法会自动关闭文件
    #             outfile.write(feature+'\n')

    # 单独测试api的覆盖率
    # for feature in apkFeatures:  # 对于apk的每个api feature，都去数据表中查看是否有对应的
    #     if feature in str(apiList): # api的匹配度
    #         mapCount = mapCount + 1
    #         print('映射成功的为：', feature)
    #     else:
    #         nmapCount = nmapCount + 1
    #         print('映射失败的为：', feature)
    #         # 将映射失败的写入本地文件nmapFeatures.txt中
    #         with open("verify/output/nmapFetures.txt", "a", encoding='utf-8') as outfile:  # 这种方法会自动关闭文件
    #             outfile.write(feature + '\n')

    # 测试所有特征的覆盖率
    for feature in apkFeatures:  # 对于apk的feature，都去数据表中查看是否有对应的
        if feature in str(kgFeaturesList):
            mapCount = mapCount + 1
            print('映射成功的为：', feature)
            # 将映射成功的写入本地文件mapFeatures.txt中，以为节点匹配做准备
            with open("verify/output/mapFeatures.txt", "a", encoding='utf-8') as outfile:  # 这种方法会自动关闭文件
                outfile.write(feature + '\n')
        else:
            nmapCount = nmapCount + 1
            print('映射失败的为：', feature)
            # 将映射失败的写入本地文件nmapFeatures.txt中
            with open("verify/output/nmapFetures.txt", "a", encoding='utf-8') as outfile:  # 这种方法会自动关闭文件
                outfile.write(feature + '\n')

    mapRate = mapCount / (mapCount + nmapCount)
    ret1 = '特征映射成功率：' + str(round(mapRate, 4) * 100) + '%'  # 以70.34%的形式输出
    with open(report_path, "a", encoding='utf-8') as outfile:  # 这种方法会自动关闭文件
        outfile.write('************** 1 *************\n')
        outfile.write(ret1 + '\n')
    return HttpResponse(ret1)


"""
*********************** 二、粒度：节点 ***************************
映射关系为 APK的特征文件->KG中的特征，
然后根据特征的匹配情况定位到某个节点，这样就可以解释该APK执行了哪些行为
"""


def verifyByNode(request):
    # 打开映射成功的txt文件，去数据表中找匹配的api
    mapFeatures = open("verify/output/mapFeatures.txt", 'r', encoding='utf-8', newline="")
    apiIdList = []  # 记录下匹配成功的api的id
    perIdList = []  # 记录下匹配成功的per的id

    # 记录下匹配到的api的id
    for row in mapFeatures.readlines():
        line = row.strip()
        # 将字符串拆分后然后再再重组，不然可能出现匹配不上的问题
        tmp1 = line.split('/')
        tmp = '/'.join(tmp1)
        ans = augmenTestAPi.objects.filter(apiName__icontains=tmp)
        if ans:
            ans = list(ans)
            for one in ans:
                # apiList.append({'id':one.id,'name':one.apiName})
                apiIdList.append(one.id)
        else:
            pass

    # 读取一次后，需要先暂时关闭然后重新读取，不然下面的遍历代码不会生效
    mapFeatures.close()
    mapFeatures = open("verify/output/mapFeatures.txt", 'r', encoding='utf-8', newline="")

    # 记录下匹配到的permission的id
    for row in mapFeatures.readlines():
        line = row.strip()
        tmp1 = line.split('.')
        tmp = '.'.join(tmp1)
        ans = PerTest.objects.filter(perName__icontains=tmp)
        if ans:
            ans = list(ans)
            for one in ans:
                # perList.append({'id':one.id, 'name':one.perName})
                perIdList.append(one.id)
        else:
            pass

    partNode = []  # 匹配上了部分特征的节点，存储着这些节点的id
    fullNode = []  # 完全匹配上的节点，存储着这些节点的id
    kgModel = KgTest.objects.values()
    kgList = list(kgModel)

    # **************根据api来匹配节点**********************
    for apiId in apiIdList:
        # count=0 # 统计匹配上的api特征数量
        for one in kgList:
            apiStr = one['apiList']
            if apiStr == '':
                continue
            else:
                if apiStr.find("'"):
                    apiStr = apiStr.replace("'", '')
                if apiStr.find(','):
                    apiStr2List = apiStr.split(',')  # 数组中每个元素的数据类型是str
                else:
                    apiStr2List = apiStr
                apiStr2List = list(map(int, apiStr2List))  # 将值为数字的字符串数组转变为数值数组
            if apiId in apiStr2List:
                partNode.append(one['nodeID'])

    # 根据per来匹配节点
    # **************查看能匹配上的节点**********************
    for perId in perIdList:
        # count=0 # 统计匹配上的api特征数量
        for one in kgList:
            perStr = one['perList']
            if perStr == '':
                continue
            else:
                if perStr.find("'"):
                    perStr = perStr.replace("'", '')
                if perStr.find(','):
                    perStr2List = perStr.split(',')  # 数组中每个元素的数据类型是str
                else:
                    perStr2List = perStr
                perStr2List = list(map(int, perStr2List))  # 将值为数字的字符串数组转变为数值数组
            if perId in perStr2List:
                partNode.append(one['nodeID'])
    # 去重和排序
    partNode = list(set(partNode))
    partNode = sorted(partNode)

    # **************查看完整匹配的节点**********************
    for nodeId in partNode:  # 这里面存放的是部分特征映射的节点的ID
        ans = KgTest.objects.get(nodeID=nodeId)
        ans = object_to_json(ans)
        kgPerList = str2list(ans['perList'])
        kgApiList = str2list(ans['apiList'])
        perMapCount = 0
        apiMapCount = 0

        # 遍历一个节点的perList，查看先前特征匹配上的permission是否有与之对应的
        for one in kgPerList:
            if one in perIdList:
                print('perOne', one)
                perMapCount = perMapCount + 1
        for one in kgApiList:
            if one in apiIdList:
                apiMapCount = apiMapCount + 1
        rate = (perMapCount + apiMapCount) / (len(kgPerList) + len(kgApiList))
        if rate > 0.7:  # 这些是完全特征匹配的
            fullNode.append(ans['nodeID'])
        # 去重和排序
    fullNode = list(set(fullNode))
    fullNode = sorted(fullNode)

    allMapNum = len(kgList)
    # 计算部分特征匹配的节点覆盖率
    partMapNum = len(partNode)
    partMapRate = partMapNum / allMapNum
    ret1 = '部分特征映射的节点覆盖率：' + str(round(partMapRate, 4) * 100) + '%'  # 以70.34%的形式输出
    # 计算完全特征匹配的节点覆盖率
    fullMapNum = len(fullNode)
    fullMapRate = fullMapNum / allMapNum
    ret2 = '完全特征映射的节点覆盖率：' + str(round(fullMapRate, 4) * 100) + '%'  # 以70.34%的形式输出
    # for one in partNode:
    #     print("one", one)
    with open(report_path, "a", encoding='utf-8') as outfile:  # 这种方法会自动关闭文件
        outfile.write(ret1 + '\n')
        outfile.write(ret2 + '\n')
        outfile.write("完全匹配上的节点:" + ','.join(str(i) for i in fullNode) + '\n')
    return HttpResponse(ret1 + '\n' + ret2)


def verifyByPath(request):
    pass
    return HttpResponse("hello")


# 下列为工具函数
# objects.get()结果转换
def object_to_json(obj):
    ans = {}
    # obj.__dict__ 可将django对象转化为字典
    for key, value in obj.__dict__.items():
        # 将字典转化为JSON格式
        ans[key] = value
    return ans


# 将从数据表中取出来的形如 23,89,90 的字符串转化为数值数组
def str2list(str):
    ret = []
    if str == '':
        pass
    else:
        if str.find("'"):
            str = str.replace("'", '')
        if str.find(','):
            ret = str.split(',')  # 数组中每个元素的数据类型是str
        else:
            ret = str
        ret = list(map(int, ret))  # 将值为数字的字符串数组转变为数值数组
    return ret


"""
传入一个带有重复数据的数组，统计这些数据及其出现的次数
"""


def numberCount(myList):
    myListCopy = sorted(myList)
    tmp = list(set(myList))
    ret = dict()
    for one in tmp:
        ret[one] = myListCopy.count(one)
    return ret
