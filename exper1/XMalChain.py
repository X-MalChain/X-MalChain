import re
import glob
import json
import shutil
import datetime
import time
import codecs  # 将ansi编码的文件转为utf-8编码的文件
import os
from operator import itemgetter, eq
from collections import Counter

import django
import sys
from django.http import HttpResponse
from augment import do_feature_file_v1

sys.path.append('../')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mwep.settings')

django.setup()

from common import models
from django.db.models import Q

from androguard.misc import AnalyzeAPK
from androguard.core.androconf import load_api_specific_resource_module
from manager.views import dict_trans_list
from common.models import ApiTest, PerTest, KgBackup, relBackup, ApiSim, ApiSDK
from exper1.augment import joint_path

kg_permissions = []  # all permissions in kg/database
kg_apis = []  # all apis in kg/database
apis_from_test = []  # Apitest中的apis
kg_features = []  # all features(permissions+apis) in kg

# 原有的解释结果
report_path = '../detect/output/xmalchain/report.txt'
match_report = '../detect/output/xmalchain/match_report.txt'
report_log = '../detect/output/xmalchain/log.txt'
# 新增后的解释结果
# report_path='../detect/output/xmalchain_augment/report.txt'
# match_report = '../detect/output/xmalchain_augment/match_report.txt'
# report_log='../detect/output/xmalchain_augment/log.txt'

statics_behavior=[]


fileID = 0


def get_pers_apis_after_augment():
    """
    :return: :list: all permissions in kg
            :list: all apis in kg
    """
    api_list = get_apis_from_wkg_after_augment()
    per_list = get_pers_from_wkg_after_augment()
    kg_list = list(per_list)  # 直接复制一份数据
    # permissions + apis = kg 中的所有特征
    for one in api_list:
        kg_list.append(one)

    return per_list, api_list, kg_list


def get_apis_from_wkg_after_augment():
    """
    获取那些已经被确立为图谱节点特征的apis
    """
    api_list = models.augmentNodeIn.objects.values('apiList')
    api_list = dict_list(api_list, 'apiList')
    api_num = []
    apis_list = []
    for one in api_list:
        if one != '' and one != ' ':
            if one.find(',') != -1:
                tmp = one.split(',')
                for api in tmp:
                    if api not in api_num and api != '':
                        api_num.append(api)
            elif one not in api_num:
                api_num.append(one)
    for one in api_num:
        try:
            ans = models.augmentAPiIn.objects.get(id=int(one))
            api = ans.apiName.replace(' ', '')
            apis_list.append(api)
        except:
            print('augmentAPiIn matching query does not exist:', one)
    return apis_list


def get_pers_from_wkg_after_augment():
    """
    获取那些已经被确立为图谱节点特征的permissions
    """
    per_list = models.augmentNodeIn.objects.values('perList')
    per_list = dict_list(per_list, 'perList')
    per_num = []
    pers_list = []
    for one in per_list:
        if one != '' and one != ' ':
            if one.find(',') != -1:
                tmp = one.split(',')
                for api in tmp:
                    if api not in per_num and api != '':
                        per_num.append(api)
            elif one not in per_num:
                per_num.append(one)
    for one in per_num:
        try:
            ans = models.augmentPerIn.objects.get(id=int(one))
            per = ans.perName.replace(' ', '')
            pers_list.append(per)
        except:
            print('augmentPerIn matching query does not exist:', one)
    return pers_list


def get_apis_from_test_after_augment():
    api_list = models.augmentAPiIn.objects.values('apiName')
    # 此时的per_list api_list是由字典组成的数组，因此进行下述处理
    api_list = dict_list(api_list, 'apiName')
    return api_list


def dict_list(demo_list, _flag):
    """
    :param demo_list:由字典组成的数组 QuerySet，形如：[{'perName': 'android.permission.ACCESS_BACKGROUND_LOCATION'}, {'perName': 'android.permission.ACCESS_COARSE_LOCATION'}]
    :param _flag: 指示传入的数组是permissions还是apis，又或者是node
    :return a sample list
    """
    try:
        ret_list = []
        for i in demo_list:
            ret_list.append(i[_flag])
        return ret_list
    except:
        print('Error: dict_list throw a exception!')


def generate_cg(apk):
    """
    :param apk:带完整路径和后缀的apk文件
    :return: 该apk利用androguard生成的gml文件，即call graph，:param
            :string: apk_name: 该apk的名称，不带后缀
    """
    filename = os.path.split(apk)[1]  # 文件的名称(带后缀)
    apk_name = filename.split('.')[0]  # 文件名（不带后缀）

    # if os.path.exists('../detect/outputCG/' + apk_name + '.txt'):
    #     file = os.path.join('../detect/outputCG/', apk_name + '.gml')  # 存放apk的特征文件
    #     return file, apk_name
    # else:
    # shutil.rmtree('detect/outputCG')  # 删除该文件夹以及该文件夹下的所有文件
    # os.mkdir('detect/outputCG')  # 创建新的文件夹
    os.system('androguard cg ' + apk + ' -o ../detect/outputCG/' + apk_name + '.gml')
    # os.system('androguard cg ' + apk + ' -o detect/outputCG/' + apk_name + '.gexf')
    # file = glob.glob('detect/outputCG/' + apk_name + '.gml')
    file = os.path.join('../detect/outputCG/', apk_name + '.gml')  # 存放apk的特征文件
    return file, apk_name


def gml_txt(gml_file, apk_name):
    """
    :param gml_file: a .gml file generated by generate_cg，传入的gml文件路径是 detect/outputCG/.gml
    :param apk_name:apk's name
    # :return: a .txt file generated from .gml file
    """
    # print('file:', gml_file)
    new_file = apk_name + '.txt'
    # print('gml_file')
    os.rename(gml_file, '../detect/outputCG/' + new_file)
    # file = glob.glob('detect/outputCG/' + apk_name + '.txt')
    file = os.path.join('../detect/outputCG/', apk_name + '.txt')  # 存放apk的特征文件


def analyse(data):
    pattern = re.compile('edge \[\n(.*?)]', re.S)  # 使用re.S参数以后，正则表达式会将这个字符串作为一个整体，在整体中进行匹配
    return_edge_list = pattern.findall(data)
    pattern = re.compile('node \[\n(.*?)external', re.S)
    return_node_list = pattern.findall(data)
    return return_node_list, return_edge_list


def get_data(url):
    f = open(url, "r", encoding='utf-8')
    data = f.read()
    f.close()
    return data


def find_related_node(source, edge_list, node_list):
    """
    :param source: id of source node
    :param edge_list: edges list from .gml
    :param node_list:nodes list from .gml
    :return :int:id of node which is related to source node
    """
    print('一跳source：', source)

    ret_api = ''
    for edge in edge_list:
        tmp = re.findall('\d+', edge)
        _source = int(tmp[0])
        _target = int(tmp[1])
        if _source == source:
            api_location = re.findall('L.*?;->.*?]', node_list[_target])
            print('_source api location:', api_location)
            if api_location:
                continue
            else:
                api_location = re.findall(
                    '(L.*?;->.*?)"', node_list[_target])
                if api_location:
                    for api in api_location:
                        tmp = api
                        if tmp[0] == "L":  # 去掉开头的L
                            tmp = api[1:]
                        judge = tmp.find("(")  # 截取字符串
                        if judge != -1:
                            tmp = tmp[:judge]
                        ret_api = tmp

    return _target, ret_api


