from django.shortcuts import render
from django.http import HttpResponse
import json
from common import models
from common.models import ApiTest, PerTest, KgTest, KgBackup, ApiSim, ApiSDK, sensitiveApi
from detect.views import dict_list, generate_cg, gml_txt, extract_features
import re

kg_permissions = []  # all permissions in kg/database
kg_apis = []  # all apis in kg/database
kg_features = []  # all features(permissions+apis) in kg


def test(request):
    # 1、打印出KG上匹配效果较差的节点
    # dict_data = {"1": 47, "2": 16, "3": 55, "4": 39, "5": 7, "6": 5, "7": 64, "8": 28, "9": 2, "10": 61, "11": 22,
    #              "12": 50, "13": 47, "14": 35, "15": 35, "16": 40, "17": 27, "18": 23, "19": 40, "20": 37, "21": 53,
    #              "22": 44, "23": 9, "24": 1, "25": 19, "26": 16, "27": 1, "28": 38, "29": 24, "30": 0, "31": 28,
    #              "32": 24, "33": 20, "34": 4, "35": 36, "36": 45, "37": 38, "38": 14, "39": 18, "40": 20, "41": 50,
    #              "42": 40, "43": 55, "44": 24, "45": 33, "46": 35}
    # print_kg(dict_data)

    # 2、打印出KG上的api需要申请的权限
    # api_map_per()

    # 3、打印出图谱上的所有节点，第二次修改后
    # print_kg_all()
    # print_kg_all_version1()
    # print_kg_rel_version1()
    print_kg_all_version2()
    print_kg_rel_version2()
    #
    # apk_path = '/home/wuyang/Experiments/Datas/tmpApk/9a.apk'
    # a, d, dx = AnalyzeAPK(apk_path)
    # permissions = a.get_permissions()
    # print("APK申请的权限有：")
    # for i in permissions:
    #     print(i)
    # apk_cg(apk_path)

    # 4、自动增加路径
    # longest_substring()

    # 5、填充ApiTest数据表的addList和repList
    # find_link_num()

    # 6、创建敏感API数据库
    # get_sensitive_apis()
    # get_sensitive_apis_mini()

    return HttpResponse('tools test')


# Create your views here.
def print_kg(dict_data):
    """l
    :param dict_data:反映节点的匹配情况
    """
    output_path = '/home/wuyang/Experiments/Datas/output/tools_mwep/print_kg.txt'
    # 在写入映射报告前，先清空txt文件，防止报告重复
    with open(output_path, "a", encoding='utf-8') as report:
        report.truncate(0)
    with open(output_path, "a", encoding='utf-8') as report:
        # report.write('ID, Node Name, Per ID, Per List, API ID, API List')
        for key, value in dict_data.items():
            if value == 0:
                # ans = KgTest.objects.get(id=int(key))     # 原有KG数据表
                ans = models.KgBackup.objects.get(id=int(key))  # 第一次更新后的KG数据表
                apistr = ans.apiList
                perstr = ans.perList
                node_id = ans.nodeID
                node_name = ans.actionName
                api_list = str_str(apistr, 0)
                per_list = str_str(perstr, 1)
                report.write('********************\n')
                ret = str(node_id) + '-' + node_name + ':\n' + perstr + ':' + ','.join(
                    str(i) for i in per_list) + '\n' + apistr + ':' + ','.join(
                    str(i) for i in api_list) + '\n'
                report.write(ret)
                report.write('********************\n\n')
        # else:
        #     continue


# Create your views here.
def print_kg_all():
    """
    打印出整张图谱的节点
    """
    output_path = '/home/wuyang/Experiments/Datas/output/tools_mwep/print_kg_all.txt'
    node_num = len(list(models.KgBackup.objects.values()))
    # 在写入映射报告前，先清空txt文件，防止报告重复
    with open(output_path, "a", encoding='utf-8') as report:
        report.truncate(0)
    with open(output_path, "a", encoding='utf-8') as report:
        # report.write('ID, Node Name, Per ID, Per List, API ID, API List')
        # for key, value in dict_data.items():
        #     ans = KgTest.objects.get(id=int(key))
        #     apistr = ans.apiList
        #     perstr = ans.perList
        #     node_id = ans.nodeID
        #     node_name = ans.actionName
        #     api_list = str_str(apistr, 0)
        #     per_list = str_str(perstr, 1)
        #     report.write('********************\n')
        #     ret = str(node_id) + '-' + node_name + ':\n' + perstr + ':' + ','.join(
        #         str(i) for i in per_list) + '\n' + apistr + ':' + ','.join(
        #         str(i) for i in api_list) + '\n'
        #     report.write(ret)
        #     report.write('********************\n\n')
        for i in range(1, node_num + 1):
            # ans = KgTest.objects.get(id=i)  # 旧的数据表
            ans = models.KgBackup.objects.get(id=i)  # 新的数据表
            apistr = ans.apiList
            perstr = ans.perList
            node_id = ans.nodeID
            node_name = ans.actionName
            api_list = str_str(apistr, 0)
            per_list = str_str(perstr, 1)
            report.write('********************\n')
            ret = str(node_id) + '-' + node_name + ':\n' + perstr + ':' + ','.join(
                str(i) for i in per_list) + '\n' + apistr + ':' + ','.join(
                str(i) for i in api_list) + '\n'
            report.write(ret)
            report.write('********************\n\n')


