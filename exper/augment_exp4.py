import re
import random
import numpy as np
import json
import shutil
import time
import codecs  # 将ansi编码的文件转为utf-8编码的文件
import os
import django
import sys
from collections import Counter
# 排序
from operator import itemgetter
from itertools import groupby

sys.path.append('../')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mwep.settings')

django.setup()

from common import models
from django.db.models import Q


def read_match_report(path):
    """
    :function 读取APK与图谱匹配的输出结果
    :param path: 要读取文件内容的文件路径
    """
    file = open(path, 'r', encoding='utf-8')
    data = file.read()
    file.close()
    return data


def get_data(url):
    """
    :function 读取文件内容
    """
    f = open(url, "r", encoding='utf-8')
    data = f.read()
    f.close()
    return data


"""
step 1:
    1) 构建敏感api数据库（手工构建）
    2) 在已知节点匹配结果的前提下，依次查看节点的特征组成，查找敏感api；
"""


def get_sensitive_apis():
    """
    :function 构建敏感api的数据库，参考的susi，数据量较大（3万+）
    """
    apis_file_path = "/home/wuyang/Experiments/Datas/pscout/SuSi-develop/permissionMethodWithLabel.txt"
    apk_file = open(apis_file_path, 'r', encoding='utf-8', newline="")
    apis = []  # 存储所有的api
    permission = ''  # 当前API对应的权限
    for row in apk_file.readlines():
        line = row.strip()
        if line.find('Permission') != -1 and line.find('permission') != -1:  # 该行显示的是permission
            permission = line.split(':')[1]  # 提取出permission
            continue
        if line.find(' Callers') != -1:  # 该行显示的是上面的permission相关的API调用
            continue
        if line.find('<') != -1 and line.find('>') != -1:  # 该行显示的api，接下来对api进行处理
            class_api = line.split(':')[0].replace('<', '')  # 提取出api所属的class
            class_api = class_api.replace('.', '/')  # 转换成和数据库一致的格式
            name_api = line.split(':')[1].split('>')[0].split(' ')[2].split('(')[0]  # 提取出api的method name
            api = class_api.strip() + ';->' + name_api.strip()
            models.sensitiveApi.objects.create(api=api, permission=permission)


def get_sensitive_apis_mini():
    """
    :function 构建小体积的敏感API数据库，参考rule.json
    """
    models.sensitiveApiMini.objects.all().delete()  # 清空表中的数据

    apis_file_path = "/home/wuyang/Experiments/Datas/pscout/rules.json"
    with open(file=apis_file_path, mode='r') as f:
        data = json.load(f)  # 读取json文件，读取json文件的数据将被转换成python的数据格式
    # print(data)
    # print(type(data))
    for obj in data:  # 遍历
        # 读取字段
        api_list = obj['or_predicates']
        tags = obj['tags']
        title = obj['title']
        description = obj['description']
        be_name = obj['name']
        # 处理list中的API
        for one in api_list:
            if one.find('L') == 0:
                one = one.replace('L', '')
            c = one.count('/')
            method_name = one.split('/')[c]
            tmp = one.split('/')
            class_name = ''
            for s in tmp[0:c - 1]:
                class_name = class_name + s + '/'
            class_name = class_name[:-1]  # 切片，去掉最后多于的一个字符
            api = class_name + ';->' + method_name
            models.sensitiveApiMini.objects.create(api=api, tags=str(tags), title=title, description=description,
                                                   name=be_name)


def get_all_sensitive_api():
    """
    :function 从敏感api数据库中提取出所有的敏感api，以便后续判断
    """


def find_sensitive_api(match_nodes):
    """
    :function 根据匹配结果，依次查看节点的特征组成，查找敏感api
    :param match_nodes:该apk匹配上的路径的节点list（先考虑路径上的）,不应该为空
    :return node_apis:返回和每个节点相对应的敏感api的名称以及特征ID，[{kg node id, [{api id, api name}]}]
    """
    node_apis = []
    for node_id in match_nodes:
        sensitive_apis = []  # 敏感api的名称和在KG中的特征ID
        node_obj = models.augmentNodeIn.objects.get(id=str(node_id))
        # print('node id:', node_id)
        api_list = node_obj.apiList  # 不同节点可能会调用相同的api
        apis_list = []
        if api_list != '' and api_list != " ":
            # print('api_list:', api_list)
            if api_list.find(' ') != -1:
                api_list = api_list.replace(' ', '')
            if api_list.find(',') != -1:
                apis_list = api_list.split(',')
            else:
                apis_list.append(int(api_list))
            if len(apis_list) > 0:
                for api_id in apis_list:
                    api_name = models.augmentAPiIn.objects.get(apiID=int(api_id)).apiName
                    try:
                        judge = models.sensitiveApi.objects.get(api=api_name)
                        if judge:  # 能在敏感API数据库中找到该条API，说明该API是敏感的，和恶意行为强相关的
                            # sensitive_apis.append({'api_id': int(api_id), 'api_name': api_name})
                            sensitive_apis.append({'api_id': int(api_id), 'api_name': api_name})
                    except Exception as e:
                        # print("find_sensitive_api:" + api_name)
                        # print(e)
                        pass
                    # print('api_name:', api_name)
                if len(sensitive_apis) > 0:  # 只对那些存在敏感api的节点进行扩充
                    node_apis.append({'node_id': node_id, 'api_info': sensitive_apis})
    return node_apis


def joint_path(match_ans):
    """
    :function 将匹配到的片段路径连接起来，组合成完整的路径
    :param match_ans:匹配结果，如e.g.[[6, 57], [35, 56], [13, 57], [22, 57], [11, 35], [16, 57], [49, 6], [30, 49]]
    :return 连接后的路径，e.g. [[30, 49, 6, 57], [11, 35, 56], [13, 57], [22, 57], [16, 57]]
    """
    # print('match ans:', match_ans)
    path = []
    while len(match_ans) > 0:
        for one_path in match_ans:
            tmp = one_path  # [6,57]
            if len(match_ans) >= 2:
                for one in match_ans[1:]:
                    # print('one:', one)
                    if one[0] == one_path[-1] and one[-1] == one_path[0]:  # 循环，可以构成一个圈
                        tmp.append(one[1])
                        tmp.insert(0, one[0])
                        tmp = tmp[0:-1]
                        match_ans.remove(one)
                    elif one[0] == one_path[-1]:  # 当前路径的末节点是某条路径的首节点
                        tmp.append(one[1])
                        match_ans.remove(one)
                    elif one[-1] == one_path[0]:  # 当前路径的首节点是某条路径的末节点
                        tmp.insert(0, one[0])  # [49,6,57]
                        match_ans.remove(one)
            path.append(tmp)
            match_ans.remove(one_path)
    return path