def extract_features_plus(apk_name, apk_path):
    """
    :function 在原有的基础上多引入正则表达式，从而节约时间
    :param txt:a .txt file generated from .gml
    :return feature_txt: a .txt file consists of key apis & permissions of an app
    """
    start_time = time.time()

    a, d, dx = AnalyzeAPK(apk_path)
    permissions = a.get_permissions()

    feature_filename = os.path.join('../detect/output_features/', apk_name + '_features.txt')  # 存放apk的特征文件
    feature_file = open(feature_filename, 'w', encoding='utf-8')
    # **********Write Information Belows*************
    # 1. write permissions
    for per in permissions:
        if per in kg_permissions:
            feature_file.write(per + '\n')
    feature_file.write('\n')

    # 2. write apis through .gml
    data = get_data(os.path.join('../detect/outputCG/', apk_name + '.txt'))
    node_list, edge_list = analyse(data)
    global apis_from_test
    global kg_apis

    data = data.replace("\n", '')

    pattern1 = re.compile('node\s\[?.*?;->.*?\[access_flag.*?]', re.S)  # 寻找可能的入口函数
    ans1 = pattern1.findall(data)  # 查找出发的节点
    # 寻找从这些节点出发的目的节点
    for one in ans1:
        source_id_str = re.findall('id\s*(\d+)', one.split('node ')[-1])[0]  # string型数据，对确定的唯一一个node，它的node id是唯一的
        # 去edges中查找以source id为起点的节点
        targets_id_by_edges = re.findall('source ' + source_id_str + '\s*target\s*(\d+)',
                                         data)  # 一个节点可能和多个节点有关联，这些id也均为string型
        # 去node list查找node
        api_list = []  # 存放即将写入特征文件的api
        for node_id in targets_id_by_edges:
            api_location = re.findall('(L.*?;->.*?)"', node_list[int(node_id)])  # 不带[]的有可能是api
            if api_location:
                for api in api_location:
                    tmp = api
                    if tmp[0] == "L":  # 去掉开头的L
                        tmp = api[1:]
                    judge = tmp.find("(")
                    if judge != -1:
                        tmp = tmp[:judge]
                    if tmp in str(apis_from_test):  # 标准api
                        # print('stand api:', tmp)
                        api_list.append(tmp)
                    else:
                        part_api = re.findall(';->.*', tmp)
                        # print('part_api0:', part_api)
                        if part_api:
                            part_api = part_api[0].replace("'", '')
                            # print('part_api1:', part_api)
                            for api in apis_from_test:
                                api_name = re.findall(';->.*', api)
                                if api_name:
                                    api_name = api_name[0].replace("'", '')
                                    if api_name == part_api:
                                        # print('part_api2:', part_api)
                                        # print('api:', api_name)
                                        api_list.append(api)
        # 考虑到api是不可以复用的，因此不能去除重复的？
        # 删减/保留api会影响匹配上的节点（对于原匹配算法来说）
        i = 0  # 从类似[1,2,2,3,3,3,4,1]转变为[1,2,3,4,1]
        while i < len(api_list) - 1:
            if api_list[i] == api_list[i + 1]:
                del api_list[i]
            else:
                i = i + 1
        intsect = list(set(kg_apis).intersection(set(api_list)))
        if len(api_list) > 0 and len(intsect) > 0:
            feature_file.write('entrypoint node id:' + str(source_id_str) + '\n')
            for api in api_list:
                feature_file.write(api + '\n')

    feature_file.close()

    end_time = time.time()
    print('特征提取时间为：', str(end_time - start_time))


def database_test():
    ans = models.augmenAPiIn.objects.count()
    print('ans:', ans)


def read_path(root_path):
    """
    :param root_path:样本根路径，每个样本都有一个文件夹，文件夹中存储着.apk以及report等，当然.apk可能和report又分属于不同的子文件夹\
    :return dir_name_list: 当前根路径下所有二级文件夹的名称

    补充：listdir()方法就只能获得第一层子文件或文件夹
    """
    dir_name_list = []
    if (os.path.exists(root_path)):  # 判断路径是否存在
        files = os.listdir(root_path)  # 读取该路径下的所有文件/文件夹
        for file in files:
            second_dir = os.path.join(root_path, file)  # 使用join函数将当前目录和文件所在根目录连接起来
            if (os.path.isdir(second_dir)):  # 当前的是文件夹
                dir_name = os.path.split(second_dir)[1]  # 获取文件夹的名称
                dir_name_list.append(dir_name)
    return dir_name_list


def find_apk(apk_root_path, apk_name):
    """
    :param apk_root_path: string .apk文件的根目录，可能也需要文件的递归，具体看数据集压缩包的文件结构
    :param apk_name: string: 该apk应该有的名字
    :return apk_true_path: string .apk文件存在的真实路径，用户可以通过该路径访问apk文件
    本数据集的文件组织结构为 /home/wuyang/Experiments/Datas/malwares/googlePlay/code_reports/AceCard/AceCard/xx.apk
    传入的参数应该为这样的形式：/home/wuyang/Experiments/Datas/malwares/googlePlay/code_reports/AceCard

    注意：因为不是所有的apk的文件组织形式都一样，所以这种方=方法不太能行🉐通
    """
    print('root path:', apk_root_path)
    files = glob.glob(apk_root_path + '/' + apk_name + '/*.apk')  # 找到.apk文件
    print('files:', files)
    dstpath = '/home/wuyang/Experiments/Datas/malwares/googlePlay/apk_sample/'
    apk_file = files[0]
    apk_new_file = apk_root_path + '/' + apk_name + '/' + apk_name + '.apk'
    os.rename(apk_file, apk_new_file)
    # 复制重命名后的文件
    shutil.copy(apk_new_file, dstpath + apk_name + '.apk')
    # print('new_file', new_file)


def find_apk_v1(apk_root_path, apk_name):
    """
    :param apk_root_path: string .apk文件的根目录，如/home/wuyang/Experiments/Datas/malwares/googlePlay/code_reports/AceCard，然后查找该目录下的.apk文件
    :param apk_name: string 该.apk文件的发布名称
    """
    dstpath = '/home/wuyang/Experiments/Datas/malwares/googlePlay/apk_sample/'
    for filepath, dirnames, filenames in os.walk(apk_root_path):
        for filename in filenames:
            if os.path.splitext(filename)[1] == '.apk':
                # print('apk:', filename)
                old_path = os.path.join(filepath, filename)
                # 复制apk文件到新的目录
                shutil.copy(old_path, dstpath + apk_name + '.apk')


def object_to_json(obj):
    """
    objects.get()结果转换
    :param obj: django的model对象
    """
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


