import json

from django.shortcuts import render
from django.http import HttpResponse

from common import models
from common.models import ApiTest, PerTest, KgBackup


# Create your views here.
def alter_table(request):
    """
    原本数据库中api的class之间使用"/"分隔
    现在使用"."分隔
    """
    try:
        ans = ApiTest.objects.all()
        ans = list(ans)
        for one in ans:
            # print('api', one)
            api = one.apiName
            ID = one.id
            # api = api.replace(".", "/")
            print('api str:', api)
            ApiTest.objects.filter(id=ID).update(apiName=api)
            # User.objects.filter(id=1).update(username='nick', is_active=True)
    except Exception as e:
        print(e)
        return HttpResponse("alter_table has an error!")

    return HttpResponse("ok")


def query_by_id(request):
    """
    function: 根据传入的id查询
    id(int):待查询的id
    flag(int):用以标识要查询的是permission还是api
    """
    id = int(request.POST.get('id'))
    flag = int(request.POST.get('flag'))
    ret = ''
    if flag == 0:
        ans = ApiTest.objects.get(apiID=id)
        ans = object_to_json(ans)
        ret = ans['apiName']
    elif flag == 1:
        ans = PerTest.objects.get(perID=id)
        ans = object_to_json(ans)
        # ret = ans.__dict__().perName
        ret = ans['perName']
    else:
        # print('xixi')
        pass
    return HttpResponse(ret, status=200)


def dict_list(demo_list, _flag):
    """
    :param demo_list:由字典组成的数组 QuerySet，形如：[{'perName': 'android.permission.ACCESS_BACKGROUND_LOCATION'}, {'perName': 'android.permission.ACCESS_COARSE_LOCATION'}]
    :param _flag: 传入要提取的字段名
    :return a sample list
    """
    try:
        ret_list = []
        for i in demo_list:
            ret_list.append(i[_flag])
        # print('ret:',ret_list)
        return ret_list
        # if _flag == 0:  # 权限的QuerySet
        #     for i in demo_list:
        #         ret_list.append(i['perName'])
        # elif _flag == 1:
        #     for i in demo_list:
        #         ret_list.append(i['apiName'])
        # elif _flag=='actionName':
        #     for i in demo_list:
        #         ret_list.append(i['apiName'])
    except Exception as e:
        print('Error: dict_list throw a exception!')
        print(e)


# objects.get()结果转换
def object_to_json(obj):
    ans = {}
    # obj.__dict__ 可将django对象转化为字典
    for key, value in obj.__dict__.items():
        # 将字典转化为JSON格式
        ans[key] = value
    return ans


def alter_api(request):
    """
    function: 修改单个的api，同时修改节点中的对应部分
    api_id：要修改的api的id
    new_api_name: 修改后的api name
    new_api_in: api 引入时的api level
    new_api_out: api弃用时的api level
    """
    try:
        # 接收从前端传入的数据
        json_data = json.loads(request.body)
        # print(json_data)
        if json_data['id'] != '':
            api_id = int(json_data['id'])
            new_api_name = json_data['newName']
            new_api_in = json_data['inLevel']
            new_api_out = json_data['outLevel']
            # 修改数据并保存
            old_api = ApiTest.objects.get(apiID=api_id)
            if new_api_name != '':
                old_api.apiName = new_api_name
            if new_api_in != '':
                old_api.inLevel = int(new_api_in)
            else:
                old_api.inLevel = 0
            if new_api_out != '':
                old_api.outLevel = int(new_api_out)
            else:
                old_api.outLevel = 0
            old_api.save()
            return HttpResponse('修改api成功', status=200)
        else:
            return HttpResponse('missing ID in alter_api()', status=500)

    except HttpResponse as e:
        print('alter_api throws an error!')
        return HttpResponse(e, status=500)