def extract_node_from_path(match_ans):
    """
    :function 从匹配路径中提取出节点
    :param match_ans: 匹配路径的序列数组
    :return path_node: 从路径中提取出来的节点ID（int类型）
    """
    ret = []
    str_li = str(match_ans)
    if str_li.find(',') == -1:  # "[]"
        pass
    else:
        str_li = str_li.replace('[', '')
        str_li = str_li.replace(' ', '')
        str_li = str_li.replace(']', '')
        str_li = str_li.split(',')
        str_li = list(set(str_li))  # 删除重复元素
        for one in str_li:
            ret.append(int(one))
        ret.sort()
    return ret


"""
setp 2:
   1) 对于查找到的敏感api，逆向在CG中找到entrypoint为1的入口函数
"""


def do_feature_file(apk_name):
    """
    :function 处理特征文件，将同一入口函数中的api切分到一个数组元素中
    :param apk_name: 待处理apk的文件名
    return 切分后的数组
    """
    # ret = []
    # 处理特征文件
    feature_filename = os.path.join('../detect/output_features/', apk_name + '_features.txt')  # 存放apk的特征文件
    # print(feature_filename)
    feature_file = open(feature_filename, 'r', encoding='utf-8')
    data = feature_file.read()  # 读取文档内容
    data = data.split("entrypoint node id:")  # 切分，此时data数组的第一个元素为permissons
    feature_file.close()
    return data[1:]


def do_feature_file_v1(apk_name):
    """
    :function 读取特征文件
    :param apk_name: 待处理apk的文件名
    return 特征文件的内容
    """
    # ret = []
    # 处理特征文件
    feature_filename = os.path.join('../detect/output_features/', apk_name + '_features.txt')  # 存放apk的特征文件
    # print(feature_filename)
    feature_file = open(feature_filename, 'r', encoding='utf-8')
    data = feature_file.read()  # 读取文档内容
    feature_file.close()
    return data


def find_entrypoint(node_api, apk_name):
    """
    :function 查找入口函数，即寻找一个从当前知识图谱到CG的映射
    :param node_api: 每个节点的ID及其相对应的敏感api的名称以及特征ID
    :param apk_name: 该APK的名称
    :return 从KG到CG的映射,e.g. [{'kg_node': 13, 'cg_node': 2315}, {'kg_node': 22, 'cg_node': 2307}]
    """
    ret = []
    feature_file = do_feature_file_v1(apk_name)  # 读取特征文件的内容
    for node in node_api:
        node_id = node['node_id']  # int型，从这个节点进行扩充。注意：该节点来自于构建的知识图谱
        api_info = node['api_info']  # list，list元素为string，图谱节点中的敏感API
        entry_nodes = []  # 可能的entrypoint node
        if len(api_info) > 0:  # 可以从该节点进行扩充
            # print(node_id)
            for one in api_info:
                api_name = one['api_name']
                # 去特征文件中查看该特征在哪个函数中
                pattern = re.compile('entrypoint node id:.*?' + api_name, re.S)
                ans = pattern.findall(feature_file)
                if ans:
                    ans = ans[0].split('entrypoint node id:')[-1]
                    pattern1 = re.compile('(\d+)\n', re.S)
                    ans = pattern1.findall(ans)[0]
                    entry_nodes.append(int(ans))
                    # print('cg father function:', ans)
            if len(entry_nodes) > 0:
                cg_node = Counter(entry_nodes).most_common(1)
                cg_node = np.asarray(cg_node)[0][0]
                ret.append({'kg_node': node_id, 'cg_node': cg_node})
        else:
            continue  # 如果api_info为空，则直接跳出本次循环，继续下一个节点的扩充

    return ret


def do_cg_file(apk_name):
    """
    :function 同 do_feature_file(apk_name)
    ：param apk_name: 当前apk的名称
    """
    # 处理CG文件
    cg_filename = os.path.join('../detect/outputCG/', apk_name + '.txt')  # 存放apk的CG文件
    cg_file = open(cg_filename, 'r', encoding='utf-8')
    data = cg_file.read()  # 读取文档内容
    cg_edge_list = data.split("edge ", 1)[1:]  # 切去node pair部分
    cg_node_list = data.split("edge ", 1)[0]  # 切去edge pair部分
    cg_file.close()
    return cg_edge_list, cg_node_list, data


def find_parent_point(entrypoint_ans, apk_name):
    """
    :function 通过CG中的Edge pair发现与当前入口函数相关的入口函数，其实就是找当前函数的父函数
    :param entrypoint_ans: find_entrypoint函数的返回结果，即KG节点和CG节点的映射
    :param apk_name: 当前apk的名称
    :return [{kg node id, map cg node id, map cg function, source node ids, cg source id, map source cg function},...]
    """
    cg_edge_part, cg_node_list, data = do_cg_file(apk_name)  # 打开当前apk的cg文件
    all_source_id = []  # 所有节点匹配上的source node id
    all_node_source_info = []  # 存储kg node id以及cg source node id
    data = data.replace('\n', '')
    for ans in entrypoint_ans:
        kg_node = ans['kg_node']
        cg_node = ans['cg_node']
        source_id_list = []  # 当前节点匹配上的source node id
        pattern2 = re.compile('source\s*' + '\d+\s*target ' + str(cg_node), re.S)  # 匹配以该节点为target的source node id
        search_ans2 = pattern2.findall(data)
        if search_ans2:
            # 提取出source node id
            for one in search_ans2:
                source_id = re.findall('\s(\d*)', one)[0]  # int
                source_id_list.append(int(source_id))
                all_source_id.append(int(source_id))
            pattern4 = re.compile('id\s' + str(cg_node) + '\s*label\s"(.*?)\s\[access_flags', re.S)
            cg_node_function = pattern4.findall(data)[0].strip()
            all_node_source_info.append({'kg_node': kg_node, 'cg_node': cg_node, 'cg_node_function': cg_node_function,
                                         'cg_source_node': source_id_list})
    # 对统计所有source node id出现的次数并排序
    if len(all_source_id) > 0:
        source_node_common = Counter(all_source_id).most_common(3)
        most_common_node = np.asarray(source_node_common)[0][0]  # 正则匹配次数最多的节点node
        most_common_node_times = np.asarray(source_node_common)[0][1]  # 正则匹配次数最多的次数
        if most_common_node_times == len(all_node_source_info):  # 恰好所有当前cg节点都有相同的source node，除开search_ans2为空的kg node
            # 在cg中查找该node，提取出入口函数
            pattern3 = re.compile('id\s' + str(most_common_node) + '\s*label\s"(.*?)\s\[access_flags', re.S)
            search_ans3 = pattern3.findall(data)
            print('search_ans3:', search_ans3)
            for one in all_node_source_info:
                one['cg_source_node_id'] = most_common_node
                one['cg_source_function'] = search_ans3[0].strip()

        else:  # 有的节点可以直接用出现次数最多（众数）的节点向上溯源，而有的节点需要根据自身的情况单独向上溯源
            most_common_nodes = np.asarray(source_node_common)[:, 0]  # 获取那些出现次数较多的节点id
            for one in all_node_source_info:
                cg_source_node = one['cg_source_node']
                intersection = list(set(cg_source_node) & set(most_common_nodes))
                if intersection:  # 有的节点可以直接用出现次数最多（众数）的节点向上溯源
                    for node in most_common_nodes:
                        if node in cg_source_node:
                            pattern5 = re.compile('id\s' + str(node) + '\s*label\s"(.*?)\s\[access_flags', re.S)
                            # print('search_ans3:', search_ans3)
                            function = pattern5.findall(data)[0].strip()
                            # print('function1:', function)
                            if function:
                                one['cg_source_node_id'] = node
                                one['cg_source_function'] = function
                                break
                    continue
                else:  # 需要根据自身的情况单独向上溯源
                    location = random.randint(0, len(cg_source_node) - 1)  # 随机选定向上溯源的节点
                    cg_source_node_id = cg_source_node[location]
                    pattern5 = re.compile('id\s' + str(cg_source_node_id) + '\s*label\s"(.*?)\s\[access_flags', re.S)
                    function = pattern5.findall(data)[0].strip()
                    # print('function2:', function)
                    if function:
                        one['cg_source_node_id'] = cg_source_node_id
                        one['cg_source_function'] = function
    return all_node_source_info