def numberCount(myList):
    """
    ：param myList:传入一个带有重复数据的数组，统计这些数据及其出现的次数
    """
    myListCopy = sorted(myList)
    tmp = list(set(myList))
    ret = dict()
    for one in tmp:
        ret[one] = myListCopy.count(one)
    return ret


def XMalChain():
    """
    使用扩充后的知识图谱来匹配APK
    """
    # 在写入映射失败的特征前，先清空txt文件，防止记录重复
    with open("detect/output/nmapFetures.txt", "a", encoding='utf-8') as nmapFeatureFile:
        nmapFeatureFile.truncate(0)

    global kg_apis, kg_permissions, kg_features, apis_from_test
    kg_permissions, kg_apis, kg_features = get_pers_apis_after_augment()  # 初始化数据：get all permissions&apis from kg/database
    apis_from_test = get_apis_from_test_after_augment()

    # 1、生成98个样本apk的特征文件
    # sample_apks_folder_path = '/home/wuyang/Experiments/Datas/malwares/sample_apk_100'
    sample_apks_folder_path = '/home/wuyang/Experiments/Datas/malwares/googlePlay/apk_sample'
    # sample_apks_folder_path='/home/wuyang/Experiments/Datas/malwares/part_androzoo/androzoo_apk_100'
    # sample_apks_folder_path = '/home/wuyang/Experiments/Datas/tmpApk/protest'
    # sample_apks_folder_path='/media/wuyang/WD_BLACK/AndroidMalware/xmal_test'

    match_report_ans = []

    # 为了避免Django项目内的文件过多，生成CG文件和特征文件前先将文件夹清空
    # shutil.rmtree('../detect/outputCG')  # 删除该文件夹以及该文件夹下的所有文件
    shutil.rmtree('../detect/output_features')
    # os.mkdir('../detect/outputCG')  # 创建新的文件夹
    os.mkdir('../detect/output_features')
    fullMapNodeStatistic = []  # 对于所有的APK文件，统计KG上每个节点的映射情况，对应的是完全匹配的情况
    partMapNodeStatistic = []  # 对于所有的APK文件，统计KG上每个节点的映射情况，对应的是部分匹配的情况
    featureMapStatistic = []  # 对于所有的APK文件，统计KG上每个特征的映射情况
    apk_feature_map = []  # 对于每一个apk，映射上的特征/该APK总的特征数。里面存储了所有apk的特征映射情况
    pathMapStatistic = []  # 对于所有的APK文件，统计KG上每条路径的映射情况
    kgModel = models.augmentNodeIn.objects.values()
    kgList = list(kgModel)

    # ********** 二、依次匹配每一个文件 *************
    with open(report_path, "a", encoding='utf-8') as report:
        # 读取所有的APK
        global flag
        files = glob.glob(sample_apks_folder_path + '/*.apk')
        file_id = 0

        time = datetime.datetime.today()
        report.write(
            "******************\n " + "After Augmentation-Dataset: " + sample_apks_folder_path + "\n" + str(
                time) + " \n******************\n")
        # report.write("******************\n " + '计算节点匹配率时，去掉permission' + " ******************\n\n")

        # 依次读取每一个APK
        for f in files:  # f形如D:/input/apk01.apk
            file_id = file_id + 1
            t = '************' + str(file_id) + '************'
            print(t)
            flag = 0
            # 生成APK的特征文件，如果文件存在则不另外生成
            filename = os.path.split(f)[1]  # 文件的名称(带后缀)
            apk_name = filename.split('.')[0]  # 文件名（不带后缀）
            print("apk aaaa:", f)
            if os.path.exists('../detect/output_features/' + apk_name + '_features.txt'):
                if os.path.exists('../detect/outputCG/' + apk_name + '.txt'):
                    pass
                else:
                    gml, apk_name = generate_cg(f)  # 输入apk，生成cg
                    gml_txt(gml, apk_name)  # 将cg转化为txt文件
            else:
                if os.path.exists('../detect/outputCG/' + apk_name + '.txt'):
                    extract_features_plus(apk_name, f)  # 提取特征,生成特征文件
                else:
                    gml, apk_name = generate_cg(f)  # 输入apk，生成cg
                    gml_txt(gml, apk_name)  # 将cg转化为txt文件

            # gml, apk_name = generate_cg(f)  # 输入apk，生成cg
            # gml_txt(gml, apk_name)  # 将cg转化为txt文件
            # extract_features_plus(apk_name, f)  # 提取特征,生成特征文件

            # 写入report
            report.write("****************** APK " + str(file_id) + " ******************\n")  # 记录当前APK的名字
            report.write("文件名：" + apk_name + '\n')  # 记录当前APK的名字
            retJson0 = apk_name
            # 首先读取某个APK的特征文件
            feature_file_path = '../detect/output_features/' + apk_name + '_features.txt'
            # 首先读取某个APK的特征文件
            apk_file = open(feature_file_path, 'r', encoding='utf-8', newline="")
            apkFeatures = []  # 存放该APK的特征
            mapFeatureList = []  # 存放映射上的APK的特征
            nmapFeatureList = []  # 存放没映射上的APK的特征
            a = 0
            for row in apk_file.readlines():  # 去掉多余的信息行
                line = row.strip()
                if line != '' and line.find('entrypoint') == -1:
                    apkFeatures.append(line)

            # *******1. 计算某个APK的特征覆盖率，这里的映射关系是：KG->某个APK特征文件，查看KG特征的完整性*******
            mapCount = 0
            nmapCount = 0

            print('apk features:', apkFeatures)

            # 测试所有特征的覆盖率
            print('特征匹配率...')
            for feature in apkFeatures:  # 对于apk的feature，都去kg中查看是否有对应的
                tmp = feature.strip()
                judge = tmp.find("(")
                if judge != -1:
                    tmp = tmp[:judge]
                # print('tmp:', tmp)
                if tmp.find(".") != -1:  # permissions
                    tmp1 = tmp.split(".")
                    tmp = ".".join(tmp1)
                    if tmp in str(kg_permissions):
                        mapCount = mapCount + 1
                        if feature not in mapFeatureList:
                            mapFeatureList.append(feature)
                        featureMapStatistic.append(feature)
                    else:
                        nmapCount = nmapCount + 1
                        if feature not in nmapFeatureList:
                            nmapFeatureList.append(feature)
                elif tmp.find("/") != -1:  # apis
                    tmp1 = tmp.split(";")
                    tmp = ";".join(tmp1)
                    # print('tmp:', tmp)
                    if tmp in str(kg_apis):
                        mapCount = mapCount + 1
                        mapFeatureList.append(feature)
                        featureMapStatistic.append(feature)
                    else:
                        # 考虑到sdk level
                        try:
                            # print("????????????????")
                            ans = models.augmentAPiIn.objects.get(apiName=tmp)
                            if ans:
                                addList = ans.addList
                                repList = ans.repList
                                # print('addList：', addList)
                                # print('repList：', repList)
                                if addList != '':
                                    add_obj = ApiSim.objects.get(id=int(addList))
                                    add_apis = add_obj.list
                                    add_apis = add_apis.split(',')
                                    for api in add_apis:
                                        api = api.replace(' ', '')
                                        if api in str(kg_apis):
                                            # print('新增 by sim：',api)
                                            mapCount = mapCount + 1
                                            mapFeatureList.append(api)
                                if repList != '':
                                    rep_obj = ApiSDK.objects.get(id=int(repList))
                                    rep_apis = rep_obj.list
                                    rep_apis = rep_apis.split(',')
                                    for api in rep_apis:
                                        api = api.replace(' ', '')
                                        if api in str(kg_apis):
                                            # print('新增 by sdk：', api)
                                            mapCount = mapCount + 1
                                            mapFeatureList.append(api)
                            else:
                                print('not find0：', tmp)
                        except:
                            # print('not find：', tmp)
                            pass
                        # if addList:

                    # else:
                    # nmapCount = nmapCount + 1
                    # print('映射失败的为：', feature)
                    # if feature not in nmapFeatureList:
                    #     nmapFeatureList.append(feature)
                    # else:
                    #     pass

            # 在写入映射成功的特征前，先清空映射成功的txt文件，防止记录重复
            with open("../detect/output/mapFeatures_xmal.txt", "a", encoding='utf-8') as mapFeatureFile:
                mapFeatureFile.truncate(0)
            # 将映射成功的写入本地文件mapFeatures.txt中，以为节点匹配做准备
            with open("../detect/output/mapFeatures_xmal.txt", "a", encoding='utf-8') as outfile:  # 这种方法会自动关闭文件
                for one in mapFeatureList:
                    outfile.write(one + '\n')

            if mapCount > 0:
                mapRate = mapCount / (mapCount + nmapCount)
                retJson1 = str(round(mapRate, 4) * 100) + '%'
                ret1 = '特征映射成功率(映射上的特征数/APK总的特征数)：' + str(
                    round(mapRate, 4) * 100) + '%'  # 以70.34%的形式输出
                report.write(ret1 + '\n')
            else:
                pass
            apk_feature_map.append({'apk': apk_name, 'mapRate': retJson1})

            # print('节点匹配')
            print('节点匹配率...')
            # *******2. 计算某个APK覆盖的节点 *******
            # 打开映射成功的txt文件，去数据表中找匹配的api
            mapFeatures = open("../detect/output/mapFeatures_xmal.txt", 'r', encoding='utf-8', newline="")
            apiIdList = []  # 记录下匹配成功的api的id
            perIdList = []  # 记录下匹配成功的per的id

            # 记录下匹配到的api的id
            for row in mapFeatures.readlines():
                line = row.strip()
                # 将字符串拆分后然后再再重组，不然可能出现匹配不上的问题
                if line.find(";") != -1:  # 说明处理的是api
                    tmp1 = line.split(';')
                    tmp = ';'.join(tmp1)  # tmp为按顺序出现的api
                    ans = models.augmentAPiIn.objects.filter(apiName=tmp)
                    if ans:
                        ans = list(ans)
                        for one in ans:
                            apiIdList.append(one.id)
                    else:
                        pass
                else:
                    continue

            # 读取一次后，需要先暂时关闭然后重新读取，不然下面的遍历代码不会生效
            mapFeatures.close()
            mapFeatures = open("../detect/output/mapFeatures_xmal.txt", 'r', encoding='utf-8', newline="")

            # 记录下匹配到的permission的id
            for row in mapFeatures.readlines():
                line = row.strip()
                if line.find(".") != -1:
                    tmp1 = line.split('.')
                    tmp = '.'.join(tmp1)
                    ans = models.augmentPerIn.objects.filter(perName__icontains=tmp)
                    if ans:
                        ans = list(ans)
                        for one in ans:
                            perIdList.append(one.id)
                    else:
                        pass
                else:
                    continue

            partNode = []  # 匹配上了部分特征的节点，存储着这些节点的id
            fullNode = []  # 完全匹配上的节点，存储着这些节点的id

            # 第1种匹配算法
            # **************根据api来匹配节点**********************

            # 分界线，两种匹配算法，以下是第2种算法(原来的匹配算法)
            # 打开映射成功的txt文件，去数据表中找匹配的api
            # 根据per来匹配节点
            # **************查看能匹配上的节点**********************
            for perId in perIdList:
                for one in kgList:
                    perStr = one['perList']
                    if perStr == '' or perStr == ' ':
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

            # **************根据api来匹配节点**********************
            for apiId in apiIdList:
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

            # 去重和排序，保持原本顺序不变
            order = list(partNode)  # 复制
            # print("old:", partNode)
            partNode = list(set(partNode))  # 去重
            partNode.sort(key=order.index)  # 恢复原本顺序
            # print("now:", partNode)

            for node in partNode:
                partMapNodeStatistic.append(node)

            # **************查看完整匹配的节点**********************
            retMapData = []  # 返回匹配的情况，包括：节点、节点匹配率、匹配上的特征、匹配失败的特征
            for nodeId in partNode:  # 这里面存放的是部分特征映射的节点的ID
                ans = models.augmentNodeIn.objects.get(nodeID=nodeId)
                ans = object_to_json(ans)
                kgPerList = str2list(ans['perList'])
                kgApiList = str2list(ans['apiList'])
                perMapCount = 0
                apiMapCount = 0

                dicTmp = {"node": nodeId}  # 给每一个节点创建一个字典
                dicTmp["allApi"] = kgApiList
                dicTmp["allPer"] = kgPerList

                mapApi = []
                nmapApi = []
                mapPer = []
                nmapPer = []

                # 遍历一个节点的perList，查看先前特征匹配上的permission是否有与之对应的
                for one in kgPerList:
                    if one in perIdList:
                        perMapCount = perMapCount + 1
                        mapPer.append(one)
                    else:
                        nmapPer.append(one)
                for one in kgApiList:
                    if one in apiIdList:
                        apiMapCount = apiMapCount + 1
                        mapApi.append(one)
                    else:
                        nmapApi.append(one)
                rate = (perMapCount + apiMapCount) / (len(kgPerList) + len(kgApiList))
                dicTmp["mapApi"] = mapApi
                dicTmp["nmapApi"] = nmapApi
                dicTmp["mapPer"] = mapPer
                dicTmp["nmapPer"] = nmapPer
                dicTmp["mapRate"] = rate
                retMapData.append(dicTmp)
                if rate == 1:  # 这些是完全特征匹配的
                    fullNode.append(ans['nodeID'])
                # 下面是不将permission计算在匹配率里面的
                # if len(kgApiList)>0:
                #     rate2 = apiMapCount / len(kgApiList)
                #     if rate2 == 1:
                #         fullNode.append(ans['nodeID'])
                # else:
                #     rate2 = perMapCount / len(kgPerList)
                #     if rate2 == 1:
                #         fullNode.append(ans['nodeID'])

            # 去重和排序
            order = list(fullNode)
            fullNode = list(set(fullNode))
            fullNode.sort(key=order.index)
            for node in fullNode:
                fullMapNodeStatistic.append(node)

            allMapNum = len(kgList)
            # 计算部分特征匹配的节点覆盖率
            partMapNum = len(partNode)
            partMapRate = partMapNum / allMapNum
            retJson2 = str(round(partMapRate, 4) * 100) + '%'
            ret2 = '部分特征映射的节点覆盖率(部分映射节点数/KG节点总数)：' + retJson2  # 以70.34%的形式输出
            # 计算完全特征匹配的节点覆盖率
            fullMapNum = len(fullNode)
            if partMapNum > 0:
                fullMapRate = fullMapNum / allMapNum
                fullMapRatePlus = fullMapNum / partMapNum
            else:
                fullMapRate = 0
                fullMapRatePlus = 0
            retJson3 = str(round(fullMapRate, 4) * 100) + '%'
            retJson4 = str(round(fullMapRatePlus, 4) * 100) + '%'
            retJson5 = fullNode
            ret3 = '完全特征映射的节点覆盖率(完全映射节点数/KG节点总数)：' + retJson3  # 以70.34%的形式输出
            ret4 = '完全特征映射的节点覆盖率(完全映射节点数/映射节点数)：' + retJson4
            report.write(ret2 + '\n')
            report.write(ret3 + '\n')
            report.write(ret4 + '\n')
            report.write("完全匹配上的节点:" + ','.join(str(i) for i in fullNode) + '\n')
            # 输出对应语义
            report.write("对应的语义如下:\n")
            for i in fullNode:
                ans = models.augmentNodeIn.objects.get(id=int(i))
                semantic = ans.actionName
                report.write(str(i) + ": " + semantic + '\n')
            with open(report_log, 'a', encoding='utf-8', newline="") as f:
                f.write('*********' + str(file_id) + '*********\n')
                f.write('Apk name: ' + apk_name + '\n')
                malicious = []
                promalicious = []
                general = []
                for i in fullNode:
                    ans = models.augmentNodeIn.objects.get(id=int(i))
                    mark = ans.mark
                    semantic = ans.actionName
                    if mark == '2':
                        malicious.append('(' + mark + ")" + semantic + '\n')
                    elif mark == '1':
                        promalicious.append('(' + mark + ")" + semantic + '\n')
                    else:
                        general.append('(' + mark + ")" + semantic + '\n')
                if len(malicious) > 0:
                    for i in malicious:
                        f.write(i)
                    f.write('------\n')
                if len(promalicious) > 0:
                    for i in promalicious:
                        f.write(i)
                    f.write('------\n')
                if len(general) > 0:
                    for i in general:
                        f.write(i)
                f.write('******************\n\n')

            print('路径匹配...')
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
            tmp = list()  # 暂时存放一条路径
            # print('fullNodeIdList：', fullNodeIdList)
            for nodeId in fullNodeIdList:
                # 1）访问数据库，查看该列表是否有图谱中的该节点的邻节点
                ans = models.augmentRelIn.objects.filter(sourceID=nodeId)
                if ans:
                    if len(tmp) == 0 or tmp[-1] != nodeId:  # 避免重复加入相同节点
                        tmp.append(nodeId)  # 加入源节点
                    ans = list(ans)
                    for one in ans:
                        # 2）如果有邻节点，判断邻节点是否也存在于APK的匹配节点列表中
                        if one.targetID in fullNodeIdList:
                            # 2.1)如果存在，则将该邻节点加入到路径列表中
                            # print('tmp:', tmp)
                            # print("匹配上的路径节点为：", str(nodeId) + "->" + str(one.targetID))
                            tmp.append(one.targetID)
                            # print('tmp list:', tmp)
                            if len(tmp) > 1:
                                pathList.append(tmp)
                                pathMapStatistic.append(tmp)
                                tmp = tmp[0:-1]
                                continue
                        else:
                            # 2.2)如果没有则跳过（因为一般来说不存在这种情况）
                            # print("有图谱上的邻节点但是邻节点不存在APK的匹配节点列表中")
                            continue
                else:
                    # 3）如果没有邻节点，则该节点是单独节点，记录下该节点（不一定，还应该判断它不是某个节点的target node）
                    # print("该节点为单独节点：",nodeId)
                    isolatedNode.append(nodeId)
                tmp = []
            isolatedNode = list(set(isolatedNode))
            # 下面的print为调试信息
            # print("pathList:", pathList)
            # print("isolatedNode:", isolatedNode)
            # 连接路径
            pathList = joint_path(pathList)
            match_report_ans.append({'apk_name': apk_name, 'match_path': str(pathList), 'perfect_match': str(fullNode)})
            report.write("基于完全匹配节点的匹配路径:" + ';'.join(str(i) for i in pathList) + '\n\n\n')

            with open(match_report, 'w', encoding='utf-8', newline="") as f:
                for one in match_report_ans:
                    f.write(json.dumps(one, indent=4, ensure_ascii=False))
                    f.write(';')
    # ******* 返回图谱的统计信息 *******
    allMapNum = len(kgList)
    partMapNodeStatisticCopy = partMapNodeStatistic.copy()
    fullMapNodeStatisticCopy = fullMapNodeStatistic.copy()
    featureMapStatisticCopy = featureMapStatistic.copy()
    statistics1 = numberCount(partMapNodeStatistic)
    statistics2 = numberCount(fullMapNodeStatistic)
    statistics1 = dict_trans_list(statistics1, allMapNum)[0]
    statistics2 = dict_trans_list(statistics2, allMapNum)[0]
    statistics3 = numberCount(featureMapStatisticCopy)
    ret9 = "KG上被匹配的特征及次数（name-count）：" + json.dumps(statistics3)
    ret5 = "KG上被部分匹配的节点及次数：" + json.dumps(statistics1)
    # fullMapNodeStatistic.sort()
    # statistics2 = sorted(statistics2.items(), key=lambda item: item[0])
    ret6 = "KG上被完全匹配的节点及次数：" + json.dumps(statistics2)
    partMapAllApkRate = len(list(set(partMapNodeStatisticCopy))) / len(kgList)
    ret7 = "KG上被部分匹配的节点覆盖率(部分匹配节点数/KG节点总数)：" + str(round(partMapAllApkRate, 4) * 100) + '%'
    fullMapAllApkRate = len(list(set(fullMapNodeStatisticCopy))) / len(kgList)
    ret8 = "KG上被完全匹配的节点覆盖率(完全匹配节点数/KG节点总数)：" + str(round(fullMapAllApkRate, 4) * 100) + '%'
    ret10 = "KG上的路径被匹配情况：" + str(pathMapStatistic)

    with open(report_path, "a", encoding='utf-8') as outfile:  # 这种方法会自动关闭文件
        outfile.write("\n\n****************** KG Statistics ******************\n")
        outfile.write(ret9 + '\n')
        # outfile.write(ret11 + '\n')
        outfile.write(ret5 + '\n')
        outfile.write(ret6 + '\n')
        outfile.write(ret7 + '\n')
        outfile.write(ret8 + '\n')
        outfile.write(ret10 + '\n')


