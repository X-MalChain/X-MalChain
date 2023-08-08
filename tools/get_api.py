import os
import django
import sys
sys.path.append('../')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mwep.settings')

django.setup()

from common.models import KgTest


def test():
    print('hello world')
    ans = KgTest.objects.values()
    print('ans:', ans)


def get_sensitive_apis():
    """
    :function 构建敏感api的数据库
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
            # models.sensitiveApi.objects.create(api=api, permission=permission)
            # if api not in apis:
            #     apis.append(api)
            # else:
            #     # apis.append(api)
            #     # print('重复')
            # print('class_api:', class_api)


get_sensitive_apis()