def print_kg_all_version1():
    """
    打印出整张新图谱的节点和关系
    """
    output_path = '/home/wuyang/Experiments/Datas/output/tools_mwep/print_kg_all_version1.txt'
    node_num = len(list(models.augmenTestNode.objects.values()))
    model=list(models.augmenTestNode.objects.values())
    # 在写入映射报告前，先清空txt文件，防止报告重复
    with open(output_path, "a", encoding='utf-8') as report:
        report.truncate(0)
    with open(output_path, "a", encoding='utf-8') as report:
        report.write("DataBase: AUGMENT\n\n")
        for one in model:
            # ans = KgTest.objects.get(id=i)  # 旧的数据表
            apistr = one['apiList']
            perstr = one['perList']
            node_id = one['nodeID']
            node_name = one['actionName']
            api_list = str_str_version1(apistr, 0)
            per_list = str_str_version1(perstr, 1)
            report.write('********************\n')
            ret = str(node_id) + '-' + node_name + ':\n' + perstr + ':' + ','.join(
                str(i) for i in per_list) + '\n' + apistr + ':' + ','.join(
                str(i) for i in api_list) + '\n'
            report.write(ret)
            report.write('********************\n\n')


def print_kg_all_version2():
    """
    打印出整张新图谱的节点和关系
    """
    output_path = '/home/wuyang/Experiments/Datas/output/tools_mwep/print_kg_all_version1.txt'
    model = list(models.augmentNodeIn.objects.values())
    # 在写入映射报告前，先清空txt文件，防止报告重复
    with open(output_path, "a", encoding='utf-8') as report:
        report.truncate(0)
    with open(output_path, "a", encoding='utf-8') as report:
        report.write("DataBase: AUGMENT\n\n")
        for one in model:
            # ans = KgTest.objects.get(id=i)  # 旧的数据表
            apistr = one['apiList']
            perstr = one['perList']
            node_id = one['nodeID']
            node_name = one['actionName']
            api_list = str_str_version2(apistr, 0)
            per_list = str_str_version2(perstr, 1)
            report.write('********************\n')
            ret = str(node_id) + '-' + node_name + ':\n' + perstr + ':' + ','.join(
                str(i) for i in per_list) + '\n' + apistr + ':' + ','.join(
                str(i) for i in api_list) + '\n'
            report.write(ret)
            report.write('********************\n\n')


def print_kg_rel_version1():
    """
    打印出整张新图谱的关系
    """
    output_path = '/home/wuyang/Experiments/Datas/output/tools_mwep/print_kg_rel_version1.txt'
    node_num = len(list(models.augmenTestRel.objects.values()))
    # 在写入映射报告前，先清空txt文件，防止报告重复
    with open(output_path, "a", encoding='utf-8') as report:
        report.truncate(0)
    with open(output_path, "a", encoding='utf-8') as report:
        report.write("DataBase: AUGMENT\n\n")
        for i in range(1, node_num + 1):
            ans = models.augmenTestRel.objects.get(id=i)  # 新的数据表
            id = ans.id
            source = ans.sourceID
            target = ans.targetID
            relation = ans.relation
            ret = '**********'+str(id) + '**********' + '\n**orientation**:' + str(source) + '--->' + str(target)+ '\n' +  '**relation**:' + relation + '\n'
            report.write(ret)
            report.write('********************\n\n')



def print_kg_rel_version2():
    """
    打印出整张新图谱的关系
    """
    output_path = '/home/wuyang/Experiments/Datas/output/tools_mwep/print_kg_rel_version1.txt'
    node_num = len(list(models.augmentRelIn.objects.values()))
    # 在写入映射报告前，先清空txt文件，防止报告重复
    with open(output_path, "a", encoding='utf-8') as report:
        report.truncate(0)
    with open(output_path, "a", encoding='utf-8') as report:
        report.write("DataBase: AUGMENT\n\n")
        for i in range(1, node_num + 1):
            try:
                ans = models.augmentRelIn.objects.get(id=i)  # 新的数据表
                id = ans.id
                source = ans.sourceID
                target = ans.targetID
                relation = ans.relation
                print('source->target:',str(source)+'->'+str(target))
                ret = '**********'+str(id) + '**********' + '\n**orientation**:' + str(source) + '--->' + str(target)+ '\n' +  '**relation**:' + relation + '\n'
                source = models.augmentNodeIn.objects.get(nodeID=source).actionName
                target = models.augmentNodeIn.objects.get(nodeID=target).actionName
                report.write(ret)
                report.write(source + '--->' + target)
                report.write('********************\n\n')
            except:
                pass