# test()

def static_analysis():
    """生成样本的cg文件，方便静态分析"""
    sample_apks_folder_path = '/media/wuyang/WD_BLACK/AndroidMalware/malware_test_genome'
    files = glob.glob(sample_apks_folder_path + '/*.apk')
    # 依次读取每一个APK
    for f in files:  # f形如D:/input/apk01.apk
        # 生成APK的特征文件，如果文件存在则不另外生成
        filename = os.path.split(f)[1]  # 文件的名称(带后缀)
        apk_name = filename.split('.')[0]  # 文件名（不带后缀）
        if os.path.exists('../detect/outputCG/' + apk_name + '.txt'):
            print('CG文件已存在:', apk_name)
            continue
        else:
            gml, apk_name = generate_cg(f)  # 输入apk，生成cg
            gml_txt(gml, apk_name)  # 将cg转化为txt文件


# static_analysis()

def find_nodes(apk_name):
    """
    :function: 根据apk的特征文件找出该apk的所有行为
    :apk_name, app的名字
    :return     match_node_rel 匹配上的节点列表，节点可能有重复
                match_node_sin 匹配上了哪些节点，节点没有重复
    """
    global kg
    global kg_apis
    feature_data = do_feature_file_v1(apk_name)
    data = feature_data.split("entrypoint node id:")
    permissions = data[0:1][0].strip('\n').split('\n')  # 该api申请的所有权限
    # print(permissions)
    perlist = []
    match_node_rel = []
    match_node_sin = []

    # 0. 根据permission name找到对应的id
    for per in permissions:
        try:
            id = models.augmentPerIn.objects.get(perName=per).perID
            if id not in perlist:
                perlist.append(id)
        except:
            print('该permission无法找到：', per)
    # print('***permission***')
    # print(perlist)

    for one in data[1:]:
        # print(one)
        apis = one.strip('\n').split('\n')[1:]
        apilist = []  # 当前集合的api list
        candidates = []  # 可能的节点
        # 1. 根据api name找到对应api id，需要注意的是考虑api sdk和api similar
        for api in apis:
            if api in kg_apis:
                pass
            else:
                api = api_sdk_sim(api)
            try:
                id = models.augmentAPiIn.objects.get(apiName=api).apiID
                apilist.append(id)
            except:
                # print('api不存在：',api)
                pass

        # 2. 和图谱上的api list求交集，确定候选节点
        for node in kg:
            tmp=apilist
            node_apiList = node['apiList']
            node_perList = node['perList']
            inset_api = list(set(node_apiList).intersection(set(tmp)))
            inset_per = list(set(node_perList).intersection(set(perlist)))
            inset_api.sort()
            inset_per.sort()
            node_apiList.sort()
            node_perList.sort()
            if eq(inset_api, node_apiList) and eq(inset_per, node_perList):
                candidates.append(node)
                # 避免API复用
                for a in inset_api:
                    apilist.remove(a)
                # break

        # 3. 确定最终匹配上的节点
        if len(candidates) > 0:
            for one in candidates:
                match_node_rel.append(one)
                if one not in match_node_sin:
                    match_node_sin.append(one)
        else:
            # 没有和该特征集匹配的节点，直接跳出本次循环
            continue

    # 处理输出的行为
    i = 0  # 从类似[1,2,2,3,3,3,4,1]转变为[1,2,3,4,1]
    while i < len(match_node_rel) - 1:
        if match_node_rel[i] == match_node_rel[i + 1]:
            del match_node_rel[i]
        else:
            i = i + 1
    # for one in match_node_sin:
    #     if one['mark']=='2':
    #         print(one)

    return match_node_rel, match_node_sin