def create_cfg(apk_name, function_name, apks_location):
    """
    :function 生成cfg文件，限制函数名（相比于先生成整个apk的cfg文件再查找ag文件而言，这种方法更节省时间）
    :param function_name: 限制的函数名（好像不用限制，因为有的也限制不了，加上需要多次生成，不如一次性生成整个apk的）
    :param apk_name: apk文件名
    :param apks_location: apks存放的路径
    """
    copy_location = '../detect/output_augment/processing/'
    folder = copy_location + apk_name
    if os.path.exists(folder):
        os.makedirs(folder)
    else:
        print('the folder exists!')
    apk = os.path.join(apks_location, apk_name + '.apk')  # 带完整路径和后缀的apk文件，形如D:/input/apk01.apk
    # 复制文件到../detect/output_augment/processing/xx中
    folder = folder + '/'
    file = os.path.split(apk)[1]
    shutil.copy(apk, folder + file)
    copy_apk = os.path.join(folder, file)

    cmd = 'androguard decompile -o ' + folder + ' -f png -i ' + copy_apk + ' --limit ' + '"' + function_name + '"'
    os.system(cmd)


def create_cfg_v1(apk_name, apks_location):
    """
    :function 生成cfg文件，限制函数名（相比于先生成整个apk的cfg文件再查找ag文件而言，这种方法更节省时间）
    :param apk_name: apk文件名
    :param apks_location: apks存放的路径
    """
    copy_location = '../detect/output_augment/processing/'
    folder = copy_location + apk_name
    if not os.path.exists(folder):
        os.makedirs(folder)
    else:
        print('the folder exists!')
    apk = os.path.join(apks_location, apk_name + '.apk')  # 带完整路径和后缀的apk文件，形如D:/input/apk01.apk
    # 复制文件到../detect/output_augment/processing/中
    folder = folder + '/'
    file = os.path.split(apk)[1]
    shutil.copy(apk, folder + file)
    copy_apk = os.path.join(folder, file)

    cmd = 'androguard decompile -o ' + folder + ' -i ' + copy_apk
    os.system(cmd)


def get_file_name(function):
    """
    :function 传入完整的函数，应该完整，即带有函数参数类型和返回值类型，
    例如对于函数：Lnet/miidi/credit/a/a/a;->a(Ljava/lang/String;)Landroid/graphics/Bitmap;
    若想找准确地找到它的cfg文件，它的cfg文件名为a a (String)Bitmap，即父文件夹 函数名 (参数类型)返回值类型
    """
    father = function.split(';', 1)[0].split('/')[-1]  # =a
    function_name = re.findall('->(.*?)\(', function)[0]
    call_param = re.findall('\((.*)\)', function)[0].replace(" ", '')
    ca = ''
    if len(call_param) > 0:  # 该函数需要调用参数，一个函数可能调用多个参数
        if call_param.find(';') != -1:
            call_param = call_param.split(';')
            for one in call_param:
                if one.find('/') != -1:
                    tmp = one.split('/')[-1]
                    ca = ca + tmp + ' '
                else:
                    ca = ca + one + ''
            call_param = ca.strip()  # =String
        else:
            if call_param.find('/') != -1:
                call_param = call_param.split('/')[-1]
            else:
                pass
    else:
        call_param = ''
    ret_param = function.split(')')[-1]
    if len(ret_param) > 0:
        if ret_param.find('/') != -1:  # =Bitmap
            ret_param = ret_param.split('/')[-1]
            if ret_param.find(';') != -1:
                ret_param = ret_param.replace(';', '')  # Bitmap
        elif ret_param.find(';') != -1:
            ret_param = ret_param.replace(';', '')
        else:
            pass
    else:
        ret_param = ''
    if function_name == '<init>':
        ag_file_name = father + '_init' + '_(' + call_param + ')' + ret_param
    else:
        ag_file_name = father + ' ' + function_name + ' (' + call_param + ')' + ret_param
    return ag_file_name


def ag_txt(base_location, file_location, function):
    """
    :function 将cfg的ag文件修改成txt类型，方便后续读取
    :param base_location: 扔进apk文件并在该文件夹下执行androguard命令
    :param file_location: 函数所在的项目文件路径
    :param function: 执行cfg的函数,应该完整，即带有函数参数类型和返回值类型，
    例如对于函数：Lnet/miidi/credit/a/a/a;->a(Ljava/lang/String;)Landroid/graphics/Bitmap;
    若想找准确地找到它的cfg文件，它的cfg文件名为a a (String)Bitmap，即父文件夹 函数名 (参数类型)返回值类型
    :return cfg的txt文件
    """
    # print("param function：", function)
    if file_location[0] == 'L':  # ag文件的位置（也是classname）往往以L开头，但是androguard decompile后的文件路径是没有L的
        file_location = file_location[1:]
    ag_path = os.path.join(base_location, file_location + '/')
    ag_file_name = get_file_name(function)
    # 如果能直接找到ag的txt文件，则直接返回不需要重命名；否则重命名后返回
    txt_file = ag_path + ag_file_name + '.txt'  # 给ag文件取新的名字，保持文件位置不变
    if os.path.exists(txt_file):
        # print('已经存在')
        return txt_file
    else:
        # print('ag_file_name:', ag_file_name)
        # print('ag_path:', ag_path)
        ag_file = ag_path + ag_file_name + '.ag'
        # ag_file = glob.glob(ag_path + ag_file_name + '.ag') # ag文件，精确到文件名
        # print('ag_file:', ag_file)
        if os.path.exists(ag_file):
            os.rename(ag_file, txt_file)
            # print('txt_file', txt_file)
            return txt_file
        else:  # 如果ag文件不存在，直接返回None
            return None