def str_str(str_id, flag):
    """
    function: 根据传入的字符串，提取出id，然后根据id和flag去相应的数据表中找到对应的特征名称
    :param str_id: 特征ID的数组，但实际上是个字符串
    :param flag: 用以标识要查询的是permission还是api, 0是api，1是permission
    :return str_list: 特征名称的数组
    """
    id_list = []
    str_list = []
    if str_id != '' and str_id != ' ':
        str_id = str_id.replace(' ', '')
        if str_id.find(','):
            id_list = str_id.split(',')
        else:
            id_list.append(str_id)
        if flag == 0:  # 去api的数据表中查找
            for one in id_list:
                ans = models.KgBackup.objects.get(id=int(one))
                if ans:
                    str_list.append(ans.apiName)
                else:
                    print('id为' + one + '的api未找到')
        elif flag == 1:
            for one in id_list:
                ans = PerTest.objects.get(id=int(one))
                if ans:
                    str_list.append(ans.perName)
                else:
                    print('id为' + one + '的permission未找到')
    return str_list


def str_str_version1(str_id, flag):
    """
    function: 根据传入的字符串，提取出id，然后根据id和flag去相应的数据表中找到对应的特征名称
    :param str_id: 特征ID的数组，但实际上是个字符串
    :param flag: 用以标识要查询的是permission还是api, 0是api，1是permission
    :return str_list: 特征名称的数组
    """
    id_list = []
    str_list = []
    if str_id != '' and str_id != ' ':
        str_id = str_id.replace(' ', '')
        if str_id.find(','):
            id_list = str_id.split(',')
        else:
            id_list.append(str_id)
        if flag == 0:  # 去api的数据表中查找
            for one in id_list:
                # print('api id:',one)
                try:
                    ans = models.augmenTestAPi.objects.get(apiID=int(one))
                    if ans:
                        str_list.append(ans.apiName)
                except:
                    print('id为' + one + '的api未找到')
        elif flag == 1:
            for one in id_list:
                ans = models.augmenTestPer.objects.get(id=int(one))
                if ans:
                    str_list.append(ans.perName)
                else:
                    print('id为' + one + '的permission未找到')
    return str_list

def str_str_version2(str_id, flag):
    """
    function: 根据传入的字符串，提取出id，然后根据id和flag去相应的数据表中找到对应的特征名称
    :param str_id: 特征ID的数组，但实际上是个字符串
    :param flag: 用以标识要查询的是permission还是api, 0是api，1是permission
    :return str_list: 特征名称的数组
    """
    id_list = []
    str_list = []
    if str_id != '' and str_id != ' ':
        str_id = str_id.replace(' ', '')
        if str_id.find(','):
            id_list = str_id.split(',')
        else:
            id_list.append(str_id)
        if flag == 0:  # 去api的数据表中查找
            for one in id_list:
                # print('api id:',one)
                try:
                    ans = models.augmentAPiIn.objects.get(apiID=int(one))
                    if ans:
                        str_list.append(ans.apiName)
                except:
                    print('id为' + one + '的api未找到')
        elif flag == 1:
            for one in id_list:
                ans = models.augmentPerIn.objects.get(id=int(one))
                if ans:
                    str_list.append(ans.perName)
                else:
                    print('id为' + one + '的permission未找到')
    return str_list


def api_map_per():
    """
    ：function： 匹配出KG上的api需要的permission
    """
    api_object = models.ApiTest.objects.values('apiName')
    api_list = dict_list(api_object, 1)  # 图谱上的所有api
    output_path = '/home/wuyang/Experiments/Datas/output/tools_mwep/api_map_per.txt'

    # 存放apk中有映射关系的api-per对
    api_per_file = 'detect/output/api_per.txt'
    file = open(api_per_file, 'r', encoding='utf-8', newline="")
    api_per = []  # 存放该api-per映射对
    for row in file.readlines():
        # print("line:"+line)
        line = row.strip()
        api_per.append(line)

    with open(output_path, "w", encoding='utf-8') as report:
        for api in api_list:
            for map in api_per:
                if map.find(api) != -1:
                    report.write(map + '\n')
                    break
            # report.write('调用' +api+ '不需要申请权限\n')


