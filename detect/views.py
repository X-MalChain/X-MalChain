import re
import string
import glob
import os
import sys
import json
import shutil
import codecs  # 将ansi编码的文件转为utf-8编码的文件

from django.shortcuts import render
from django.http import HttpResponse

# from androguard.core.bytecodes import apk
# from androguard.core.bytecodes import dvm
# from androguard.core.analysis.analysis import Analysis
from androguard.misc import AnalyzeAPK
from androguard.core.androconf import load_api_specific_resource_module
from manager.views import dict_trans_list
import csv
from common.models import augmenTestAPi, PerTest, KgTest, relTest
from common import models

kg_permissions = []  # all permissions in kg/database
kg_apis = []  # all apis in kg/database
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
report_path = '/home/wuyang/Experiments/Datas/output/report_mwep/report1.txt'
input_path = '/home/wuyang/Experiments/Datas/tmpApk'

# flag = 0
fileID = 0


# 在写入映射失败的特征前，先清空txt文件，防止记录重复
# with open("detect/output/nmapFetures.txt", "a", encoding='utf-8') as nmapFeatureFile:
#     nmapFeatureFile.truncate(0)


def test(request):
    # 在写入映射报告前，先清空txt文件，防止报告重复
    with open(report_path, "a", encoding='utf-8') as report:
        report.truncate(0)

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
    apk_map_kg_main()
    # ********************************************

    # *******处理样本数据*********
    # root_path = '/home/wuyang/Experiments/Datas/malwares/googlePlay/code_reports'
    # dirs = read_path(root_path)
    # # print('dirs:', dirs)
    # for dir in dirs:
    #     print('dir:', dir)
    #     # find_apk(root_path+'/'+dir, dir)
    #     find_apk_v1(root_path + '/' + dir, dir)
    # **************************

    # testApk_path = '/home/wuyang/Experiments/Datas/tmpdata/testAPK.txt'
    # 获取APK文件对象
    # a = apk.APK('/home/wuyang/Experiments/Datas/tmpApk/10.apk', False, "r", None, 2)
    # permissions=apk.get
    # 获取DEX文件对象
    # d = dvm.DalvikVMFormat(a.get_dex())
    # 获取分析结果对象
    # x = Analysis.VMAnalysis(d)
    # a表示apk文件信息,关 APK 的信息，例如包名、权限、AndroidManifest.xml、resources；
    # d表示dex文件对象，可以获取类，方法和字符串；
    # dex表示 Analysis 对象，其包含链接了关于 classes.dex 信息的特殊的类
    # a, d, dx = AnalyzeAPK('/home/wuyang/Experiments/Datas/tmpApk/10.apk')
    # for meth, perm in dx.get_permissions(a.get_effective_target_sdk_version()):
    #     print('Using API method {method} for permission {permission}'.format(method=meth, permission=perm))
    #     print('used in:')
    #     for _, m, _ in meth.get_xref_from():
    #         print(m.full_name)
    # print('调用方法：', dx.get_methods())
    # 构造json返回内容，通过HttpResponse返回
    # tmp = {}
    # data = json.loads(json.dumps(tmp))
    # # data['analysis_ans'] = x
    # ret = json.dumps(data, ensure_ascii=False)
    # os.system('androguard cg %m -o %n'(arg1, arg2))
    # os.system('androguard cg /home/wuyang/Experiments/Datas/tmpApk/10.apk -o '
    #           '/home/wuyang/Experiments/Datas/tmpApk/10.gml')
    # global kg_apis, kg_permissions, kg_features
    # kg_permissions, kg_apis, kg_features = get_pers_apis()  # 初始化数据：get all permissions&apis from kg/database
    # apk_path = '/home/wuyang/Experiments/Datas/tmpApk/10.apk'
    # gml, apk_name = generate_cg(apk_path)  # 输入apk，生成cg
    # txt = gml_txt(gml, apk_name)  # 将cg转化为txt文件
    # # print('txt:', txt)
    # # database_test()  # 测试数据库是否可以正常接入
    # extract_features(txt, apk_name, apk_path)  # 提取特征

    return HttpResponse('detect test', status=200)


def get_pers_apis():
    """
    :return: :list: all permissions in kg
            :list: all apis in kg
    """
    per_list = PerTest.objects.values('perName')
    api_list = augmenTestAPi.objects.values('apiName')
    # 此时的per_list api_list是由字典组成的数组，因此进行下述处理
    per_list = dict_list(per_list, 0)
    api_list = dict_list(api_list, 1)

    kg_list = list(per_list)  # 直接复制一份数据
    # permissions + apis = kg 中的所有特征
    for one in api_list:
        kg_list.append(one)

    return per_list, api_list, kg_list


