import re
import string
import glob
import os
import sys
import json
import shutil
import datetime
import time
import codecs  # 将ansi编码的文件转为utf-8编码的文件

from django.http import HttpResponse
from common import models

# from androguard.core.bytecodes import apk
# from androguard.core.bytecodes import dvm
# from androguard.core.analysis.analysis import Analysis
from androguard.misc import AnalyzeAPK
from androguard.core.androconf import load_api_specific_resource_module
from manager.views import dict_trans_list
from common.models import ApiTest, PerTest, KgBackup, relBackup, ApiSim, ApiSDK, augmenTestNode, augmenTestRel, \
    augmenTestPer, augmenTestAPi
from exper1.augment import joint_path

kg_permissions = []  # all permissions in kg/database
kg_apis = []  # all apis in kg/database
apis_from_test = []  # Apitest中的apis
kg_features = []  # all features(permissions+apis) in kg

# Create your views here.
# testApk_path = 'D:\\testAPK0.txt'   # 输入是apk的特征文件
testApk_path = '/home/wuyang/Experiments/Datas/tmpdata/testAPK.txt'
apkfile = './10.apk'
apiFeature_path = ''
perFeature_path = 'verify/input/perFeature.txt'  # 单独存放kg的permission特征
apiFeature_path = 'verify/input/apiFeature.txt'  # 单独存放kg的api特征
kgFeatures_path = 'verify/input/kgFeatures.txt'  # 存放kg的所有特征
# report_path = "/home/wuyang/Experiments/Datas/output/reportTest.txt"  # 输出是匹配结果
# report_path = '/home/wuyang/Experiments/Datas/output/report_mwep/report1.txt'
report_path = 'detect/output/report1.txt'
report_path_augment = 'detect/output/report1_augment.txt'
match_report_path = 'detect/output/match_report1.txt'
match_report_path_augment = 'detect/output/match_report1_augment.txt'
input_path = '/home/wuyang/Experiments/Datas/tmpApk'

# flag = 0
fileID = 0


# 在写入映射失败的特征前，先清空txt文件，防止记录重复
# with open("detect/output/nmapFetures.txt", "a", encoding='utf-8') as nmapFeatureFile:
#     nmapFeatureFile.truncate(0)


def test(request):
    # 在写入映射报告前，先清空txt文件，防止报告重复
    # with open(report_path, "a", encoding='utf-8') as report:
    #     report.truncate(0)
    # with open(report_path_augment, "a", encoding='utf-8') as report:
    #     report.truncate(0)

    # 在写入映射失败的特征前，先清空txt文件，防止记录重复
    with open("detect/output/nmapFetures.txt", "a", encoding='utf-8') as nmapFeatureFile:
        nmapFeatureFile.truncate(0)

    # 在写入api-permission的映射前，先清空txt文件，防止记录重复
    # with open("detect/output/api_per.txt", "a", encoding='utf-8') as output:
    #     output.truncate(0)
    # *******检测apk*******
    # ret = kg_map_apk('detect/output_features/10_features.txt', apk_name)
    # ********************

    # *******验证KG，构建从原始样本apk到KG的映射*******
    # apk_map_kg_main()
    apk_map_kg_main_after_augment()
    # ********************************************

    # get_apis_from_wkg()

    return HttpResponse('exper1 test', status=200)


def get_pers_apis():
    """
    :return: :list: all permissions in kg
            :list: all apis in kg
    """
    # per_list = PerTest.objects.values('perName')
    # # 因为ApiTest中存储了所有的api，包括功能相似的api和根据SDK Level发生更新/替换的API，故在从CG-特征文件的过程中，是考虑了SDK Level的
    # api_list = ApiTest.objects.values('apiName')
    # # 此时的per_list api_list是由字典组成的数组，因此进行下述处理
    # per_list = dict_list(per_list, 'perName')
    # api_list = dict_list(api_list, 'apiName')

    # kg_list = list(per_list)  # 直接复制一份数据
    # # permissions + apis = kg 中的所有特征
    # for one in api_list:
    #     kg_list.append(one)
    #
    # return per_list, api_list, kg_list

    api_list = get_apis_from_wkg()
    per_list = get_pers_from_wkg()
    kg_list = list(per_list)  # 直接复制一份数据
    # permissions + apis = kg 中的所有特征
    for one in api_list:
        kg_list.append(one)

    return per_list, api_list, kg_list


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


def get_apis_from_wkg():
    """
    获取那些已经被确立为图谱节点特征的apis
    """
    api_list = augmenTestNode.objects.values('apiList')
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
    # print('api_num:',api_num)
    # print('api_num1:', len(api_num))
    for one in api_num:
        ans = augmenTestAPi.objects.get(id=int(one))
        api = ans.apiName.replace(' ', '')
        apis_list.append(api)
    # print('apis_list:', apis_list)
    # print('apis_list:', len(apis_list))
    return apis_list


def get_apis_from_wkg_after_augment():
    """
    获取那些已经被确立为图谱节点特征的apis
    """
    api_list = models.augmenTestNode.objects.values('apiList')
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
            ans = models.augmenTestAPi.objects.get(id=int(one))
            api = ans.apiName.replace(' ', '')
            apis_list.append(api)
        except:
            print('augmenTestAPi matching query does not exist:', one)
    return apis_list


def get_pers_from_wkg():
    """
    获取那些已经被确立为图谱节点特征的permissions
    """
    per_list = augmenTestNode.objects.values('perList')
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
        ans = PerTest.objects.get(id=int(one))
        api = ans.perName.replace(' ', '')
        pers_list.append(api)
    return pers_list


def get_pers_from_wkg_after_augment():
    """
    获取那些已经被确立为图谱节点特征的permissions
    """
    per_list = models.augmenTestNode.objects.values('perList')
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
            ans = models.augmenTestPer.objects.get(id=int(one))
            per = ans.perName.replace(' ', '')
            pers_list.append(per)
        except:
            print('augmenTestPer matching query does not exist:', one)
    return pers_list


