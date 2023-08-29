from django.http import HttpResponse
from common import models
from common.models import ApiTest, PerTest, KgTest, relTest, KgBackup, relBackup

# Create your views here.
from py2neo import Graph, Node, Relationship, NodeMatcher


def create_graph():
    # 1. access the neo4j, input username and password
    graph = Graph("http://localhost:7474", auth=("neo4j", '11111111'), name='mwep')
    # avoid multiple draw
    # graph.delete()
    graph.run('match (n) detach delete n')

    # 2. Create nodes
    kg = KgBackup.objects.values()
    for one in kg:
        action_id = one['id']
        action_name = one['actionName']
        per_id_list = one['perList']
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
        node = Node('Behavior', ID=action_id, name=action_id, apis=apis, permissions=permissions, action=action_name)
        graph.create(node)

    # 3. Create relationships
    node_matcher = NodeMatcher(graph)
    rel = models.relBackup.objects.values()
    for one in rel:
        node_id_source = one['sourceID']
        node_id_target = one['targetID']
        relation = one['relation']
        if relation=='': 
            relation='next'
        node_source = node_matcher.match("Behavior").where(ID=node_id_source).first()
        node_target = node_matcher.match("Behavior").where(ID=node_id_target).first()
        r = Relationship(node_source, relation, node_target)
        graph.create(r)


def str_list(str_list):
    """
    :param str_list: string list
    """
    ret_list = []
    if str_list != '':
        if str_list.find(',') != -1:
            ret_list = str_list.split(',')
        else:
            ret_list.append(int(str_list))
    return ret_list


def test(request):
    create_graph()
    return HttpResponse("create kg")