def dict_list(demo_list, _flag):
    """
    :param demo_list:由字典组成的数组 QuerySet，形如：[{'perName': 'android.permission.ACCESS_BACKGROUND_LOCATION'}, {'perName': 'android.permission.ACCESS_COARSE_LOCATION'}]
    :param _flag: 指示传入的数组是permissions还是apis，又或者是node
    :return a sample list
    """
    ret_list = []
    if _flag == 0:  # 权限的QuerySet
        for i in demo_list:
            ret_list.append(i['perName'])
    elif _flag == 1:
        for i in demo_list:
            ret_list.append(i['apiName'])
    elif _flag == 2:
        for i in demo_list:
            ret_list.append(i['actionName'])
    else:
        print('Error: dict_list throw a exception!')
    return ret_list


def generate_cg(apk):
    """
    :param apk:带完整路径和后缀的apk文件
    :return: 该apk利用androguard生成的gml文件，即call graph，:param
            :string: apk_name: 该apk的名称，不带后缀
    """
    filename = os.path.split(apk)[1]  # 文件的名称(带后缀)
    apk_name = filename.split('.')[0]  # 文件名（不带后缀）
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
    # print('file:', gml_file)
    new_file = apk_name + '.txt'
    # print('gml_file')
    os.rename(gml_file, 'detect/outputCG/' + new_file)
    # file = glob.glob('detect/outputCG/' + apk_name + '.txt')
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
    # feature_file.write('apiStart' + '\n')
    for edge in edge_list:
        tmp = re.findall('\d+', edge)
        source = int(tmp[0])
        target = int(tmp[1])
        # print('source:{} \ntarget:{}'.format(source, target))
        api_location = re.findall('L.*?;->.*?]', node_list[source])
        # print('node list:', node_list[source])
        # print('location:', api_location)
        api_location = re.findall('L.*?;->.*?]', node_list[source])  # 能在node_list[source]中找到符合正则表达式的字符串，以列表的形式返回
        # 下面分情况讨论
        if api_location:
            api_location = re.findall('L.*?;->.*?]', node_list[target])  # 第1种情况
            if api_location:  # 第1.1种情况
                continue
            else:  # 第1.2种情况
                api_location = re.findall(
                    '(L.*?;->.*?)"', node_list[target])
                if api_location:
                    for api in api_location:
                        # api_list.append(api)
                        tmp = api
                        if tmp[0] == "L":  # 去掉开头的L
                            tmp = api[1:]
                        judge = tmp.find("(")  # 截取字符串
                        if judge != -1:
                            tmp = tmp[:judge]
                        if tmp in str(kg_apis):
                            api_list.append(tmp)
                            # feature_file.write(tmp + '\n')
                            # feature_file.write('一跳开始' + '\n')
                            # api_list.append(find_related_node(target, edge_list, node_list)[1])
                            # feature_file.write('一跳结束' + '\n')
        else:  # 第2种情况)
            api_location = re.findall('(L.*?;->.*?)"', node_list[source])
            if api_location:
                for api in api_location:
                    # api_list.append(api)
                    tmp = api
                    if tmp[0] == "L":  # 去掉开头的L
                        tmp = api[1:]
                    judge = tmp.find("(")  # 截取字符串
                    if judge != -1:
                        tmp = tmp[:judge]
                    if tmp in str(kg_apis):
                        # feature_file.write(tmp + '\n')
                        api_list.append(tmp)

            api_location = re.findall('L.*?;->.*?]', node_list[target])
            if api_location:  # 第2.1种情况
                continue
            else:  # 第2.2种情况
                api_location = re.findall(
                    '(L.*?;->.*?)"', node_list[target])
                if api_location:
                    for api in api_location:
                        # api_list.append(api)
                        tmp = api
                        if tmp[0] == "L":  # 去掉开头的L
                            tmp = api[1:]
                        judge = tmp.find("(")  # 截取字符串
                        if judge != -1:
                            tmp = tmp[:judge]
                        if tmp in str(kg_apis):
                            # perm_api_file.write(tmp + '\n')
                            # api_list.append(tmp)
                            feature_file.write(tmp + '\n')
                            # feature_file.write('一跳开始' + '\n')
                            # api_list.append(find_related_node(target, edge_list, node_list)[1])
                            # feature_file.write('一跳结束' + '\n')

    i = 0  # 从类似[1,2,2,3,3,3,4,1]转变为[1,2,3,4,1]
    while i < len(api_list) - 1:
        if api_list[i] == api_list[i + 1]:
            del api_list[i]
        else:
            i = i + 1
    for api in api_list:
        feature_file.write(api + '\n')
    # feature_file.write("apiEnd" + '\n')
    feature_file.close()

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
    global kg_apis, kg_permissions, kg_features
    kg_permissions, kg_apis, kg_features = get_pers_apis()  # 初始化数据：get all permissions&apis from kg/database
    # print('kg fearure len:', len(kg_features))

    # 1、生成98个样本apk的特征文件
    sample_apks_folder_path = '/home/wuyang/Experiments/Datas/malwares/sample_apk_100'
    # sample_apks_folder_path = '/home/wuyang/Experiments/Datas/malwares/googlePlay/apk_sample'

    # 为了避免Django项目内的文件过多，生成CG文件和特征文件前先将文件夹清空
    shutil.rmtree('detect/outputCG')  # 删除该文件夹以及该文件夹下的所有文件
    shutil.rmtree('detect/output_features')
    os.mkdir('detect/outputCG')  # 创建新的文件夹
    os.mkdir('detect/output_features')

    # ********** 二、依次匹配每一个文件 *************
    with open(report_path, "a", encoding='utf-8') as report:
        # 读取所有的APK
        global flag
        files = glob.glob(sample_apks_folder_path + '/*.apk')
        # files=os.listdir(sample_apks_folder_path)
        file_id = 0
        fullMapNodeStatistic = []  # 对于所有的APK文件，统计KG上每个节点的映射情况，对应的是完全匹配的情况
        partMapNodeStatistic = []  # 对于所有的APK文件，统计KG上每个节点的映射情况，对应的是部分匹配的情况
        featureMapStatistic = []  # 对于所有的APK文件，统计KG上每个特征的映射情况
        apk_feature_map = []  # 对于每一个apk，映射上的特征/该APK总的特征数。里面存储了所有apk的特征映射情况
        pathMapStatistic = []  # 对于所有的APK文件，统计KG上每条路径的映射情况
        kgModel = KgTest.objects.values()
        kgList = list(kgModel)  # 图谱上的节点数

        report.write(
            "******************\n " + "Dataset: " + sample_apks_folder_path + " ******************\n")  # 记录当前APK的名字
        report.write("******************\n " + '计算节点匹配率时，去掉permission' + " ******************\n\n")

        # 依次读取每一个APK
        for f in files:  # f形如D:/input/apk01.apk
            print("***********************")
            print("apk:", f)
            file_id = file_id + 1
            flag = 0
            # 生成APK的特征文件
            gml, apk_name = generate_cg(f)  # 输入apk，生成cg
            txt = gml_txt(gml, apk_name)  # 将cg转化为txt文件
            extract_features(txt, apk_name, f)  # 提取特征,生成特征文件
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
                a = a + 1
                if line != '':
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
                if tmp.find("."):  # permissions
                    tmp1 = tmp.split(".")
                    tmp = ".".join(tmp1)
                elif tmp.find(";"):  # apis
                    tmp1 = tmp.split(";")
                    tmp = ";".join(tmp1)
                if tmp in str(kg_features):
                    mapCount = mapCount + 1
                    # print('映射成功的为：', feature)
                    if feature not in mapFeatureList:
                        mapFeatureList.append(feature)
                    else:
                        pass
                    featureMapStatistic.append(feature)
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
                ans = KgTest.objects.get(nodeID=nodeId)
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
                            if len(tmp) > 1:
                                pathList.append(tmp)
                                pathMapStatistic.append(tmp)
                            tmp = []
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
            isolatedNode = list(set(isolatedNode))
            # 下面的print为调试信息
            # print("fullNodeIdList:", fullNodeIdList)
            # print("pathList:", pathList)
            # print("isolatedNode:", isolatedNode)
            # print("test:",list(set(test)))
            report.write("基于完全匹配节点的匹配路径:" + ';'.join(str(i) for i in pathList) + '\n\n\n')

    # ******* 返回图谱的统计信息 *******
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
    kg_model = KgTest.objects.values()
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
        ans = KgTest.objects.get(nodeID=nodeId)
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
    # report.write("基于完全匹配节点的匹配路径:" + ';'.join(str(i) for i in pathList) + '\n\n\n')
    ret_json5 = pathList

    ret_json6 = []  # 返回匹配的路径中节点的ID及其名称
    if len(pathList) > 0:  # 如果存在路径匹配
        for one in pathList:
            tmp = []
            for id in one:
                ans = KgTest.objects.get(nodeID=id)
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

    kgModel = KgTest.objects.values()
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
                ans = KgTest.objects.get(nodeID=nodeId)
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
            retJson5 = pathList

            retJson6 = []  # 返回匹配的路径中节点的ID及其名称
            if len(pathList) > 0:  # 如果存在路径匹配
                for one in pathList:
                    tmp = []
                    for id in one:
                        ans = KgTest.objects.get(nodeID=id)
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