def add_api(request):
    """
    function：添加新的api
    api_name: 新的api的名称
    in_level:引入时的版本
    out_level: 弃用时的版本
    add_list: 相关的add api list
    rep_list: 相关的replace api list
    """
    try:
        # 接收从前端传入的数据
        json_data = json.loads(request.body)
        print(json_data)
        if json_data['apiName'] != '':
            api_name = json_data['apiName']
            in_level = json_data['inLevel']
            out_level = json_data['outLevel']
            add_list = json_data['addList']
            rep_list = json_data['repList']
            # 检查该api是否重复出现
            api_names = ApiTest.objects.values('apiName')
            api_names = dict_list(api_names, 'apiName')
            if api_names not in api_names:  # 没有重复插入
                models.ApiTest.objects.create(apiName=api_name, inLevel=in_level, outLevel=out_level, addList=add_list,
                                                    repList=rep_list)
                ans = ApiTest.objects.get(apiName=api_name)
                ans = object_to_json(ans)
                ApiTest.objects.filter(id=ans['id']).update(apiID=ans['id'])  # 设置apiID的值
        return HttpResponse('添加api成功')

    except HttpResponse as e:
        print('add_api throws an error!')
        return HttpResponse(e, status=500)


def delete_api(request):
    """
    function: 删除api
    api_id：要修改的api的id
    """
    try:
        # assert request.method == 'Post'
        # 接收从前端传入的数据
        json_data = json.loads(request.body)
        api_id = json_data['id']
        # api_id = request.POST.get('api_id')
        ApiTest.objects.filter(id=api_id).delete()

        return HttpResponse('删除API成功')
    except HttpResponse as e:
        print('delete_api throws an error!')
        return HttpResponse(e, status=500)


def alter_node(request):
    """
    function: 修改单个的节点，同时修改节点中的对应部分
    node_id：要修改的node的id
    new_node_name: 修改后的node name
    new_per_list: 节点相关的permissions
    new_api_list: api弃用时的apis

    补充！！！当api发生变化时，他们在kg表和关系表中出现的地方也应该相应修改(这部分还没写)
    """
    try:
        # 接收从前端传入的数据
        json_data = json.loads(request.body)
        # print(json_data)
        if json_data['id'] != '':
            node_id = int(json_data['id'])
            new_node_name = json_data['actionName']
            new_pers = json_data['perList']
            new_apis = json_data['apiList']
            # print('new apis:', new_apis)
            # 修改数据并保存
            old_node = KgBackup.objects.get(id=node_id)
            # print('node:', object_to_json(old_node))
            if new_node_name != '':
                old_node.actionName = new_node_name
            if new_pers != '':
                if new_pers == '0':  # 当接收到的数为0时，将原有数据清空
                    old_node.perList = ''
                else:
                    old_node.perList = new_pers
            if new_apis != '':
                if new_apis == '0':
                    old_node.apiList = ''
                else:
                    old_node.apiList = new_apis
            old_node.save()

        return HttpResponse('修改节点成功')

    except HttpResponse as e:
        print('alter_node throws an error!')
        return HttpResponse(e, status=500)


def add_node(request):
    """
    function：添加新的节点
    node_name: 新的node的名称
    api_list: 相关的api list
    per_list: 相关的per list
    """
    try:
        # 接收从前端传入的数据
        json_data = json.loads(request.body)
        print(json_data)
        if json_data['nodeName'] != '':
            node_name = json_data['nodeName']
            api_list = json_data['apiList']
            per_list = json_data['perList']
            # 检查该api是否重复出现
            node_names = KgBackup.objects.values('actionName')
            node_names = dict_list(node_names, 'actionName')
            if node_name not in node_names:  # 没有重复插入
                models.augmenTestNode.objects.create(actionName=node_name, apiList=api_list, perList=per_list)
                ans = KgBackup.objects.get(actionName=node_name)
                ans_id = ans.id
                KgBackup.objects.filter(id=ans_id).update(nodeID=ans_id)  # 设置node ID的值
        return HttpResponse('添加node成功')

    except BaseException as e:
        print('add_node throws an error!')
        return HttpResponse(e, status=500)