def get_apis_from_test():
    api_list = augmenTestAPi.objects.values('apiName')
    # 此时的per_list api_list是由字典组成的数组，因此进行下述处理
    api_list = dict_list(api_list, 'apiName')
    return api_list


def get_apis_from_test_after_augment():
    api_list = models.augmenTestAPi.objects.values('apiName')
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
        # if _flag == 0:  # 权限的QuerySet
        #     for i in demo_list:
        #         ret_list.append(i['perName'])
        # elif _flag == 1:
        #     for i in demo_list:
        #         ret_list.append(i['apiName'])
        # elif _flag == 2:
        #     for i in demo_list:
        #         ret_list.append(i['actionName'])
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

    if os.path.exists('detect/outputCG/' + apk_name + '.gml'):
        print('cg的gml文件已存在')
        file = os.path.join('detect/outputCG/', apk_name + '.gml')  # 存放apk的特征文件
        return file, apk_name
    else:
        # shutil.rmtree('detect/outputCG')  # 删除该文件夹以及该文件夹下的所有文件
        # os.mkdir('detect/outputCG')  # 创建新的文件夹
        os.system('androguard cg ' + apk + ' -o detect/outputCG/' + apk_name + '.gml')
        # os.system('androguard cg ' + apk + ' -o detect/outputCG/' + apk_name + '.gexf')
        # file = glob.glob('detect/outputCG/' + apk_name + '.gml')
        file = os.path.join('detect/outputCG/', apk_name + '.gml')  # 存放apk的特征文件
        return file, apk_name


def gml_txt(gml_file, apk_name):
    """
    :param gml_file: a .gml file generated by generate_cg，传入的gml文件路径是 detect/outputCG/.gml
    :param apk_name:apk's name
    :return: a .txt file generated from .gml file
    """
    # new_file = os.path.join('detect/outputCG/', apk_name + '.txt')
    print('apk_name:', apk_name)
    print('aml file:', gml_file)
    if os.path.exists('detect/outputCG/'+apk_name + '.gml'):
        print('修改gml名称')
        os.rename('detect/outputCG/'+apk_name + '.gml', 'detect/outputCG/'+apk_name + '.txt')
        # file = glob.glob('detect/outputCG/' + apk_name + '.txt')
        print('xixi')
        file = os.path.join('detect/outputCG/', apk_name + '.txt')  # 存放apk的特征文件
        return file


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


def extract_features(txt, apk_name, apk_path):
    """
    :param txt:a .txt file generated from .gml
    :return feature_txt: a .txt file consists of key apis & permissions of an app
    """
    start_time = time.time()

    a, d, dx = AnalyzeAPK(apk_path)
    permissions = a.get_permissions()

    feature_filename = os.path.join('detect/output_features/', apk_name + '_features.txt')  # 存放apk的特征文件
    feature_file = open(feature_filename, 'w', encoding='utf-8')
    # **********Write Information Belows*************
    # 1. write permissions
    # feature_file.write('perStart' + '\n')
    for per in permissions:
        if per in kg_permissions:
            feature_file.write(per + '\n')
    # feature_file.write('perEnd' + '\n')
    feature_file.write('\n')
    # feature_file.close()

    # 2. write apis through .gml
    data = get_data(os.path.join('detect/outputCG/', apk_name + '.txt'))
    api_list = list()  # 存放即将写入特征文件的api
    node_list, edge_list = analyse(data)
    global apis_from_test
    # print('apis_from_test:', apis_from_test)

    # sta_apis=[] # 记录已经
    # print('node list', node_list[10:15])
    for node in node_list:
        api_location0 = re.findall('L.*?;->.*?]', node)  # 能在node_list[source]中找到符合正则表达式的字符串，以列表的形式返回
        if api_location0:
            api_list = []
            # print('node:', node)
            source = re.findall('id\s*\d+', node)  # 拿到函数入口，e.g.【‘id 10’】
            source_id = source[0].replace("'", '').split(' ')[1]
            # source_name = re.findall('entrypoint 1', node)
            # if source_name:
            #     print('source name:', source_name)
            #     feature_file.write('entrypoint node id:' + str(source_id) + '\n')
            # print('\nsource id:', source_id)
            # 去edges中查找以source id为起点的节点
            for edge in edge_list:
                source_edges = re.findall('source\s*\d+', edge)
                source_edge_id = source_edges[0].replace("'", '').split(' ')[1]
                if source_edge_id == source_id:
                    target = re.findall('target\s*\d+', edge)  # 结果可能有多个
                    target_id = target[0].replace("'", '').split(' ')[1]
                    # print('target id:', target_id)
                    # 去node list查找node
                    api_location = re.findall('(L.*?;->.*?)"', node_list[int(target_id)])  # 不带[]的有可能是api
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
            if len(api_list) > 0:
                feature_file.write('entrypoint node id:' + str(source_id) + '\n')
            for api in api_list:
                # print('api:', api)
                feature_file.write(api + '\n')
            # feature_file.write("apiEnd" + '\n')
    feature_file.close()

    end_time = time.time()
    print('特征提取时间为：', str(end_time - start_time))

    # 存放apk中有映射关系的api-per对
    # api_per_name=os.path.join('detect/output_features/', apk_name + '_api_per.txt')
    # api_per = open('detect/output/api_per.txt', 'a', encoding='utf-8')
    # perm_map = load_api_specific_resource_module('api_permission_mappings')
    # for meth_analysis in dx.get_methods():
    #     meth = meth_analysis.get_method()
    #     name = meth.get_class_name() + "-" + meth.get_name() + "-" + str(meth.get_descriptor())
    #     for k, v in perm_map.items():
    #         if name == k:
    #             result = str(meth) + ' : ' + str(v)
    #             api_per.write(result + '\n')
    # api_per.close()

    # return "hello"