def get_location_name(cg_function):
    """
    :function 根据函数的详细完整信息切分出ag文件应该在的文件位置、生成cfg时需要限制的函数名称
    :param cg_function: 函数的完整信息，e.g.Ljava/io/PrintStream;->println(Ljava/lang/String;)V
    """
    file_location = cg_function.split(';')[0]  # 该函数ag文件的位置，e.g.Lcom/bbcc/eeff/App$1
    function_name = cg_function.split('>')[1].split('(')[0]  # 只是简单的名称
    if file_location[0] == 'L':  # ag文件的位置（也是classname）往往以L开头，但是androguard decompile后的文件路径是没有L的
        file_location = file_location[1:]
    return file_location, function_name


def find_down_entrypoint(all_node_source_info, apk_name, base_location, apks_location):
    """
    :function 寻找和当前kg node可能扩展的入口函数
    :param all_node_source_info: find_parent_point函数的输出
    :param apk_name: 当前apk的名称
    :param base_location: 处理cfg文件夹
    :param apks_location: 存放apk的文件夹
    """
    # 生成cfg，然后根据file location去相应的位置找cg文件
    start = time.time()
    create_cfg_v1(apk_name, apks_location)
    end = time.time()
    print('CFG执行时间为：', end - start)

    all_node_source_info_end = []
    exist_fun = []
    for info in all_node_source_info:
        exist_fun.append(info['cg_node_function'])  # 代表着kg上已有的节点
    for info in all_node_source_info:
        ret = info
        cg_source_function = info['cg_source_function']
        cg_current_function = info['cg_node_function']
        cfg_down_function = []  # cfg中，当前函数可能的下位函数
        cfg_down_function_ret = []  # cfg中，当前函数可能的下位函数
        file_location = cg_source_function.split(';')[0]  # 该函数ag文件的位置，e.g.Lcom/bbcc/eeff/App$1
        function_name = cg_source_function.split('>')[1].split('(')[0]
        # # 使用function name生成cfg，然后根据file location去相应的位置找cg文件
        # create_cfg(apk_name, function_name, apks_location)
        # 将cfg的某个函数的ag文件修改成txt类型，方便后续读取
        cfg_file = ag_txt(base_location, file_location, cg_source_function)
        # 读取cfg文件
        # print('cfg_file:', cfg_file)
        if cfg_file is not None:  # cfg文件存在
            if os.path.exists(cfg_file):
                cfg_file = open(cfg_file, 'r', encoding='utf-8', newline="")
                flag = 0
                for row in cfg_file.readlines():
                    if row.find(cg_current_function) != -1:  # 为了保障从特定行开始处理文件
                        flag = 1  # 找到开始扩展的位置，是kg上的节点映射到该apk中的某个函数
                        # 记录当前函数的行号（也即调用的顺序编号），以处理那些来自同一个源入口函数的函数的顺序，和节点的扩展路径相关
                        pattern7 = re.compile('\s*(\d*)\s*?\(', re.S)
                        location = pattern7.findall(row)[0]
                        info['cg_node_function_num'] = int(location)
                        ret['cg_node_function_num'] = int(location)
                        # cfg_down_function_ret.append({'fun': cg_current_function, 'num': int(location)})
                        continue
                    if flag == 0:
                        continue
                    else:
                        if row.find('invoke-virtual') != -1 or row.find('invoke-static') != -1:  # 只处理invoke类型的语句
                            pattern6 = re.compile('(L.*)?\n', re.S)
                            fun = pattern6.findall(row)[0]
                            pattern7 = re.compile('\s*(\d*)\s*?\(', re.S)
                            location = pattern7.findall(row)[0]
                            if fun not in exist_fun and fun[0:5] != 'Ljava' and fun[0:9] != 'Landroidx' and fun[
                                                                                                            0:8] != 'Landroid':  # 考虑利用这些函数挖掘新的节点
                                # fun为可能的扩展函数
                                cfg_down_function.append({'fun': fun, 'num': int(location)})
                                cfg_down_function_ret.append({'fun': fun, 'num': int(location)})
                info['cfg_down_function'] = cfg_down_function
                ret['cfg_down_function'] = cfg_down_function_ret
                if len(cfg_down_function_ret) > 0:
                    all_node_source_info_end.append(ret)
        else:  # 当前函数的cfg文件不存在，说明找的父函数不靠谱
            print('不存在:', cg_source_function)
            info['cfg_down_function'] = cfg_down_function  # cfg_down_function为[]
    return all_node_source_info, all_node_source_info_end


"""
step 3:
   1) 对于查找到的下位函数，生成该函数的CFG，从中抽取敏感API
   2) 将抽取出来的敏感API作为新节点的特征（所需Permission另外获取）
"""


def get_api2per_db():
    """
    :function 构建 api--permission 数据库，即调用一个API时需要申请的权限
    """
    # 先清空数据表内容
    models.apiRequsetPer.objects.all().delete()

    tmp_list = []
    api_per_file_path = '../detect/output/api_per.txt'
    file = open(api_per_file_path, 'r', encoding='utf-8', newline="")
    for row in file.readlines():
        line = row.strip()
        tmp_list.append(line)
    tmp_list = list(set(tmp_list))  # 删除重复的
    for one in tmp_list:
        api = one.split('(')[0]
        if api[0] == 'L':
            api = api[1:]
        per = re.findall(":\s\[(.*?)]", one)[0]  # 需要申请的权限可能有多个
        # print(per)
        per = per.replace("'", '').replace(" ", '')
        if models.apiRequsetPer.objects.filter(Q(api=api) & Q(per=per)):
            pass
        else:
            count = len(list(models.apiRequsetPer.objects.values()))
            models.apiRequsetPer.objects.create(api=api, per=per)
            models.apiRequsetPer.objects.filter(Q(api=api) & Q(per=per)).update(id=count + 1)  # 设置node ID的值