def str_list(s):
    """
    将节点的perlist(数据类型str)和apilist(数据类型str)转化为相应的list(数据类型int)
    s: 带处理的字符串
    """
    ret = []
    if len(s) > 0 and s != '':
        s = s.replace(' ', '')
        if s.find(',') == -1:
            ret.append(int(s))
        else:
            tmp = s.split(',')
            for one in tmp:
                ret.append(int(one))

    return ret


def api_sdk_sim(api_name):
    """
    考虑到api版本更新和相似的api
    :param api_name 传入api的name，将这个api映射为现有节点中存储的api
    :return 返回这个api对应节点上的api的name
    """
    ret = api_name
    try:
        ans = models.augmentAPiIn.objects.get(apiName=api_name)
        if ans.addList != '' or ans.repList != '':
            addList = ans.addList
            repList = ans.repList
            # print('addList：', addList)
            # print('repList：', repList)
            if addList != '':
                add_obj = ApiSim.objects.get(id=int(addList))
                add_apis = add_obj.list
                add_apis = add_apis.split(',')
                for api in add_apis:
                    api = api.replace(' ', '')
                    if api in str(kg_apis):
                        # print('新增 by sim：',api)
                        ret = api
                        break
            if repList != '':
                rep_obj = ApiSDK.objects.get(id=int(repList))
                rep_apis = rep_obj.list
                rep_apis = rep_apis.split(',')
                for api in rep_apis:
                    api = api.replace(' ', '')
                    if api in str(kg_apis):
                        # print('新增 by sdk：', api)
                        ret = api
                        break
        else:
            # print('not find0：', )
            pass
    except:
        # print('not find：', tmp)
        pass

    return ret


