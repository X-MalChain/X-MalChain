import json

from django.http import HttpResponse

from common import models
from common.models import ApiTest, PerTest, KgBackup


# Create your views here.
def alter_table(request):
    try:
        ans = ApiTest.objects.all()
        ans = list(ans)
        for one in ans:
            api = one.apiName
            ID = one.id
            print('api str:', api)
            ApiTest.objects.filter(id=ID).update(apiName=api)
    except Exception as e:
        print(e)
        return HttpResponse("alter_table has an error!")

    return HttpResponse("ok")


def query_by_id(request):
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
    else:
        pass
    return HttpResponse(ret, status=200)


def dict_list(demo_list, _flag):
    try:
        ret_list = []
        for i in demo_list:
            ret_list.append(i[_flag])
        return ret_list
    except Exception as e:
        print('Error: dict_list throw a exception!')
        print(e)


def object_to_json(obj):
    ans = {}
    for key, value in obj.__dict__.items():
        ans[key] = value
    return ans


def alter_api(request):
    try:
        json_data = json.loads(request.body)
        if json_data['id'] != '':
            api_id = int(json_data['id'])
            new_api_name = json_data['newName']
            new_api_in = json_data['inLevel']
            new_api_out = json_data['outLevel']
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
            return HttpResponse('alter api', status=200)
        else:
            return HttpResponse('missing ID in alter_api()', status=500)

    except HttpResponse as e:
        print('alter_api throws an error!')
        return HttpResponse(e, status=500)


def add_api(request):
    try:
        json_data = json.loads(request.body)
        print(json_data)
        if json_data['apiName'] != '':
            api_name = json_data['apiName']
            in_level = json_data['inLevel']
            out_level = json_data['outLevel']
            add_list = json_data['addList']
            rep_list = json_data['repList']
            api_names = ApiTest.objects.values('apiName')
            api_names = dict_list(api_names, 'apiName')
            if api_names not in api_names:
                models.ApiTest.objects.create(apiName=api_name, inLevel=in_level, outLevel=out_level, addList=add_list,
                                                    repList=rep_list)
                ans = ApiTest.objects.get(apiName=api_name)
                ans = object_to_json(ans)
                ApiTest.objects.filter(id=ans['id']).update(apiID=ans['id'])
        return HttpResponse('add api')

    except HttpResponse as e:
        print('add_api throws an error!')
        return HttpResponse(e, status=500)


def delete_api(request):
    try:
        json_data = json.loads(request.body)
        api_id = json_data['id']
        ApiTest.objects.filter(id=api_id).delete()

        return HttpResponse('delete API')
    except HttpResponse as e:
        print('delete_api throws an error!')
        return HttpResponse(e, status=500)


def alter_node(request):
    try:
        json_data = json.loads(request.body)
        if json_data['id'] != '':
            node_id = int(json_data['id'])
            new_node_name = json_data['actionName']
            new_pers = json_data['perList']
            new_apis = json_data['apiList']
            old_node = KgBackup.objects.get(id=node_id)
            if new_node_name != '':
                old_node.actionName = new_node_name
            if new_pers != '':
                if new_pers == '0':
                    old_node.perList = ''
                else:
                    old_node.perList = new_pers
            if new_apis != '':
                if new_apis == '0':
                    old_node.apiList = ''
                else:
                    old_node.apiList = new_apis
            old_node.save()

        return HttpResponse('alter node')

    except HttpResponse as e:
        print('alter_node throws an error!')
        return HttpResponse(e, status=500)


def add_node(request):
    try:
        json_data = json.loads(request.body)
        print(json_data)
        if json_data['nodeName'] != '':
            node_name = json_data['nodeName']
            api_list = json_data['apiList']
            per_list = json_data['perList']
            node_names = KgBackup.objects.values('actionName')
            node_names = dict_list(node_names, 'actionName')
            if node_name not in node_names:
                models.augmenTestNode.objects.create(actionName=node_name, apiList=api_list, perList=per_list)
                ans = KgBackup.objects.get(actionName=node_name)
                ans_id = ans.id
                KgBackup.objects.filter(id=ans_id).update(nodeID=ans_id)
        return HttpResponse('add node')

    except BaseException as e:
        print('add_node throws an error!')
        return HttpResponse(e, status=500)


def dict_trans_list(dict, node_num):
    ret_dict = {}
    ret_node_id_list = []
    ret_node_map_num = []
    key_list = []
    value_list = []
    int_or_str = 0
    for key, value in dict.items():
        if isinstance(key, int):
            int_or_str = 0
            break
        elif isinstance(key, str):
            int_or_str = 1
            break
    for key, value in dict.items():
        key_list.append(key)
        value_list.append(value)
    n = 1
    while n <= node_num:
        try:
            if int_or_str == 1:
                pos = key_list.index(str(n))
                num = value_list[pos]
                ret_dict.update({str(n): num})
            else:
                pos = key_list.index(n)
                num = value_list[pos]
                ret_dict.update({str(n): num})
        except:
            ret_dict.update({str(n): 0})
        n = n + 1
    for key, value in ret_dict.items():
        ret_node_id_list.append(key)
        ret_node_map_num.append(value)
    return ret_dict, ret_node_id_list, ret_node_map_num


def alter_relation():
    """
    """


def test(request):
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


    return HttpResponse('manage test!')