def extract_features_plus(txt, apk_name, apk_path):
    """
    :function 在原有的基础上多引入正则表达式，从而节约时间
    :param txt:a .txt file generated from .gml
    :return feature_txt: a .txt file consists of key apis & permissions of an app
    """
    start_time = time.time()

    a, d, dx = AnalyzeAPK(apk_path)
    permissions = a.get_permissions()

    feature_filename = os.path.join('detect/output_features/', apk_name + '_features.txt')  # 存放apk的特征文件
    feature_file = open(feature_filename, 'w', encoding='utf-8')
    # **********Write Information Belows*************
    # 1. write permissions
    for per in permissions:
        if per in kg_permissions:
            feature_file.write(per + '\n')
    feature_file.write('\n')

    # 2. write apis through .gml
    data = get_data(os.path.join('detect/outputCG/', apk_name + '.txt'))
    node_list, edge_list = analyse(data)
    global apis_from_test

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
        if len(api_list) > 0:
            feature_file.write('entrypoint node id:' + str(source_id_str) + '\n')
            for api in api_list:
                feature_file.write(api + '\n')

    feature_file.close()

    end_time = time.time()
    print('特征提取时间为：', str(end_time - start_time))


def database_test():
    ans = augmenTestAPi.objects.count()
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
            # 解压
            # if os.path.splitext(filename)[1] == '.zip':
            #     zip_path = os.path.join(filepath, filename)
            #     print('zip:',zip_path)
            #     os.system('unzip -o ' + zip_path+' -d '+filepath)
            # os.path.splitext():分离文件名与扩展名
            if os.path.splitext(filename)[1] == '.apk':
                # print('apk:', filename)
                old_path = os.path.join(filepath, filename)
                # 复制apk文件到新的目录
                shutil.copy(old_path, dstpath + apk_name + '.apk')