def extract_sensitive_api_from_fun(txt_cfg, function_name):
    """
    :function 给定一个函数的cfg文件，从中抽取敏感API（前提是该cfg文件存在）
    :param txt_cfg: txt格式的cfg文件
    :param function_name: 新节点的第1版名称，直接用函数的简单命名给新的节点命名
    """
    new_node = {}
    apis = []  # 该节点的特征api
    pers = []  # 该节点的特征permission
    if txt_cfg is not None and os.path.exists(txt_cfg):  # cfg文件存在
        cfg_file = open(txt_cfg, 'r', encoding='utf-8', newline="")
        for row in cfg_file.readlines():
            if row.find('invoke-virtual') != -1 or row.find('invoke-static') != -1 or row.find('sget-object')!=-1:  # 只处理invoke类型的语句
                pattern6 = re.compile('(L.*)?\n', re.S)
                fun = pattern6.findall(row)[0]
                if fun.find('(')!=-1:
                    fun1 = fun.split('(')[0][1:]
                else:
                    fun1=fun.split(' ')[0][1:]
                # 判断该api是否为敏感api，现在小数据库中查找，若没有再去大数据库中找
                try:
                    ans = models.sensitiveApiMini.objects.get(api=fun1)
                    if ans:
                        if fun1 not in apis:
                            apis.append(fun1)
                            # 查询调用该api是否需要申请权限
                            try:
                                q = models.apiRequsetPer.objects.get(api=fun1)
                                if q:
                                    permissions = q.per
                                    if permissions.find(',') != -1:
                                        li = permissions.split(',')
                                        for one in li:
                                            pers.append(one)
                                    else:
                                        pers.append(q.per)
                            except Exception as e:
                                # print(e)
                                pass
                    else:
                        # try:
                        ans1 = models.sensitiveApi.objects.get(api=fun1)
                        if ans1:
                            if fun1 not in apis:
                                apis.append(fun1)
                                # 查询调用该api是否需要申请权限
                                try:
                                    q = models.apiRequsetPer.objects.get(api=fun1)
                                    if q:
                                        permissions = q.per
                                        if permissions.find(',') != -1:
                                            li = permissions.split(',')
                                            for one in li:
                                                pers.append(one)
                                        else:
                                            pers.append(q.per)
                                except Exception as e:
                                    # print(e)
                                    pass
                        # except Exception as e:
                        #     print(e)
                except Exception as e:
                    pass
        if len(apis) > 0:  # 能够在该函数的cfg中找到敏感api，这些敏感API能较好地表征一个行为
            new_node['node_name'] = function_name  # 给函数命名
            new_node['apis'] = apis
            new_node['pers'] = pers
            return new_node
    else:  # cfg文件不存在
        return None


def extract_sensitive_api_from_fun_v2(txt_cfg, function_name):
    """
    :function 给定一个函数的cfg文件，从中抽取敏感API（前提是该cfg文件存在）
    :Tips: 因为只提取敏感API的花，挖掘到的节点较少，因此考虑纳入常规API
    :param txt_cfg: txt格式的cfg文件
    :param function_name: 新节点的第1版名称，直接用函数的简单命名给新的节点命名
    """
    # print('txt_cfg:', txt_cfg)
    new_node = {}
    apis = []  # 该节点的特征api
    pers = []  # 该节点的特征permission
    if txt_cfg is not None and os.path.exists(txt_cfg):  # cfg文件存在
        cfg_file = open(txt_cfg, 'r', encoding='utf-8', newline="")
        for row in cfg_file.readlines():
            if row.find('invoke-virtual') != -1 or row.find('invoke-static') != -1 or row.find('sget-object')!=-1:  # 只处理invoke类型的语句
                pattern6 = re.compile('(L.*)?\n', re.S)
                fun = pattern6.findall(row)[0]
                if fun.find('(') != -1:
                    fun1 = fun.split('(')[0][1:]
                else:
                    fun1 = fun.split(' ')[0][1:]
                # 判断该api是否为敏感api，现在小数据库中查找，若没有再去大数据库中找
                try:
                    ans = models.sensitiveApiMini.objects.get(api=fun1)
                    if ans:
                        if fun1 not in apis:
                            apis.append(fun1)
                            # 查询调用该api是否需要申请权限
                            try:
                                q = models.apiRequsetPer.objects.get(api=fun1)
                                if q:
                                    permissions = q.per
                                    if permissions.find(',') != -1:
                                        li = permissions.split(',')
                                        for one in li:
                                            pers.append(one)
                                    else:
                                        pers.append(q.per)
                            except Exception as e:
                                # print(e)
                                pass
                    else:
                        # try:
                        ans1 = models.sensitiveApi.objects.get(api=fun1)
                        if ans1:
                            if fun1 not in apis:
                                apis.append(fun1)
                                # 查询调用该api是否需要申请权限
                                try:
                                    q = models.apiRequsetPer.objects.get(api=fun1)
                                    if q:
                                        permissions = q.per
                                        if permissions.find(',') != -1:
                                            li = permissions.split(',')
                                            for one in li:
                                                pers.append(one)
                                        else:
                                            pers.append(q.per)
                                except Exception as e:
                                    # print(e)
                                    pass
                except Exception as e:
                    pass
        cfg_file.close()
        if len(apis) > 0:  # 能够在该函数的cfg中找到敏感api，这些敏感API能较好地表征一个行为
            print('找到敏感API')
            new_node['node_name'] = function_name  # 给函数命名
            new_node['apis'] = apis
            new_node['pers'] = pers
            new_node['mark'] = ''
            return new_node
        else:  # 找不到敏感API，因此退而求其次，寻找常规API
            # print('未找到敏感API')
            apis = []  # 该节点的特征api
            pers = []  # 该节点的特征permission
            cfg_file = open(txt_cfg, 'r', encoding='utf-8', newline="")
            for row in cfg_file.readlines():
                if row.find('invoke-virtual') != -1 or row.find('invoke-static') != -1:  # 只处理invoke类型的语句
                    pattern6 = re.compile('(L.*)?\n', re.S)
                    fun = pattern6.findall(row)[0]
                    # print('fun:',fun)
                    if fun[0:5] == 'Ljava' or fun[0:9] == 'Landroidx' or fun[0:8] == 'Landroid':  # 潜在的API
                        fun1 = fun.split('(')[0][1:]
                        if fun1 != 'java/lang/Exception;->printStackTrace' and fun1 not in apis:
                            apis.append(fun1)
                        # 查询调用该api是否需要申请权限
                        try:
                            q = models.apiRequsetPer.objects.get(api=fun1)
                            if q:
                                permissions = q.per
                                if permissions.find(',') != -1:
                                    li = permissions.split(',')
                                    for one in li:
                                        pers.append(one)
                                else:
                                    pers.append(q.per)
                        except Exception as e:
                            # print(e)
                            pass
            if len(apis) > 3:  # 能够在该函数中找到常规API
                # print('找到常规API')
                new_node['node_name'] = function_name  # 给函数命名
                new_node['apis'] = apis
                new_node['pers'] = pers
                new_node['mark'] = '*'
                return new_node
            else:
                return {}
            cfg_file.close()
    else:  # cfg文件不存在
        return None


