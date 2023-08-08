from django.shortcuts import render
from django.http import HttpResponse
from common import models
from common.models import ApiTest, PerTest, KgTest, relTest, KgBackup, relBackup

# Create your views here.
from py2neo import Graph, Node, Relationship, NodeMatcher


def create_graph():
    # 1、连接neo4j数据库，输入账号密码并指定数据库
    graph = Graph("http://localhost:7474", auth=("neo4j", '11111111'), name='mwep')
    # 清除neo4j中原有节点的所有信息
    # graph.delete()
    graph.run('match (n) detach delete n')

    # 2、创建节点，使用表KgTest读取有哪些节点，并通过和表ApiTest、PerTest连接读取每个节点的特征（即调用的apis和申请的permissions）
    # kg = KgTest.objects.values()
    kg = KgBackup.objects.values()
    for one in kg:
        action_id = one['id']
        action_name = one['actionName']
        per_id_list = one['perList']
        # print('per list:', per_id_list)
        api_id_list = one['apiList']
        per_list = str_list(per_id_list)
        api_list = str_list(api_id_list)
        permissions = []
        apis = []
        if len(per_list) > 0:
            for per in per_list:
                try:
                    per_obj = PerTest.objects.get(id=per)
                    permissions.append(per_obj.perName)
                except:
                    pass
        if len(api_list) > 0:
            for api in api_list:
                try:
                    api_obj = models.ApiTest.objects.get(id=api)
                    apis.append(api_obj.apiName)
                except:
                    pass
        # print('one', kg)
        # if int(action_id)<20:
        #     node = Node('Behavoir', ID=action_name, name=action_name)  # 给节点添加标签，显著恶意的和非显著恶意的
        # else:
        #     node = Node('Unkown', ID=action_name, name=action_name)  # 给节点添加标签，显著恶意的和非显著恶意的
        node = Node('Behavior', ID=action_id, name=action_id, apis=apis, permissions=permissions, action=action_name)
        graph.create(node)

    # 3、创建关系，使用表relTest读取节点之间的关系
    node_matcher = NodeMatcher(graph)  # 创建NodeMatcher对象
    # rel = relTest.objects.values()
    rel = models.relBackup.objects.values()
    for one in rel:
        node_id_source = one['sourceID']
        node_id_target = one['targetID']
        relation = one['relation']
        # print('sourceID:',node_id_source)
        # print('target:', node_id_target)
        # print('relation:', relation)
        if relation=='':    # relation不能为空
            relation='next'
        # print('\n')
        node_source = node_matcher.match("Behavior").where(ID=node_id_source).first()
        node_target = node_matcher.match("Behavior").where(ID=node_id_target).first()
        r = Relationship(node_source, relation, node_target)
        graph.create(r)


def str_list(str_list):
    """
    :param str_list: 数据类型为字符串，但是是数组的形式
    """
    ret_list = []
    if str_list != '':  # 首先应该保证不为空
        if str_list.find(',') != -1:  # 说明有多个permission或者apis
            ret_list = str_list.split(',')
        else:
            ret_list.append(int(str_list))  # 说明只有一个permission或者api
    return ret_list


def test(request):
    create_graph()
    return HttpResponse("create kg")