def get_all_list():
    """
    获取知识图谱上所有节点对应的api list和per list
    """
    model = list(models.augmentNodeIn.objects.values())
    ret = []
    for node in model:
        json = {}
        nodeID = node['nodeID']
        actionName = node['actionName']
        mark = node['mark']
        perlist = str_list(node['perList'])
        apilist = str_list(node['apiList'])

        json['nodeID'] = nodeID
        json['actionName'] = actionName
        json['mark'] = mark
        json['perList'] = perlist
        json['apiList'] = apilist
        ret.append(json)

    return ret


def find_relation(match_node_rel):
    """
    根据匹配出的节点，找出这些节点可以匹配上的路径
    """
    match_node = match_node_rel
    ret_path = []
    fullNodeIdList = []  # 存储节点的ID
    for node in match_node:
        fullNodeIdList.append(node['nodeID'])
    # 遍历访问该APK的部分特征匹配节点列表
    # fullNodeIdList = fullNode[:]  # 复制列表，其中存储的是ID
    tmp = list()  # 暂时存放一条路径

    for node in match_node:
        nodeId = node['nodeID']
        # 1）访问数据库，查看该列表是否有图谱中的该节点的邻节点
        try:
            ans = models.augmentRelIn.objects.filter(sourceID=nodeId)
            if ans:
                if len(tmp) == 0 or tmp[-1] != nodeId:  # 避免重复加入相同节点
                    tmp.append(nodeId)  # 加入源节点
                ans = list(ans)
                for one in ans:
                    # 2）如果有邻节点，判断邻节点是否也存在于APK的匹配节点列表中
                    if one.targetID in fullNodeIdList:
                        # 2.1)如果存在，则将该邻节点加入到路径列表中
                        # print('tmp:', tmp)
                        # print("匹配上的路径节点为：", str(nodeId) + "->" + str(one.targetID))
                        tmp.append(one.targetID)
                        fullNodeIdList.remove(nodeId)
                        fullNodeIdList.remove(one.targetID)
                        # print('tmp list:', tmp)
                        if len(tmp) > 1:
                            ret_path.append(tmp)
                            tmp = tmp[0:-1]
                            continue
                    else:
                        # 2.2)如果没有则跳过（因为一般来说不存在这种情况）
                        # print("有图谱上的邻节点但是邻节点不存在APK的匹配节点列表中")
                        continue
        except:
            pass
        tmp = []

    # 匹配出来的路径去重
    ret_path2 = []
    for one in ret_path:
        if one not in ret_path2:
            ret_path2.append(one)

    # 查找对应的语义
    ret_path = []  # 全部的路径
    # 返回带和不带malicious node的路径
    ret_path_malicious = []
    ret_path_others = []
    for nodelist in ret_path2:
        flag = 0  # 判断当前路径中是否有恶意节点，有为1，没有为0
        semantics = []
        for node in nodelist:  # 寻找对应的语义
            ans = models.augmentNodeIn.objects.get(nodeID=node)
            if ans.mark == '2':
                flag = 1
            semantic = ans.actionName
            semantics.append(semantic)
        ret_path.append({'path': nodelist, 'semantics': semantics})

        if flag == 0:  # 返回不带恶意节点的路径
            ret_path_others.append({'path': nodelist, 'semantics': semantics})
        elif flag == 1:  # 返回带恶意节点的路径
            ret_path_malicious.append({'path': nodelist, 'semantics': semantics})
        else:
            print('what error')

    return ret_path, ret_path_malicious, ret_path_others