def apk_cg(apk_path):
    """
    :function 传入apk的路径，生成该apk的cg
    :param apk_path:str, 传入apk的路径
    """
    gml_file, apk_name = generate_cg(apk_path)
    txt_file = gml_txt(gml_file, apk_name)
    extract_features(txt_file, apk_name, apk_path)  # 提取特征,生成特征文件
    print('已经成功生成APK: ' + apk_name + ' 的CG文件，详见：' + txt_file)


def longest_substring():
    """
    :function 给定一个字符串，查找字符串上的重复项
    """
    print("longest\n")
    nodelist_path = '/home/wuyang/Experiments/Datas/output/tools_mwep/sample100_nodelist.txt'
    # 首先读取某个APK的特征文件
    file = open(nodelist_path, 'r', encoding='utf-8', newline="")
    s = ""  # 存放匹配上的节点，各个APK匹配上的节点之间直接用“+”连接
    for row in file.readlines():
        line = row.strip()
        if line != '':
            s = s + line + ','
    print('s:\n' + s)
    # r = re.compile(r"(.+?)\1+")
    # for match in r.finditer(re.sub(r'\s+', ",", s)):
    #     return (match.group(1), len(match.group(0)) / len(match.group(1)))
    # s=s.replace()
    dic, maxln, start_index = {}, 0, 0
    all_str = []
    for index, item in enumerate(s):
        if item in dic:  # 如果窗口中存在当前字符，则左边界向右移动
            start_index = max(start_index, dic[item] + 1)
        maxln = max(maxln, index - start_index + 1)  # 如果不存在，则扩大窗口
        windows = s[index + 1 - maxln:index + 1]  # 得到窗口中的子串
        all_str.append(windows)  # 记录所有子串到列表
        dic[item] = index
    # print("所有子窗口为%s" %all_str)
    unexpect_str = []
    for obj in all_str:
        for i in range(len(obj)):
            if obj.count(obj[i]) != 1 or len(obj) < maxln:
                unexpect_str.append(obj)
    for j in unexpect_str:
        if j in all_str:
            all_str.remove(j)
    final_result = set(all_str)
    print("最长无重复字符串为：%s" % final_result)
    print("最长无重复子串长度为:%s" % (maxln))


def find_link_num():
    """
    :function 找到每一个api与ApiSim数据表和ApiSDK数据表的链接
    """
    all_apis = []  # 存储ApiSim和APiSDK中出现的所有api
    # 先检查ApiSim数据表中的
    api_sim_table = ApiSim.objects.values()
    api_sim_table = list(api_sim_table)
    for one in api_sim_table:
        api_list = []
        apis = one['list']
        list_id = one['id']
        if apis.find(',') != -1:
            api_list = apis.split(',')
        else:
            api_list.append(apis)
        for api in api_list:
            # 去ApiTest数据表中查询
            api = api.replace(' ', '')
            all_apis.append(api)
            try:
                ans = models.ApiTest.objects.get(apiName=api)
                ans.addList = list_id
                ans.save()
            except:
                print('api:{} 在ApiTest数据表中缺失'.format(api))
                models.ApiTest.objects.create(apiName=api, addList=list_id)

    # 再检查ApiSDK数据表中的
    api_sdk_table = ApiSDK.objects.values()
    api_sdk_table = list(api_sdk_table)
    for one in api_sdk_table:
        api_list = []
        apis = one['list']
        list_id = one['id']
        if apis.find(',') != -1:
            api_list = apis.split(',')
        else:
            api_list.append(apis)
        for api in api_list:
            # 去ApiTest数据表中查询
            api = api.replace(' ', '')
            all_apis.append(api)
            try:
                ans = models.ApiTest.objects.get(apiName=api)
                ans.repList = list_id
                ans.save()
            except:
                print('api:{} 在ApiTest数据表中缺失'.format(api))
                models.ApiTest.objects.create(apiName=api, repList=list_id)

    # 清理ApiTest中错误的链接
    ans = models.ApiTest.objects.values('apiName')
    api_ans = dict_list(ans, 1)  # ApiTest上的所有api
    for api in api_ans:
        obj = models.ApiTest.objects.get(apiName=api)
        if api not in str(all_apis):
            obj.repList = ''
            obj.addList = ''
            obj.save()
        try:
            if int(obj.addList) > len(api_sim_table):
                obj.addList = ''
                obj.save()
        except:
            pass
        try:
            if int(obj.repList) > len(api_sdk_table):
                obj.repList = ''
                obj.save()
        except:
            pass
        if obj.apiID is None:
            obj.apiID = obj.id
            obj.save()
        # 顺便清理之前的NULL
        if obj.inLevel is None or obj.inLevel == '0':
            obj.inLevel = ''
            obj.save()
        if obj.outLevel is None or obj.outLevel == '0' or obj.outLevel == 0:
            obj.outLevel = ''
            obj.save()