def augment_new_node(all_node_source_info, apk_name, base_location, apks_location):
    """
    :function 根据all_node_source_info挖掘新的节点
    """
    augment_nodes = []
    for info in all_node_source_info:
        kg_node = info['kg_node']
        cg_node_function = info['cg_node_function']
        cfg_down_functions = info['cfg_down_function']
        father_cfg_function = info['cg_source_function']  # 当前节点对应入口函数的父函数
        if len(cfg_down_functions) > 0:  # 当cfg存在时，
            cfg_function_num = info['cg_node_function_num']  # 当前节点对应的入口函数在父函数中的调用序号
            new_nodes = []
            for one in cfg_down_functions:
                f = one['fun']
                num = one['num']
                file_location, function_name = get_location_name(f)
                # 生成cfg
                # create_cfg(apk_name, function_name, apks_location)
                # 将ag文件变成txt文件
                cfg_file = ag_txt(base_location, file_location, f)
                if cfg_file is not None and os.path.exists(cfg_file):
                    new_node = extract_sensitive_api_from_fun(cfg_file, function_name)
                    if new_node is not None:
                        new_node['cfg_function_num'] = num
                        new_node['father_cfg_function'] = f
                        if new_node not in new_nodes:
                            new_nodes.append(new_node)
                # print('fun:',fun)
            augment_nodes.append(
                {'source_kg_node': kg_node, 'cg_node_function': cg_node_function, 'cfg_function_num': cfg_function_num,
                 'father_cfg_function': father_cfg_function, 'target_kg_nodes': new_nodes})
        else:
            continue
    return augment_nodes


def augment_new_node_v1(all_node_source_info, base_location):
    """
    :function 根据all_node_source_info挖掘新的节点
    :param all_node_source_info: 至此的信息
    :param base_location: 处理cfg的文件夹路径
    """
    augment_nodes = []
    for info in all_node_source_info:
        kg_node = info['kg_node']
        cg_node_function = info['cg_node_function']
        cfg_down_functions = info['cfg_down_function']
        cfg_father_function = info['cg_source_function']  # 当前节点对应入口函数的父函数
        if len(cfg_down_functions) > 0:  # 当cfg存在时，
            cfg_function_num = info['cg_node_function_num']  # 当前节点对应的入口函数在父函数中的调用序号
            new_nodes = []
            for one in cfg_down_functions:
                f = one['fun']
                num = one['num']
                file_location, function_name = get_location_name(f)

                # 将ag文件变成txt文件
                cfg_file = ag_txt(base_location, file_location, f)
                if cfg_file is not None and os.path.exists(cfg_file):
                    new_node = extract_sensitive_api_from_fun_v2(cfg_file, function_name)
                    print('new_node xixi:', new_node)
                    if new_node is not None and new_node != []:
                        new_node['cfg_function_num'] = num
                        new_node['cfg_father_function'] = f
                        if new_node not in new_nodes:
                            new_nodes.append(new_node)
            if len(new_nodes) > 0:
                augment_nodes.append(
                    {'kg_node': kg_node, 'cg_node_function': cg_node_function, 'cfg_function_num': cfg_function_num,
                     'cfg_father_function': cfg_father_function, 'target_kg_nodes': new_nodes})
        else:
            continue
    return augment_nodes


def augment_new_node_v2(all_node_source_info, base_location):
    """
    :function 根据all_node_source_info挖掘新的节点
    1. 之前是回到父函数，然后在父函数中寻找下一个子函数，而忽略了父函数中可能存在的敏感API或常规API
    2.因为按照之前设计的，只提取敏感api的话，挖掘的新节点很少，因此加入常规API
    :param all_node_source_info: 至此的信息
    :param base_location: 处理cfg的文件夹路径
    """
    augment_nodes = []
    for info in all_node_source_info:
        kg_node = info['kg_node']
        cg_node_function = info['cg_node_function']
        cfg_down_functions = info['cfg_down_function']
        cfg_father_function = info['cg_source_function']  # 当前节点对应入口函数的父函数
        # 查看下位函数中是否有新的节点
        if len(cfg_down_functions) > 0:  # 当cfg存在时，
            cfg_function_num = info['cg_node_function_num']  # 当前节点对应的入口函数在父函数中的调用序号
            new_nodes = []
            for one in cfg_down_functions:
                f = one['fun']
                num = one['num']
                if num == cfg_function_num:
                    continue
                else:
                    file_location, function_name = get_location_name(f)
                    # 将ag文件变成txt文件
                    cfg_file = ag_txt(base_location, file_location, f)
                    if cfg_file is not None and os.path.exists(cfg_file):
                        new_node = extract_sensitive_api_from_fun_v2(cfg_file, function_name)
                        if new_node is not None:
                            new_node['cfg_function_num'] = num
                            new_node['cfg_father_function'] = f
                            if new_node not in new_nodes:
                                new_nodes.append(new_node)
            if len(new_nodes) > 0:
                augment_nodes.append(
                    {'kg_node': kg_node, 'cg_node_function': cg_node_function, 'cfg_function_num': cfg_function_num,
                     'cfg_father_function': cfg_father_function, 'target_kg_nodes': new_nodes})
        else:
            continue
    return augment_nodes


def augment_from_father_node_v2(all_node_source_info, base_location):
    """
    :function 根据all_node_source_info挖掘新的节点
    1. 之前是回到父函数，然后在父函数中寻找下一个子函数，而忽略了父函数中可能存在的敏感API或常规API
    2.因为按照之前设计的，只提取敏感api的话，挖掘的新节点很少，因此加入常规API
    :param all_node_source_info: 至此的信息
    :param base_location: 处理cfg的文件夹路径
    """
    augment_nodes = []
    for info in all_node_source_info:
        kg_node = info['kg_node']
        cg_node_function = info['cg_node_function']
        cfg_down_functions = info['cfg_down_function']
        cfg_father_function = info['cg_source_function']  # 当前节点对应入口函数的父函数
        # 查看下位函数中是否有新的节点
        if len(cfg_down_functions) > 0:  # 当cfg存在时，
            cfg_function_num = info['cg_node_function_num']  # 当前节点对应的入口函数在父函数中的调用序号
            new_nodes = []
            for one in cfg_down_functions:
                f = one['fun']
                num = one['num']
                if num == cfg_function_num:
                    continue
                else:
                    file_location, function_name = get_location_name(f)
                    # 将ag文件变成txt文件
                    cfg_file = ag_txt(base_location, file_location, f)
                    if cfg_file is not None and os.path.exists(cfg_file):
                        new_node = extract_sensitive_api_from_fun_v2(cfg_file, function_name)
                        if new_node is not None:
                            new_node['cfg_function_num'] = num
                            new_node['cfg_father_function'] = f
                            if new_node not in new_nodes:
                                new_nodes.append(new_node)
            if len(new_nodes) > 0:
                augment_nodes.append(
                    {'kg_node': kg_node, 'cg_node_function': cg_node_function, 'cfg_function_num': cfg_function_num,
                     'cfg_father_function': cfg_father_function, 'target_kg_nodes': new_nodes})
        else:
            continue
    return augment_nodes