def get_malicious_nodes():
    """
    获取知识图谱上那些mark为2的节点
    """
    ret = []
    model = models.augmentNodeIn.objects.values()
    model = list(model)
    for node in model:
        if node['mark'] == '2':
            ret.append(node['nodeID'])
    return ret


def split_m_o(match_node_sin):
    """
    将节点分为恶意的和其他的
    """
    ret_malicious = []
    ret_benign = []
    for node in match_node_sin:
        if node['mark'] == '2':
            ret_malicious.append(node)
        else:
            ret_benign.append(node)

    return ret_malicious, ret_benign


def extract_id(node_list):
    """
    从字典节点的列表中提取出节点的id list
    """
    ret = []
    for one in node_list:
        if one['nodeID'] not in ret:
            ret.append(one['nodeID'])

    return ret


def output(match_node_sin, match_path_malicious):
    """
    输出最终检测报告中应该有的行为。
    node_malicious 匹配出的恶意节点+其他节点
    match_path 匹配出的路径（至少带一个恶意节点的）
    """
    ret = []

    node_mlicious, node_benign = split_m_o(match_node_sin)
    node_w = extract_id(match_node_sin)
    node_m = extract_id(node_mlicious)
    node_b = extract_id(node_benign)
    path_nodes = []  # 恶意路径中的节点
    for one in match_path_malicious:
        for i in one['path']:
            if i not in path_nodes:
                path_nodes.append(i)
    # 求两个集合的交集
    inset_nodes = list(set(node_w).intersection(path_nodes))
    # 求两个集合的并集
    union_nodes = list(set(inset_nodes).union(node_m))

    for one in union_nodes:
        for node in match_node_sin:
            if one == node['nodeID']:
                ret.append(node)
                continue

    return ret


def reason(match_path,apk_name):
    """
    根据匹配的路径，推理出现有检测结果中没有的行为
    """
    renew_path=[]   # 推理后的路径
    # 1. 找到路径的首尾节点
    for one in match_path:
        path = one['path']
        source = path[0]
        target = path[-1]
        source_head_candidates = []  # 当前路径首节点的source node
        target_tail_candidates = []  # 当前路径尾节点的target node
        try:
            source_head_rel = models.augmentRelIn.objects.filter(targetID=source)
            if source_head_rel:
                for obj in source_head_rel:
                    id = obj.sourceID
                    # 查找相应的节点
                    try:
                        ans = models.augmentNodeIn.objects.get(nodeID=id)
                        source_head_candidates.append(
                            {'nodeID': ans.nodeID, 'actionName': ans.actionName, 'mark': ans.mark,
                             'perList': str_list(ans.perList), 'apiList': str_list(ans.apiList)})
                    except:
                        print('reason 没有查找到该首节点')
        except:
            pass
        try:
            target_tail_rel = models.augmentRelIn.objects.filter(sourceID=target)
            if target_tail_rel:
                for obj in target_tail_rel:
                    id = obj.targetID
                    # 查找相应的节点
                    try:
                        ans = models.augmentNodeIn.objects.get(nodeID=id)
                        target_tail_candidates.append(
                            {'nodeID': ans.nodeID, 'actionName': ans.actionName, 'mark': ans.mark,
                             'perList': str_list(ans.perList), 'apiList': str_list(ans.apiList)})
                    except:
                        print('reason 没有查找到该尾节点')
        except:
            pass

        # 2. 查看他们首尾节点的特征匹配情况。模糊查询，在整个特征文件中查找，而不是在某个函数中查找
        tmp=path # 存放新的路径的
        # print('source_head_candidate:',source_head_candidates)
        for node in source_head_candidates:
            nodeID=node['nodeID']
            f=compute_f(apk_name,node)
            # 设置阈值，超过则加入到原有路径中
            if f>=0.5:
                tmp.insert(0,nodeID)
        for node in target_tail_candidates:
            nodeID=node['nodeID']
            f=compute_f(apk_name,node)
            if f>=0.5:
                tmp.append(nodeID)
        renew_path.append({'path':tmp,'semantics':one['semantics']})

    return renew_path


def compute_f(apk_name, dict_node):
    """
    apk_name 用于定位特征文件
    dict_node 一个节点的字典形式，如 {'nodeID': ans.nodeID, 'actionName': ans.actionName, 'mark': ans.mark,
                             'perList': perList, 'apiList': apiList})
    返回该节点的特征匹配率
    """
    apilist=dict_node['apiList']
    perlist=dict_node['perList']

    feature_data = do_feature_file_v1(apk_name)
    api_str_list=query_kg_list(apilist,1)
    per_str_list=query_kg_list(perlist,0)

    # 查找匹配上的特征并计数
    api_count=0
    per_count=0
    for api in api_str_list:
        pattern=re.compile(api,re.S)
        ans=pattern.findall(feature_data)
        print('api ans:',ans[0])
        if ans:
            api_count=api_count+1
    for per in per_str_list:
        pattern = re.compile(per, re.S)
        ans = pattern.findall(feature_data)
        print('per ans:', ans[0])
        if pattern:
            per_count = per_count + 1

    # 计算特征覆盖率
    f=(api_count+per_count)/(len(apilist)+len(perlist))

    return f