def apk_map_kg_main():
    """
    构建由apk->kg的映射，检验整张图谱的完整程度；
    样本： 构建图谱时的98个apk
    :return
        1) 所有的特征是否都有匹配的APK
        2) 所有的节点是否都有匹配的APK
        3) 所有的路径是否都有匹配的APK
    """
    global kg_apis, kg_permissions, kg_features, apis_from_test
    kg_permissions, kg_apis, kg_features = get_pers_apis()  # 初始化数据：get all permissions&apis from kg/database
    apis_from_test = get_apis_from_test()

    # 1、生成98个样本apk的特征文件
    # sample_apks_folder_path = '/home/wuyang/Experiments/Datas/malwares/sample_apk_100'
    # sample_apks_folder_path = '/home/wuyang/Experiments/Datas/malwares/googlePlay/apk_sample'
    # sample_apks_folder_path='/home/wuyang/Experiments/Datas/malwares/part_androzoo/androzoo_apk_100'
    # sample_apks_folder_path = '/home/wuyang/Experiments/Datas/tmpApk/protest'

    # 扩充数据集
    sample_apks_folder_path = '/media/wuyang/WD_BLACK/AndroidMalware/malware_test'

    match_report_ans = []

    # 为了避免Django项目内的文件过多，生成CG文件和特征文件前先将文件夹清空
    shutil.rmtree('detect/outputCG')  # 删除该文件夹以及该文件夹下的所有文件
    shutil.rmtree('detect/output_features')
    os.mkdir('detect/outputCG')  # 创建新的文件夹
    os.mkdir('detect/output_features')
    fullMapNodeStatistic = []  # 对于所有的APK文件，统计KG上每个节点的映射情况，对应的是完全匹配的情况
    partMapNodeStatistic = []  # 对于所有的APK文件，统计KG上每个节点的映射情况，对应的是部分匹配的情况
    featureMapStatistic = []  # 对于所有的APK文件，统计KG上每个特征的映射情况
    apk_feature_map = []  # 对于每一个apk，映射上的特征/该APK总的特征数。里面存储了所有apk的特征映射情况
    pathMapStatistic = []  # 对于所有的APK文件，统计KG上每条路径的映射情况
    kgModel = models.augmenTestNode.objects.values()
    kgList = list(kgModel)

    # ********** 二、依次匹配每一个文件 *************
    with open(report_path, "a", encoding='utf-8') as report:
        # 读取所有的APK
        global flag
        files = glob.glob(sample_apks_folder_path + '/*.apk')
        # files=os.listdir(sample_apks_folder_path)
        file_id = 0

        time = datetime.datetime.today()
        report.write(
            "******************\n " + "Dataset: " + sample_apks_folder_path + "\n" + str(
                time) + " \n******************\n")
        # report.write("******************\n " + '计算节点匹配率时，去掉permission' + " ******************\n\n")

        # 依次读取每一个APK
        for f in files:  # f形如D:/input/apk01.apk
            print("***********************")
            print("apk:", f)
            file_id = file_id + 1
            flag = 0
            # 生成APK的特征文件，如果文件存在则不另外生成
            gml, apk_name = generate_cg(f)  # 输入apk，生成cg
            txt = gml_txt(gml, apk_name)  # 将cg转化为txt文件
            if os.path.exists('detect/output_features/' + apk_name + '_features.txt'):
                pass
            else:
                extract_features_plus(txt, apk_name, f)  # 提取特征,生成特征文件
            # 写入report
            report.write("****************** APK " + str(file_id) + " ******************\n")  # 记录当前APK的名字
            report.write("文件名：" + apk_name + '\n')  # 记录当前APK的名字
            retJson0 = apk_name
            # 首先读取某个APK的特征文件
            feature_file_path = 'detect/output_features/' + apk_name + '_features.txt'
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
                            ans = augmenTestAPi.objects.get(apiName=tmp)
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
            with open("detect/output/mapFeatures.txt", "a", encoding='utf-8') as mapFeatureFile:
                mapFeatureFile.truncate(0)
            # # 在写入映射失败的特征前，先清空txt文件，防止记录重复
            # with open("detect/output/nmapFetures.txt", "a", encoding='utf-8') as nmapFeatureFile:
            #     nmapFeatureFile.truncate(0)
            # 将映射成功的写入本地文件mapFeatures.txt中，以为节点匹配做准备
            with open("detect/output/mapFeatures.txt", "a", encoding='utf-8') as outfile:  # 这种方法会自动关闭文件
                for one in mapFeatureList:
                    outfile.write(one + '\n')
            with open("detect/output/all_map.txt", "a", encoding='utf-8') as outfile:
                for one in mapFeatureList:
                    outfile.write(one + '\n')
            # 将映射失败的写入本地文件nmapFeatures.txt中
            with open("detect/output/nmapFetures.txt", "a", encoding='utf-8') as outfile:  # 这种方法会自动关闭文件
                for one in nmapFeatureList:
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
            mapFeatures = open("detect/output/mapFeatures.txt", 'r', encoding='utf-8', newline="")
            apiIdList = []  # 记录下匹配成功的api的id
            perIdList = []  # 记录下匹配成功的per的id

            # 记录下匹配到的api的id
            for row in mapFeatures.readlines():
                line = row.strip()
                # 将字符串拆分后然后再再重组，不然可能出现匹配不上的问题
                if line.find(";") != -1:  # 说明处理的是api
                    tmp1 = line.split(';')
                    tmp = ';'.join(tmp1)  # tmp为按顺序出现的api
                    ans = augmenTestAPi.objects.filter(apiName=tmp)
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
            mapFeatures = open("detect/output/mapFeatures.txt", 'r', encoding='utf-8', newline="")

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
                            perIdList.append(one.id)
                    else:
                        pass
                else:
                    continue

            partNode = []  # 匹配上了部分特征的节点，存储着这些节点的id
            fullNode = []  # 完全匹配上的节点，存储着这些节点的id

            # 第1种匹配算法
            # **************根据api来匹配节点**********************

            # pos=0 #起始匹配的位置
            # while pos<len(apiIdList):
            #     record_apis = ''  # 记录已经判断匹配过的api
            #     node_set = []
            #     first_set = []
            #     for apiId in apiIdList[pos:]:
            #         print('record_apis:',record_apis)
            #         record_apis=record_apis+str(apiId)
            #         # 查看和该api有关的节点
            #         for node in kgList:
            #             apiStr = node['apiList']
            #             if apiStr == '':
            #                 continue
            #             elif apiStr.find(str(apiId))!=-1:
            #                 node_set.append(node['id'])
            #         # 如果该api只匹配上了一个节点，处理比较简单
            #         if len(node_set)==1:
            #             # 判断api是否全部满足映射
            #             if apiStr.find(',')==-1 and apiStr in record_apis:  # 只有一个api，则检查permission是否满足映射
            #                 perStr = node['perList']
            #                 if perStr == '' or perStr == ' ':
            #                     record_apis=''
            #                     fullNode.append(node['id'])  # 该节点的特征有且只有一个api，并且该api映射成功
            #                 elif perStr.find(',') != -1:  # permission特征多于1
            #                     per_list = perStr.split(',')
            #                     count = 0
            #                     for one in per_list:
            #                         if one in str(perIdList):
            #                             count = count + 1
            #                     if count == len(per_list):
            #                         record_apis = ''
            #                         fullNode.append(node['id'])
            #                 else:  # permission的数量为1
            #                     if perStr in str(perIdList):
            #                         record_apis = ''
            #                         fullNode.append(node['id'])
            #             elif apiStr.find(',')!=-1:  # 节点有多个api，则需要观察后续的
            #                 api_str_list=api_str_list.split(',')
            #                 count=0
            #                 for one in api_str_list:
            #                     if one in record_apis:
            #                         count=count+1
            #                 if count==len(api_str_list):
            #                     fullNode.append(node['id'])
            #                 pass
            #         else:
            #             # 当当前api匹配上多个节点时，则需要观察下一条api匹配的节点,跳出当前遍历
            #             first_set=node_set.copy()
            #             pos=pos+1
            #             break
            #         pos=pos+1

            # for node in kgList:
            # apiStr = node['apiList']
            # if apiStr == '':
            #     continue
            # else:
            #     if apiStr.find(str(apiId)) != -1:  # 该api在该节点中出现过
            #         partNode.append(node['id'])
            #         if apiStr.find(',') != -1:  # 说明该节点的api特征只有一个api,没有permission
            #             perStr = node['perList']
            #             if perStr == '' or perStr == ' ':
            #                 fullNode.append(node['id'])  # 该节点的特征有且只有一个api，并且该api映射成功
            #             elif perStr.find(',') != -1:  # permission特征多于1
            #                 per_list = perStr.split(',')
            #                 count = 0
            #                 for one in per_list:
            #                     if one in str(perIdList):
            #                         count = count + 1
            #                 if count == len(per_list):
            #                     fullNode.append(node['id'])
            #             else:  # permission的数量为1
            #                 if perStr in str(perIdList):
            #                     fullNode.append(node['id'])

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
                ans = augmenTestNode.objects.get(nodeID=nodeId)
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
                ans = augmenTestRel.objects.filter(sourceID=nodeId)
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

            with open(match_report_path, 'w', encoding='utf-8', newline="") as f:
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

    # 将生成的report复制到另一个文件夹内，以免因为程序的反复多次运行造成复写i
    file = os.path.split(report_path)[1]
    shutil.copy(report_path, '/home/wuyang/Experiments/Datas/output/report_mwep_back/' + file)
    return HttpResponse("hello world")