"""
setp 4:
   1) 将新的节点加入到已有图谱中
"""


def copy_kg_db():
    """
    :function 复制有关知识图谱的两张数据表（节点表和关系表）到备用数据表中
    """
    models.augmenTestNode.objects.all().delete()
    models.augmenTestRel.objects.all().delete()
    models.augmenTestAPi.objects.all().delete()
    models.augmenTestPer.objects.all().delete()

    nodes = list(models.augmenTestNode.objects.values())
    a = 0
    for one in nodes:
        a = a + 1
        models.augmenTestNode.objects.create(nodeID=one['nodeID'], actionName=one['actionName'], perList=one['perList'],
                                             apiList=one['apiList'])
        models.augmenTestNode.objects.filter(nodeID=one['nodeID']).update(id=a)  # 设置node ID的值

    rels = list(models.augmenTestRel.objects.values())
    b = 0
    for one in rels:
        # current_id = one['id']  # 1093
        # print('current_id:', current_id)
        b = b + 1
        models.augmenTestRel.objects.create(sourceID=one['sourceID'], sourceAct=one['sourceAct'],
                                            targetID=one['targetID'], targetAct=one['targetAct'],
                                            relation=one['relation'])
        try:
            models.augmenTestRel.objects.filter(Q(sourceID=one['sourceID']) & Q(targetID=one['targetID'])).update(id=b)
        except Exception as e:
            print(copy_kg_db)
            print(e)
            # print(str(one['sourceID'])+str(one['targetID']))

    # 以及api和permission表
    apis = list(models.augmenTestAPi.objects.values())
    for one in apis:
        c = one['apiID']
        models.augmenTestAPi.objects.create(apiID=one['apiID'], apiName=one['apiName'], inLevel=one['inLevel'],
                                            outLevel=one['outLevel'], addList=one['addList'], repList=one['repList'])
        models.augmenTestAPi.objects.filter(apiID=one['apiID']).update(id=c)

    pers = list(models.PerTest.objects.values())
    d = 0
    for one in pers:
        d = d + 1
        models.augmenTestPer.objects.create(perID=one['perID'], perName=one['perName'], inLevel=one['inLevel'],
                                            outLevel=one['outLevel'])
        models.augmenTestPer.objects.filter(perID=one['perID']).update(id=d)


def key_sort_group(data):
    """
    :function 对列表中dict数据指定key排序，分组
    :param data: 待处理的字典list
    """
    result = dict()
    for cfg_father_function, items in groupby(data, key=itemgetter('cfg_father_function')):  # 将父函数相同的分为一组
        result[str(cfg_father_function)] = list(items)
    return result


def augment_new_kg(augment_nodes):
    """
    :function 分析的可扩展节点信息，将新的节点加入到知识图谱中
    :param augment_nodes: 函数augment_new_node的返回值
    """
    new_path = []
    if len(augment_nodes) > 0:
        ret = key_sort_group(augment_nodes)
        for key, value in ret.items():  # 按照父函数排序后的结果
            father = key
            value_list = value
            value_list.sort(key=itemgetter('cfg_function_num'))  # cfg_function_num排序；无返回值
            # 开始添加新的路径和节点
            path = []
            judge = []
            for one in value_list:
                source_kg_node = one['kg_node']  # 从该节点出发，是KG中真实存在的node id
                cg_node_function = one['cg_node_function']
                cfg_function_num = one['cfg_function_num']
                judge.append({'cfg_function_num': cfg_function_num, 'cg_node_function': cg_node_function,
                              'kg_node': source_kg_node})
                target_kg_nodes = one['target_kg_nodes']  # 发现的新的节点，是字典型list
                # print('target_kg_nodes:', target_kg_nodes)
                for new in target_kg_nodes:
                    if 'node_name' in new:
                        # 新的节点
                        judge.append(
                            {'cfg_function_num': new['cfg_function_num'],
                             'cg_node_function': new['cfg_father_function'],
                             'kg_node': 0, 'node_name': new['node_name'], 'apis': new['apis'], 'pers': new['pers'],
                             'mark': new['mark']})
            judge.sort(key=itemgetter('cfg_function_num'))
            # print('judge:', judge)
            # 向数据库中添加新的节点
            for one in judge:
                source_kg_node = one['kg_node']
                if source_kg_node == 0:  # 说明在原数据库中不存在，因此需要先添加
                    # 添加新的api和permission
                    per_list = ''
                    api_list = ''
                    pers = one['pers']
                    apis = one['apis']
                    if len(pers) > 0:
                        for per in pers:
                            try:
                                per_ans = models.augmentPerIn.objects.get(perName=per)
                                if per_ans:
                                    per_list = per_list + str(per_ans.perID) + ','
                            except Exception as e:  # 现有数据库中没有这条权限
                                print('查询per id失败：', per)
                                now_len = len(list(models.augmentPerIn.objects.values()))
                                models.augmentPerIn.objects.create(perName=per, perID=now_len + 1)
                                per_ans = models.augmentPerIn.objects.get(perName=per)
                                ans_id = per_ans.perID
                                models.augmenTestPer.objects.filter(perID=ans_id).update(id=ans_id)  # 设置node ID的值
                        per_list = per_list.strip(',')  # 删去最后一个字符
                    if len(apis) > 0:
                        for api in apis:
                            try:
                                api_ans = models.augmentAPiIn.objects.get(apiName=api.strip())
                                if api_ans:
                                    api_list = api_list + str(api_ans.apiID) + ','
                            except Exception as e:  # 现有数据库中没有这条API
                                # print('查询api id失败：', api)
                                now_len = len(list(models.augmentAPiIn.objects.values())) + 6  # 因为之前删除过一些API
                                models.augmentAPiIn.objects.create(apiName=api, apiID=now_len + 1)
                                api_ans = models.augmentAPiIn.objects.get(apiName=api)
                                ans_id = api_ans.apiID
                                models.augmentAPiIn.objects.filter(apiID=ans_id).update(id=ans_id)  # 设置node ID的值
                                api_list = api_list + str(ans_id) + ','
                        api_list = api_list.strip(',')  # 删去最后一个字符

                    node_name = one['node_name']
                    if len(node_name) <= 5:  # 按照API给节点取新的名字
                        tmp_name = ''
                        for i in apis:
                            tmp_name = tmp_name + i.split('->')[-1] + ' '
                        node_name = tmp_name.strip(' ')
                    try:
                        q = models.augmentNodeIn.objects.filter(actionName=node_name)
                        if q:  # 已经存在
                            one['source_kg_node'] = q[0].nodeID
                            path.append(one['source_kg_node'])
                        else:
                            # 创建新的节点
                            model=list(models.augmentNodeIn.objects.values())
                            kg_count = len(model)
                            now=model[kg_count-1]
                            now_id=now['nodeID']
                            one['source_kg_node'] = kg_count + 1
                            source_kg_node = one['source_kg_node']
                            mark = one['mark']
                            path.append(source_kg_node)
                            # print('api list:', api_list)
                            models.augmentNodeIn.objects.create(nodeID=now_id, actionName=node_name,
                                                                 perList=per_list,
                                                                 apiList=api_list,
                                                                 mark=mark)
                            models.augmentNodeIn.objects.filter(nodeID=now_id).update(id=now_id)
                    except Exception as e:
                        # print(e)
                        pass
                else:
                    path.append(source_kg_node)

            print('path1:', path)
            i = 0  # 从类似[1,2,2,3,3,3,4,1]转变为[1,2,3,4,1]
            while i < len(path) - 1:
                if path[i] == path[i + 1]:
                    del path[i]
                else:
                    i = i + 1
            print('path2:', path)
            new_path.append(path)
            # 根据path创建新的节点之间的关系
            i = 0
            while i < len(path) - 1:
                source = path[i]
                target = path[i + 1]
                try:
                    ans = models.augmentRelIn.objects.filter(Q(sourceID=source) & Q(targetID=target))
                    if ans:
                        pass  # 该关系已经存在
                except:
                    counts = len(list(models.augmentRelIn.objects.values()))
                    models.augmentRelIn.objects.create(sourceID=source, targetID=target)
                    models.augmentRelIn.objects.filter(Q(sourceID=source) & Q(targetID=target)).update(id=counts + 1)
                i = i + 1
    return new_path