def query_kg_list(int_list,flag):
    """
    根据传入的int id list和flag去数据库中查找相应的string name list
    """
    # 查询permission
    ret=[]
    if flag==0 and len(int_list)>0:
        for one in int_list:
            try:
                ans=models.augmentPerIn.objects.get(perID=one).perName
                ans=ans.strip(' ').replace(' ','') # 防止有多余的空格
            except:
                print('该permission无法被找到：',one)

    # 查询apis
    if flag==1 and len(int_list)>0:
        for one in int_list:
            try:
                ans=models.augmentAPiIn.objects.get(apiID=one).apiName
                ans=ans.strip(' ').replace(' ','') # 防止有多余的空格
            except:
                print('该api无法被找到：',one)

    return ret


# global kg,malicious_nodes
# kg=get_all_list()
# malicious_nodes=get_malicious_nodes()
# for one in kg[0:25]:
#     print(one)
# m1,m2=find_nodes('ClickrAd')
# p1,p2,p3=find_relation(m1)
# for one in p2:
#     print(one)
#
# print('**********')
# for one in p3:
#     print(one)

# find_nodes('GoldenCup')

def XMalChain_v1():
    """
    使用扩充后的知识图谱来匹配APK
    """
    # 在写入映射失败的特征前，先清空txt文件，防止记录重复
    with open(report_log, "a", encoding='utf-8') as f:
        f.truncate(0)
    with open(match_report, "a", encoding='utf-8') as f:
        f.truncate(0)
    global kg, malicious_nodes
    global kg_apis, kg_permissions, kg_features, apis_from_test
    kg_permissions, kg_apis, kg_features = get_pers_apis_after_augment()  # 初始化数据：get all permissions&apis from kg/database
    apis_from_test = get_apis_from_test_after_augment()
    kg = get_all_list()
    malicious_nodes = get_malicious_nodes()

    # 1、生成98个样本apk的特征文件
    sample_apks_folder_path = '/home/wuyang/Experiments/Datas/malwares/sample_apk_100'
    # sample_apks_folder_path = '/home/wuyang/Experiments/Datas/malwares/googlePlay/apk_sample'
    # sample_apks_folder_path='/home/wuyang/Experiments/Datas/malwares/part_androzoo/androzoo_apk_100'
    # sample_apks_folder_path = '/home/wuyang/Experiments/Datas/tmpApk/protest'
    # sample_apks_folder_path='/media/wuyang/WD_BLACK/AndroidMalware/xmal_test'

    match_report_ans = []

    # 为了避免Django项目内的文件过多，生成CG文件和特征文件前先将文件夹清空
    # shutil.rmtree('../detect/outputCG')  # 删除该文件夹以及该文件夹下的所有文件
    # shutil.rmtree('../detect/output_features')
    # os.mkdir('../detect/outputCG')  # 创建新的文件夹
    # os.mkdir('../detect/output_features')

    # ********** 二、依次匹配每一个文件 *************
    with open(report_log, "a", encoding='utf-8') as report:
        # 读取所有的APK
        global flag
        files = glob.glob(sample_apks_folder_path + '/*.apk')
        file_id = 0

        # report.write("******************\n " + '计算节点匹配率时，去掉permission' + " ******************\n\n")

        # 依次读取每一个APK
        for f in files:  # f形如D:/input/apk01.apk
            file_id = file_id + 1
            flag = 0
            # 生成APK的特征文件，如果文件存在则不另外生成
            filename = os.path.split(f)[1]  # 文件的名称(带后缀)
            apk_name = filename.split('.')[0]  # 文件名（不带后缀）

            # 写入report
            report.write("****************** APK " + str(file_id) + " ******************\n")  # 记录当前APK的名字
            report.write("Apk name：" + apk_name + '\n')  # 记录当前APK的名字
            print("******************" + str(file_id) + " ******************")
            print("Apk name: " + apk_name + '')

            if os.path.exists('../detect/output_features/' + apk_name + '_features.txt'):
                pass
            else:
                if os.path.exists('../detect/outputCG/' + apk_name + '.txt'):
                    pass
                else:
                    print('生成CG文件...')
                    gml, apk_name = generate_cg(f)  # 输入apk，生成cg
                    gml_txt(gml, apk_name)  # 将cg转化为txt文件
                print('生成特征文件...')
                extract_features_plus(apk_name, f)  # 提取特征,生成特征文件

            print('节点匹配...')
            # *******计算某个APK覆盖的节点 *******
            match_node_rel, match_report_sin = find_nodes(apk_name)
            report.write("\n")
            malicious = []
            others = []
            global statics_behavior
            for node in match_report_sin:
                if node['mark'] == '2':
                    malicious.append(node['actionName'] + '\n')
                    statics_behavior.append(node['actionName'])
                else:
                    others.append(node['actionName'] + '\n')
            if len(malicious) > 0:
                report.write('---Malicious---\n')
                for i in malicious:
                    report.write(i)
                report.write('\n')
            if len(others) > 0:
                report.write('---Others---\n')
                for i in others:
                    report.write(i)
                report.write('\n')

            print('路径匹配...')
            # ************3.路径匹配 ***********
            path_all, path_m, path_o = find_relation(match_node_rel)
            output_nodes = output(match_report_sin, path_m)
            report.write('\n---Malicious Path---\n')
            for one in path_m:
                path = one['path']
                semantics = one['semantics']
                report.write('->'.join(str(i) for i in path) + ': ' + '->'.join(str(i) for i in semantics) + '\n')
            report.write('\n---Others Path---\n')
            for one in path_o:
                path = one['path']
                semantics = one['semantics']
                report.write('->'.join(str(i) for i in path) + ': ' + '->'.join(str(i) for i in semantics) + '\n')

            print('输出最终节点与推理...')
            report.write('\n\n---Final Output---\n')
            for one in output_nodes:
                report.write(one['actionName'] + '\n')

            renew_path=reason(path_m,apk_name)
            report.write('\n---Reasoning Path---\n')
            for one in renew_path:
                path = one['path']
                semantics = one['semantics']
                report.write('->'.join(str(i) for i in path) + ': ' + '->'.join(str(i) for i in semantics) + '\n')
            report.write('******************\n\n')
            print('---END---')

            # 用于扩充数据集
            # match_report_ans = []
            # fullNode = []
            # pathList = []
            # for one in match_report_sin:
            #     fullNode.append(one['nodeID'])
            # for one in path_all:
            #     # print(one)
            #     if one['path'] not in pathList:
            #         pathList.append(one['path'])
            # match_report_ans.append({'apk_name': apk_name, 'match_path': str(pathList), 'perfect_match': str(fullNode)})
            #
            # with open(match_report, 'a', encoding='utf-8', newline="") as f:
            #     for one in match_report_ans:
            #         f.write(json.dumps(one, indent=4, ensure_ascii=False))
            #         f.write(';')


XMalChain_v1()

print('startc:',statics_behavior[0:3])
arr = statics_behavior


# arr=Counter(lists)
# print(arr)
def counter(arr):
    return Counter(arr)

ans=counter(arr)
print('*********')
print(ans)