def dict_trans_list(dict, node_num):
    """
    :param dict:传入的是字典，例如   {"1": 97, "2": 16, "5": 69, "6": 64, "7": 94}，对应的是每个节点被匹配的次数
    :param node_num: 图谱上所有节点的数量，当前为50
    :return ret_node_id_list: 节点序列
            ret_node_map_num: 与节点序列相对应的节点匹配次数
    """
    ret_dict = {}
    ret_node_id_list = []
    ret_node_map_num = []
    key_list = []
    value_list = []
    int_or_str = 0  # 判断输入数据的key的数据类型，0为int，1为str
    for key, value in dict.items():
        if isinstance(key, int):
            int_or_str = 0  # key的数据类型为int
            break
        elif isinstance(key, str):
            int_or_str = 1
            break
    for key, value in dict.items():
        # print('key: ', key, 'value: ', value)
        key_list.append(key)
        value_list.append(value)
    n = 1
    while n <= node_num:
        try:
            if int_or_str == 1:
                pos = key_list.index(str(n))
                # print('pos:', pos)
                num = value_list[pos]
                ret_dict.update({str(n): num})
            else:
                pos = key_list.index(n)
                # print('pos:', pos)
                num = value_list[pos]
                ret_dict.update({str(n): num})
        except:  # 没有找到相应的元素
            ret_dict.update({str(n): 0})
        n = n + 1
    for key, value in ret_dict.items():
        # print('key: ', key, 'value: ', value)
        ret_node_id_list.append(key)
        ret_node_map_num.append(value)
    return ret_dict, ret_node_id_list, ret_node_map_num


def alter_relation():
    """
    function:修改reltest数据表
    罢了，第一次直接手动修改
    """


def test(request):
    # dict1: 正常条件下完全匹配的节点情况
    # dict3: 不将permission计算在匹配率后的完全匹配的节点情况
    # dict1 = {"1": 47, "5": 7, "6": 5, "7": 71, "8": 28, "11": 22, "14": 35, "15": 35, "17": 27, "18": 15, "23": 9,
    #         "31": 28, "32": 78, "39": 36, "40": 35, "42": 16, "46": 50, "47": 63, "48": 55, "49": 24, "50": 83}
    dict2 = {1: 10, 2: 2, 5: 8, 6: 8, 7: 10, 8: 10, 9: 8, 10: 9, 11: 8, 12: 10, 13: 10, 14: 9, 15: 9, 16: 9, 17: 8,
             18: 9, 19: 8, 20: 9, 21: 9, 22: 9, 23: 8, 24: 10, 25: 7, 26: 1, 27: 10, 28: 10, 29: 1, 30: 3, 31: 3, 32: 6,
             33: 6, 34: 10, 35: 7, 36: 9, 38: 10, 39: 6, 40: 9, 41: 5, 42: 10, 43: 1, 44: 6, 45: 2, 46: 4, 47: 6, 48: 8,
             49: 3, 50: 10}
    dict3 = {"1": 47, "2": 0, "3": 0, "4": 0, "5": 11, "6": 45, "7": 93, "8": 40, "9": 45, "10": 0, "11": 22, "12": 50,
             "13": 47, "14": 35, "15": 51, "16": 40, "17": 51, "18": 51, "19": 40, "20": 37, "21": 0, "22": 0, "23": 9,
             "24": 52, "25": 0, "26": 0, "27": 1, "28": 6, "29": 0, "30": 24, "31": 28, "32": 78, "33": 0, "34": 0,
             "35": 57, "36": 0, "37": 0, "38": 0, "39": 38, "40": 51, "41": 0, "42": 19, "43": 0, "44": 0, "45": 0,
             "46": 50, "47": 63, "48": 55, "49": 24, "50": 83}

    node_num = 50
    ret_dict, ret_node_id_list, ret_node_map_num = dict_trans_list(dict3, node_num)
    print('*************************')
    print('ret_dict:', ret_dict)
    print('ret_node_id_list:', ret_node_id_list)
    print('ret_node_map_num:', ret_node_map_num)

    # KgBackup.objects.filter(id=1).update(nodeID=1)  # 设置node ID的值
    # KgBackup.objects.filter(id=2).update(nodeID=2)  # 设置node ID的值
    return HttpResponse('manage test!')