def auto_augment():
    """
    :function 完整的augment.py代码，即完整地执行所有流程
    """
    # copy_kg_db()  # 复制数据表做备份，该函数执行一次就行
    # get_api2per_db()  # 构建 api--permission 数据库，即调用一个API时需要申请的权限

    # 读取匹配的输出结果
    file_path = '../detect/output/xmalchain/match_report.txt'
    # apks_location = '/home/wuyang/Experiments/Datas/tmpApk/protest'
    # apks_location = '/home/wuyang/Experiments/Datas/malwares/sample_apk_100'
    apks_location='/home/wuyang/Experiments/Datas/malwares/googlePlay/apk_sample'
    # apks_location='/home/wuyang/Experiments/Datas/malwares/part_androzoo/androzoo_apk_100'
    # apks_location='/media/wuyang/WD_BLACK/AndroidMalware/malware_test_googleplay'
    logs = '../detect/output/xmalchain/augment_logs.txt'

    # 输出结果
    output_path = '../detect/output/xmalchain/augment_report.txt'
    # 清空输出报告
    with open(output_path, "a", encoding='utf-8') as output:
        output.truncate(0)
    with open(logs, "a", encoding='utf-8') as output:
        output.truncate(0)
    # 清空CFG生成的文件夹
    # shutil.rmtree('../detect/output_augment/processing/')
    # os.mkdir('../detect/output_augment/processing/')

    file_data = read_match_report(file_path).split(";")
    # print(file_data)
    file_list = []  # [{apk name1, match ans1},{apk name2, match ans2}...]
    for one in file_data[0:-1]:
        file_list.append(json.loads(one))  # 字符串转换为字典
    count = 0
    for one in file_list:
        start = time.time()  # 开始计算时间
        apk_name = one['apk_name']
        match_path = one['match_path']  # "[[47, 57], [12, 57], [13, 57], [22, 57], [16, 57]]"
        base_location = '../detect/output_augment/processing/'  # 扔进apk文件并在该文件夹下执行androguard命令
        base_location = base_location + apk_name + '/'
        ret_json = {}
        ret_json['apk_name'] = apk_name
        ret_json['match_path'] = match_path
        # 1. 处理匹配结果
        print('apk_name:', apk_name)
        path_node = extract_node_from_path(match_path)
        if len(path_node) > 0:
            print('path_node:', path_node)
            # match_nodes = [6, 11, 13, 16, 22, 30, 35, 49, 56, 57]  # 来自9e.apk
            # 2. 根据匹配结果，依次查看节点的特征组成，查找敏感api
            node_apis = find_sensitive_api(path_node)
            print('node_apis:', node_apis)
            # 3. 找入口函数，即寻找一个从当前知识图谱节点到CG节点的映射
            entrypoint_ans = find_entrypoint(node_apis, apk_name)
            print('entrypoint_ans:', entrypoint_ans)
            # 4. 通过CG中的Edge pair发现与当前节点相关的入口函数
            all_node_source_info = find_parent_point(entrypoint_ans, apk_name)
            for one in all_node_source_info:
                print('all node source info1:', one)
            # 5. 寻找当前kg node可能扩展的入口函数
            all_node_source_info, all_node_source_info_end = find_down_entrypoint(all_node_source_info, apk_name,
                                                                                  base_location, apks_location)
            # 6. 挖掘新的节点
            for one in all_node_source_info:
                print('all node source info2:', one)
            augment_nodes = augment_new_node_v2(all_node_source_info, base_location)
            print('augment node:', augment_nodes)
            # 7. 将新的节点插入到数据库中
            new_path = augment_new_kg(augment_nodes)
            # 8. 写入日志文件中
            end = time.time()
            comput_time = end - start
            ret_json['comput_time'] = comput_time
            ret_json['new_path'] = new_path
            ret_json['augment_nodes'] = augment_nodes
            with open(output_path, 'a', encoding='utf-8') as output:
                output.write(json.dumps(ret_json, indent=4, ensure_ascii=False))
                output.write(';')
            # 将输出信息写入日志文件
            count = count + 1
            with open(logs, 'a', encoding='utf-8') as output:
                output.write('\n\n******' + str(count) + '******' + '\n')
                output.write('Apk Name: ' + apk_name + '\n')
                output.write('Match Path: ' + str(match_path) + '\n')
                output.write('Match Nodes: ' + str(path_node) + '\n')
                output.write('KG Node -> CG Node: ' + str(entrypoint_ans) + '\n')
                output.write('Find Father and New Nodes: ' + str(all_node_source_info) + '\n')
                output.write('Augment Nodes: ' + str(augment_nodes) + '\n')


        else:
            with open(output_path, 'a', encoding='utf-8') as output:
                output.write(json.dumps(ret_json, indent=4, ensure_ascii=False))
                output.write(';')


# auto_augment()