def kg_map_apk(feature_file, apk_name):
    """
    创建从知识图谱到apk的映射，用于后续的Application
    :param feature_file: apk的特征文件
    :param apk_name: apk的文件名，不带后缀
    :return :json:匹配该apk的匹配结果
    """
    full_map_node_statistic = []  # 对于所有的APK文件，统计KG上每个节点的映射情况，对应的是完全匹配的情况
    part_map_node_statistic = []  # 对于所有的APK文件，统计KG上每个节点的映射情况，对应的是部分匹配的情况

    ans_data = []  # 存储返回前端的数据
    kg_model = augmenTestNode.objects.values()
    kg_nodes_list = list(kg_model)  # 图谱上的节点数
    ret_json0 = apk_name

    # 首先读取某个APK的特征文件
    apk_file = open(feature_file, 'r', encoding='utf-8', newline="")
    apk_features = []  # 存放该APK的特征
    mapFeatureList = []  # 存放映射上的APK的特征
    nmapFeatureList = []  # 存放没映射上的APK的特征
    a = 0
    for row in apk_file.readlines():  # 去掉多余的信息行
        line = row.strip()
        print('num:{},row:{}'.format(a, line))
        a = a + 1
        if line != '':
            apk_features.append(line)

    # *******1. 计算某个APK的特征覆盖率，这里的映射关系是：KG->某个APK特征文件，查看KG特征的完整性*******
    map_count = 0
    nmap_count = 0
    for feature in apk_features:  # 对于apk的feature，都去kg中查看是否有对应的
        tmp = feature.strip()
        judge = tmp.find("(")
        if judge != -1:
            tmp = tmp[:judge]
        if tmp.find("/"):
            tmp1 = tmp.split("/")
            tmp = "/".join(tmp1)
        elif tmp.find(";"):
            tmp1 = tmp.split(";")
            tmp = ";".join(tmp1)
        if tmp in str(kg_features):
            map_count = map_count + 1
            # print('映射成功的为：', feature)
            if feature not in mapFeatureList:
                mapFeatureList.append(feature)
            else:
                pass
        else:
            nmap_count = nmap_count + 1
            # print('映射失败的为：', feature)
            if feature not in nmapFeatureList:
                nmapFeatureList.append(feature)
            else:
                pass

    with open("detect/output/mapFeatures.txt", "a",
              encoding='utf-8') as mapFeatureFile:  # 在写入映射成功的特征前，先清空映射成功的txt文件，防止记录重复
        mapFeatureFile.truncate(0)
    with open("detect/output/nmapFetures.txt", "a", encoding='utf-8') as nmapFeatureFile:  # 在写入映射失败的特征前，先清空txt文件，防止记录重复
        nmapFeatureFile.truncate(0)
    with open("detect/output/mapFeatures.txt", "a",
              encoding='utf-8') as outfile:  # 将映射成功的写入本地文件mapFeatures.txt中，以为节点匹配做准备
        for one in mapFeatureList:
            outfile.write(one + '\n')
    with open("detect/output/nmapFetures.txt", "a", encoding='utf-8') as outfile:  # 将映射失败的写入本地文件nmapFeatures.txt中
        for one in nmapFeatureList:
            outfile.write(one + '\n')
    with open("detect/output/all_nmap.txt", "a",
              encoding='utf-8') as outfile:  # 将映射失败的写入本地文件nmapFeatures.txt中，是所有apk没有映射上的节点
        for one in nmapFeatureList:
            outfile.write(one + '\n')

    if map_count > 0:
        map_rate = map_count / (map_count + nmap_count)
        ret_json1 = str(round(map_rate, 4) * 100) + '%'
    else:
        pass

    # *******2. 计算某个APK覆盖的节点 *******
    mapFeatures = open("detect/output/mapFeatures.txt", 'r', encoding='utf-8', newline="")  # 打开映射成功的txt文件，去数据表中找匹配的api
    # **************2.1 查看能匹配上的特征**********************
    apiIdList = []  # 记录下匹配成功的api的id
    perIdList = []  # 记录下匹配成功的per的id
    for row in mapFeatures.readlines():  # 记录下匹配到的api的id
        line = row.strip()
        # 将字符串拆分后然后再再重组，不然可能出现匹配不上的问题
        if line.find(";") != -1:  # 说明处理的是api
            tmp1 = line.split(';')
            tmp = ';'.join(tmp1)
            ans = augmenTestAPi.objects.filter(apiName__icontains=tmp)
            if ans:
                ans = list(ans)
                for one in ans:
                    apiIdList.append(one.id)
            else:
                pass
        else:
            continue
    mapFeatures.close()  # 读取一次后，需要先暂时关闭然后重新读取，不然下面的遍历代码不会生效
    mapFeatures = open("detect/output/mapFeatures.txt", 'r', encoding='utf-8', newline="")
    for row in mapFeatures.readlines():  # 记录下匹配到的permission的id
        line = row.strip()
        if line.find(".") != -1:  # 说明处理的是permission
            tmp1 = line.split('.')
            tmp = '.'.join(tmp1)
            ans = PerTest.objects.filter(perName__icontains=tmp)
            if ans:
                ans = list(ans)
                for one in ans:
                    perIdList.append(one.id)
            else:
                pass
        else:
            continue
    # **************2.2 查看能匹配上的节点**********************
    mapNode = []  # 匹配上了部分特征的节点，存储着这些节点的id
    fullNode = []  # 完全匹配上的节点，存储着这些节点的id,它是匹配上的节点的子集
    for perId in perIdList:  # 根据per来匹配节点
        for one in kg_nodes_list:
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
                mapNode.append(one['nodeID'])  # 该特征出现在这些节点中

    # **************根据api来匹配节点**********************
    for apiId in apiIdList:
        for one in kg_nodes_list:
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
                mapNode.append(one['nodeID'])

    # 如果一个节点出现的次数等于该节点的特征数，其实就能判定该节点三完全匹配的，因为特征文件中的特征都是唯一的

    # 去重和排序，保持原本顺序不变
    order = list(mapNode)  # 复制
    # print("old:", partNode)
    mapNode = list(set(mapNode))  # 去重
    mapNode.sort(key=order.index)  # 恢复原本顺序
    # print("now:", partNode)

    for node in mapNode:
        part_map_node_statistic.append(node)

    # **************查看完整匹配的节点**********************
    ret_map_data = []  # 返回匹配的情况，包括：节点、节点匹配率、匹配上的特征、匹配失败的特征
    for nodeId in mapNode:  # 这里面存放的是特征匹配上的节点的ID，不一定是100%匹配
        ans = augmenTestNode.objects.get(nodeID=nodeId)
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
        ret_map_data.append(dicTmp)
        if rate == 1:  # 这些是完全特征匹配的
            fullNode.append(ans['nodeID'])

    # 去重和排序
    order = list(fullNode)
    fullNode = list(set(fullNode))
    fullNode.sort(key=order.index)
    for node in fullNode:
        full_map_node_statistic.append(node)
    allMapNum = len(kg_nodes_list)

    # 计算部分特征匹配的节点覆盖率
    partMapNum = len(mapNode)
    partMapRate = partMapNum / allMapNum
    ret_json2 = str(round(partMapRate, 4) * 100) + '%'
    ret2 = '映射上的节点覆盖率(映射上的节点数/KG节点总数)：' + ret_json2  # 以70.34%的形式输出
    # 计算完全特征匹配的节点覆盖率
    fullMapNum = len(fullNode)
    if partMapNum > 0:
        fullMapRate = fullMapNum / allMapNum
        fullMapRatePlus = fullMapNum / partMapNum
    else:
        fullMapRate = 0
        fullMapRatePlus = 0
    ret_json3 = str(round(fullMapRate, 4) * 100) + '%'
    ret_json4 = str(round(fullMapRatePlus, 4) * 100) + '%'
    ret_json5 = fullNode

    # ************3.路径匹配 ***********
    """
    算法步骤（以部分匹配为例）：
        首先记录APK的特征文件中哪些可以连通的路径，并记录那些单独存在的节点。有一个保存路径的列表。
        遍历访问该APK的部分特征匹配节点列表：
        1）访问数据库，查看该列表是否有图谱中的邻节点（在列表中，邻节点应该出现在当前节点的后面？）
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
        ans = augmenTestRel.objects.filter(sourceID=nodeId)
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
    # report.write("基于完全匹配节点的匹配路径:" + ';'.join(str(i) for i in pathList) + '\n\n\n')
    ret_json5 = pathList

    ret_json6 = []  # 返回匹配的路径中节点的ID及其名称
    if len(pathList) > 0:  # 如果存在路径匹配
        for one in pathList:
            tmp = []
            for id in one:
                ans = augmenTestNode.objects.get(nodeID=id)
                ans = object_to_json(ans)
                name = ans['actionName']
                tmp.append({'id': id, 'action': name})
            ret_json6.append(tmp)

    # 构造json返回内容，通过HttpResponse返回
    tmp = {}
    data = json.loads(json.dumps(tmp))
    data['filename'] = ret_json0
    data['maprate'] = ret_json1
    data['partmap'] = ret_json2
    data['fullmap'] = ret_json3
    data['fullandpart'] = ret_json4
    data['pathlist'] = ret_json5
    data['pathaction'] = ret_json6
    data['mapData'] = ret_map_data
    ret = json.dumps(data, ensure_ascii=False)

    return ret


def mainDetect(request):
    # ********** 一、数据准备 *************
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

    kgModel = augmenTestNode.objects.values()
    kgList = list(kgModel)  # 图谱上的节点数

    # ********** 二、依次匹配每一个文件 *************
    with open(report_path, "a", encoding='utf-8') as report:
        # 读取APK的特征文件
        global fileID
        global flag
        files = glob.glob(input_path + '/*.txt')
        fileID = 0

        fullMapNodeStatistic = []  # 对于所有的APK文件，统计KG上每个节点的映射情况，对应的是完全匹配的情况
        partMapNodeStatistic = []  # 对于所有的APK文件，统计KG上每个节点的映射情况，对应的是部分匹配的情况

        ansData = []  # 存储返回前端的数据

        for f in files:  # f形如D:/input/apkname.txt
            fileID = fileID + 1
            flag = 0
            filePathAndName = os.path.split(f)  # 返回值为元组：（path, file name）
            fileName = filePathAndName[1]
            retJson0 = fileName
            report.write("****************** APK " + str(fileID) + " ******************\n")  # 记录当前APK的名字
            report.write("文件名：" + fileName + '\n')  # 记录当前APK的名字

            # 首先读取某个APK的特征文件
            apkFile = open(f, 'r', encoding='utf-8', newline="")
            apkFeatures = []  # 存放该APK的特征
            mapFeatureList = []  # 存放映射上的APK的特征
            nmapFeatureList = []  # 存放没映射上的APK的特征

            for row in apkFile.readlines():  # 去掉多余的信息行
                line = row.strip()
                if line == "perStart":
                    flag = 1
                    continue
                elif line == 'perEnd':
                    flag = 0
                    continue
                elif line == 'apiStart':
                    flag = 1
                    continue
                elif line == 'apiEnd':
                    flag = 0
                    break
                else:
                    pass
                if flag == 1:
                    apkFeatures.append(line)

            # *******1. 计算某个APK的特征覆盖率，这里的映射关系是：KG->某个APK特征文件，查看KG特征的完整性*******
            mapCount = 0
            nmapCount = 0

            # 测试所有特征的覆盖率
            for feature in apkFeatures:  # 对于apk的feature，都去kg中查看是否有对应的
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
                    if feature not in mapFeatureList:
                        mapFeatureList.append(feature)
                    else:
                        pass
                else:
                    nmapCount = nmapCount + 1
                    # print('映射失败的为：', feature)
                    if feature not in nmapFeatureList:
                        nmapFeatureList.append(feature)
                    else:
                        pass

            # 在写入映射成功的特征前，先清空映射成功的txt文件，防止记录重复
            with open("detect/output/mapFeatures.txt", "a", encoding='utf-8') as mapFeatureFile:
                mapFeatureFile.truncate(0)
            # 在写入映射失败的特征前，先清空txt文件，防止记录重复
            with open("detect/output/nmapFetures.txt", "a", encoding='utf-8') as nmapFeatureFile:
                nmapFeatureFile.truncate(0)
            # 将映射成功的写入本地文件mapFeatures.txt中，以为节点匹配做准备
            with open("detect/output/mapFeatures.txt", "a", encoding='utf-8') as outfile:  # 这种方法会自动关闭文件
                for one in mapFeatureList:
                    outfile.write(one + '\n')
            # 将映射失败的写入本地文件nmapFeatures.txt中
            with open("detect/output/nmapFetures.txt", "a", encoding='utf-8') as outfile:  # 这种方法会自动关闭文件
                for one in nmapFeatureList:
                    outfile.write(one + '\n')

            if mapCount > 0:
                mapRate = mapCount / (mapCount + nmapCount)
                retJson1 = str(round(mapRate, 4) * 100) + '%'
                ret1 = '特征映射成功率(映射上的特征数/APK总的特征数)：' + str(
                    round(mapRate, 4) * 100) + '%'  # 以70.34%的形式输出
                report.write(ret1 + '\n')
            else:
                pass

            # *******2. 计算某个APK覆盖的节点 *******
            # 打开映射成功的txt文件，去数据表中找匹配的api
            mapFeatures = open("detect/output/mapFeatures.txt", 'r', encoding='utf-8', newline="")
            apiIdList = []  # 记录下匹配成功的api的id
            perIdList = []  # 记录下匹配成功的per的id

            # for one in mapFeatureList:
            #     pass

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
                            apiIdList.append(one.id)
                    else:
                        pass
                else:
                    continue

            # 读取一次后，需要先暂时关闭然后重新读取，不然下面的遍历代码不会生效
            mapFeatures.close()
            mapFeatures = open("detect/output/mapFeatures.txt", 'r', encoding='utf-8', newline="")

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
                            perIdList.append(one.id)
                    else:
                        pass
                else:
                    continue

            partNode = []  # 匹配上了部分特征的节点，存储着这些节点的id
            fullNode = []  # 完全匹配上的节点，存储着这些节点的id

            # 根据per来匹配节点
            # **************查看能匹配上的节点**********************
            for perId in perIdList:
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
                ans = augmenTestNode.objects.get(nodeID=nodeId)
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
                ans = augmenTestRel.objects.filter(sourceID=nodeId)
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
            retJson5 = pathList

            retJson6 = []  # 返回匹配的路径中节点的ID及其名称
            if len(pathList) > 0:  # 如果存在路径匹配
                for one in pathList:
                    tmp = []
                    for id in one:
                        ans = augmenTestNode.objects.get(nodeID=id)
                        ans = object_to_json(ans)
                        name = ans['actionName']
                        tmp.append({'id': id, 'action': name})
                    retJson6.append(tmp)

        # 构造json返回内容，通过HttpResponse返回
        tmp = {}
        data = json.loads(json.dumps(tmp))
        data['filename'] = retJson0
        data['maprate'] = retJson1
        data['partmap'] = retJson2
        data['fullmap'] = retJson3
        data['fullandpart'] = retJson4
        data['pathlist'] = retJson5
        data['pathaction'] = retJson6
        data['mapData'] = retMapData
        ret = json.dumps(data, ensure_ascii=False)

    return HttpResponse(ret, status=200)


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


def apk_map_kg_main_after_augment():
    """
    使用扩充后的知识图谱来匹配APK
    """
    global kg_apis, kg_permissions, kg_features, apis_from_test
    kg_permissions, kg_apis, kg_features = get_pers_apis_after_augment()  # 初始化数据：get all permissions&apis from kg/database
    apis_from_test = get_apis_from_test_after_augment()

    # 1、生成98个样本apk的特征文件
    # sample_apks_folder_path = '/home/wuyang/Experiments/Datas/malwares/sample_apk_100'
    # sample_apks_folder_path = '/home/wuyang/Experiments/Datas/malwares/googlePlay/apk_sample'
    # sample_apks_folder_path='/home/wuyang/Experiments/Datas/malwares/part_androzoo/androzoo_apk_100'
    # sample_apks_folder_path = '/home/wuyang/Experiments/Datas/tmpApk/protest'
    sample_apks_folder_path = '/media/wuyang/WD_BLACK/AndroidMalware/malware_test_googleplay'

    match_report_ans = []

    # 为了避免Django项目内的文件过多，生成CG文件和特征文件前先将文件夹清空
    # shutil.rmtree('detect/outputCG')  # 删除该文件夹以及该文件夹下的所有文件
    # shutil.rmtree('detect/output_features')
    # os.mkdir('detect/outputCG')  # 创建新的文件夹
    # os.mkdir('detect/output_features')
    fullMapNodeStatistic = []  # 对于所有的APK文件，统计KG上每个节点的映射情况，对应的是完全匹配的情况
    partMapNodeStatistic = []  # 对于所有的APK文件，统计KG上每个节点的映射情况，对应的是部分匹配的情况
    featureMapStatistic = []  # 对于所有的APK文件，统计KG上每个特征的映射情况
    apk_feature_map = []  # 对于每一个apk，映射上的特征/该APK总的特征数。里面存储了所有apk的特征映射情况
    pathMapStatistic = []  # 对于所有的APK文件，统计KG上每条路径的映射情况
    kgModel = models.augmenTestNode.objects.values()
    kgList = list(kgModel)

    # ********** 二、依次匹配每一个文件 *************
    with open(report_path_augment, "a", encoding='utf-8') as report:
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
            print("apk:", f)
            flag = 0
            # 生成APK的特征文件，如果文件存在则不另外生成
            filename = os.path.split(f)[1]  # 文件的名称(带后缀)
            apk_name = filename.split('.')[0]  # 文件名（不带后缀）
            print('apk name：', apk_name)
            if os.path.exists('detect/output_features/' + apk_name + '_features.txt'):
                print('特征文件存在')
                continue
            else:
                print('特征文件不存在')
                gml, apk_name = generate_cg(f)  # 输入apk，生成cg
                txt = gml_txt(gml, apk_name)  # 将cg转化为txt文件
                txt = os.path.join('detect/outputCG/', apk_name + '.txt')
                extract_features_plus(txt, apk_name, f)  # 提取特征,生成特征文件
            # try:
            #     f = open('detect/output_features/' + apk_name + '_features.txt')
            #     f.close()
            #     print('特征文件存在')
            #     continue
            # except Exception:
            #     print('特征文件不存在')
            #     gml, apk_name = generate_cg(f)  # 输入apk，生成cg
            #     txt = gml_txt(gml, apk_name)  # 将cg转化为txt文件
            #     txt = os.path.join('detect/outputCG/', apk_name + '.txt')
            #     extract_features_plus(txt, apk_name, f)  # 提取特征,生成特征文件
                # if os.path.exists('detect/output_features/' + apk_name + '_features.txt'):
            #     print('特征文件已存在:', apk_name)
            #     continue  # 如果该文件的特征文件存在，说明已经匹配过了，那么直接开始下一个apk的匹配，以减少运行时间
            # else:
            #     extract_features_plus(txt, apk_name, f)  # 提取特征,生成特征文件
            # 写入report
            report.write("****************** APK " + str(file_id) + " ******************\n")  # 记录当前APK的名字
            report.write("文件名：" + apk_name + '\n')  # 记录当前APK的名字
            retJson0 = apk_name
            # 首先读取某个APK的特征文件
            feature_file_path = 'detect/output_features/' + apk_name + '_features.txt'
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
                            ans = models.augmenTestAPi.objects.get(apiName=tmp)
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
            with open("detect/output/mapFeatures.txt", "a", encoding='utf-8') as mapFeatureFile:
                mapFeatureFile.truncate(0)
            # # 在写入映射失败的特征前，先清空txt文件，防止记录重复
            # with open("detect/output/nmapFetures.txt", "a", encoding='utf-8') as nmapFeatureFile:
            #     nmapFeatureFile.truncate(0)
            # 将映射成功的写入本地文件mapFeatures.txt中，以为节点匹配做准备
            with open("detect/output/mapFeatures.txt", "a", encoding='utf-8') as outfile:  # 这种方法会自动关闭文件
                for one in mapFeatureList:
                    outfile.write(one + '\n')
            with open("detect/output/all_map.txt", "a", encoding='utf-8') as outfile:
                for one in mapFeatureList:
                    outfile.write(one + '\n')
            # 将映射失败的写入本地文件nmapFeatures.txt中
            with open("detect/output/nmapFetures.txt", "a", encoding='utf-8') as outfile:  # 这种方法会自动关闭文件
                for one in nmapFeatureList:
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
            mapFeatures = open("detect/output/mapFeatures.txt", 'r', encoding='utf-8', newline="")
            apiIdList = []  # 记录下匹配成功的api的id
            perIdList = []  # 记录下匹配成功的per的id

            # 记录下匹配到的api的id
            for row in mapFeatures.readlines():
                line = row.strip()
                # 将字符串拆分后然后再再重组，不然可能出现匹配不上的问题
                if line.find(";") != -1:  # 说明处理的是api
                    tmp1 = line.split(';')
                    tmp = ';'.join(tmp1)  # tmp为按顺序出现的api
                    ans = models.augmenTestAPi.objects.filter(apiName=tmp)
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
            mapFeatures = open("detect/output/mapFeatures.txt", 'r', encoding='utf-8', newline="")

            # 记录下匹配到的permission的id
            for row in mapFeatures.readlines():
                line = row.strip()
                if line.find(".") != -1:
                    tmp1 = line.split('.')
                    tmp = '.'.join(tmp1)
                    ans = models.augmenTestPer.objects.filter(perName__icontains=tmp)
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
                ans = models.augmenTestNode.objects.get(nodeID=nodeId)
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
                ans = models.augmenTestRel.objects.filter(sourceID=nodeId)
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

            with open(match_report_path_augment, 'a', encoding='utf-8', newline="") as f:
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

    with open(report_path_augment, "a", encoding='utf-8') as outfile:  # 这种方法会自动关闭文件
        outfile.write("\n\n****************** KG Statistics ******************\n")
        outfile.write(ret9 + '\n')
        # outfile.write(ret11 + '\n')
        outfile.write(ret5 + '\n')
        outfile.write(ret6 + '\n')
        outfile.write(ret7 + '\n')
        outfile.write(ret8 + '\n')
        outfile.write(ret10 + '\n')

    # 将生成的report复制到另一个文件夹内，以免因为程序的反复多次运行造成复写i
    # file = os.path.split(report_path)[1]
    # shutil.copy(report_path, '/home/wuyang/Experiments/Datas/output/report_mwep_back/' + file)
    return HttpResponse("match after augment")
