from django.db import models


# Create your models here.
# 存放数据表的定义


# KG 表，存放节点信息
class KgTest(models.Model):
    nodeID = models.IntegerField()
    actionName = models.CharField(max_length=120)
    perList = models.CharField(max_length=120, blank=True)
    apiList = models.CharField(max_length=120, blank=True)


# KG 表，存放节点信息
# 更新后的节点数据表
class KgBackup(models.Model):
    nodeID = models.IntegerField(null=True, blank=True)
    actionName = models.CharField(max_length=120)
    perList = models.CharField(max_length=120, blank=True, default='')
    apiList = models.CharField(max_length=120, blank=True, default='')


# Api表，存放Api的基本信息，包括引入和弃用的API Level，和与之相关联的AddApiTest和RepApiTest
class ApiTest(models.Model):
    apiID = models.IntegerField(blank=True)
    apiName = models.CharField(max_length=200)
    inLevel = models.CharField(max_length=50, blank=True)
    outLevel = models.CharField(max_length=50, blank=True)
    # addList = models.IntegerField()
    addList = models.CharField(max_length=200, blank=True)
    # repList = models.IntegerField()
    repList = models.CharField(max_length=200, blank=True)


class AddApiTest(models.Model):
    listID = models.IntegerField()
    list = models.CharField(max_length=600)


class ApiSim(models.Model):
    listID = models.IntegerField(blank=True)
    list = models.CharField(max_length=600)


class ApiSDK(models.Model):
    listID = models.IntegerField(blank=True)
    list = models.CharField(max_length=600)


class PerSDK(models.Model):
    listID = models.IntegerField(blank=True)
    list = models.CharField(max_length=600)


class RepApiTest(models.Model):
    listID = models.IntegerField()
    list = models.CharField(max_length=600)


# Permission表，存放Permission的基本信息，包括引入和弃用的API Level
class PerTest(models.Model):
    perID = models.IntegerField()
    perName = models.CharField(max_length=200)
    inLevel = models.IntegerField()
    outLevel = models.IntegerField()


class relTest(models.Model):
    sourceID = models.IntegerField()
    sourceAct = models.CharField(max_length=200)
    targetID = models.IntegerField()
    targetAct = models.CharField(max_length=200)
    relation = models.CharField(max_length=120, blank=True)


# 更新后的关系数据表
class relBackup(models.Model):
    sourceID = models.IntegerField()
    sourceAct = models.CharField(max_length=200, blank=True, default='')
    targetID = models.IntegerField()
    targetAct = models.CharField(max_length=200, blank=True, default='')
    relation = models.CharField(max_length=120, blank=True)


class sensitiveApi(models.Model):
    api = models.CharField(max_length=200, blank=True, default='')
    permission = models.CharField(max_length=200, blank=True, default='')


class sensitiveApiMini(models.Model):
    api = models.CharField(max_length=200, blank=True, default='')
    tags = models.CharField(max_length=100, blank=True, default='')
    title = models.CharField(max_length=200, blank=True, default='')
    description = models.CharField(max_length=400, blank=True, default='')
    name = models.CharField(max_length=200, blank=True, default='')


# 调用api所需要的申请的权限
class apiRequsetPer(models.Model):
    api = models.CharField(max_length=250, blank=True, default='')
    per = models.CharField(max_length=250, blank=True, default='')


# 测试图谱自动扩展，测试数据库
class augmenTestNode(models.Model):
    nodeID = models.IntegerField(null=True, blank=True)
    actionName = models.CharField(max_length=120)
    perList = models.CharField(max_length=120, blank=True, default='')
    apiList = models.CharField(max_length=120, blank=True, default='')
    mark = models.CharField(max_length=50, blank=True, default='')

# 测试扩展的节点关系数据表
class augmenTestRel(models.Model):
    sourceID = models.IntegerField()
    sourceAct = models.CharField(max_length=200, blank=True, default='')
    targetID = models.IntegerField()
    targetAct = models.CharField(max_length=200, blank=True, default='')
    relation = models.CharField(max_length=120, blank=True)

# Permission表，用于测试扩展
class augmenTestPer(models.Model):
    # perID = models.IntegerField(blank=True)
    perID = models.IntegerField(null=True, blank=True)
    perName = models.CharField(max_length=200)
    inLevel = models.CharField(max_length=50, blank=True)
    outLevel = models.CharField(max_length=50, blank=True)

# Api表，用于测试扩展
class augmenTestAPi(models.Model):
    # apiID = models.IntegerField(blank=True)
    apiID = models.IntegerField(null=True, blank=True)
    apiName = models.CharField(max_length=200)
    inLevel = models.CharField(max_length=50, blank=True)
    outLevel = models.CharField(max_length=50, blank=True)
    addList = models.CharField(max_length=200, blank=True)
    repList = models.CharField(max_length=200, blank=True)


# 下面为备份扩充的知识图谱
# 备份经过第一次数据集（amd）扩充后的知识图谱
class augmentAMDNode(models.Model):
    nodeID = models.IntegerField(null=True, blank=True)
    actionName = models.CharField(max_length=120)
    perList = models.CharField(max_length=120, blank=True, default='')
    apiList = models.CharField(max_length=120, blank=True, default='')
    mark = models.CharField(max_length=50, blank=True, default='')

class augmentAMDRel(models.Model):
    sourceID = models.IntegerField()
    sourceAct = models.CharField(max_length=200, blank=True, default='')
    targetID = models.IntegerField()
    targetAct = models.CharField(max_length=200, blank=True, default='')
    relation = models.CharField(max_length=120, blank=True)

class augmentAMDPer(models.Model):
    # perID = models.IntegerField(blank=True)
    perID = models.IntegerField(null=True, blank=True)
    perName = models.CharField(max_length=200)
    inLevel = models.CharField(max_length=50, blank=True)
    outLevel = models.CharField(max_length=50, blank=True)

class augmentAMDAPi(models.Model):
    # apiID = models.IntegerField(blank=True)
    apiID = models.IntegerField(null=True, blank=True)
    apiName = models.CharField(max_length=200)
    inLevel = models.CharField(max_length=50, blank=True)
    outLevel = models.CharField(max_length=50, blank=True)
    addList = models.CharField(max_length=200, blank=True)
    repList = models.CharField(max_length=200, blank=True)

# 备份经过第2次数据集（amd+drebin）扩充后的知识图谱
class augmentNode2(models.Model):
    nodeID = models.IntegerField(null=True, blank=True)
    actionName = models.CharField(max_length=120)
    perList = models.CharField(max_length=120, blank=True, default='')
    apiList = models.CharField(max_length=120, blank=True, default='')
    mark = models.CharField(max_length=50, blank=True, default='')

class augmentRel2(models.Model):
    sourceID = models.IntegerField()
    sourceAct = models.CharField(max_length=200, blank=True, default='')
    targetID = models.IntegerField()
    targetAct = models.CharField(max_length=200, blank=True, default='')
    relation = models.CharField(max_length=120, blank=True)

class augmentPer2(models.Model):
    # perID = models.IntegerField(blank=True)
    perID = models.IntegerField(null=True, blank=True)
    perName = models.CharField(max_length=200)
    inLevel = models.CharField(max_length=50, blank=True)
    outLevel = models.CharField(max_length=50, blank=True)

# Api表，用于测试扩展
class augmentAPi2(models.Model):
    # apiID = models.IntegerField(blank=True)
    apiID = models.IntegerField(null=True, blank=True)
    apiName = models.CharField(max_length=200)
    inLevel = models.CharField(max_length=50, blank=True)
    outLevel = models.CharField(max_length=50, blank=True)
    addList = models.CharField(max_length=200, blank=True)
    repList = models.CharField(max_length=200, blank=True)

# 备份经过第3次数据集（amd+drebin）扩充后的知识图谱
class augmentNode3(models.Model):
    nodeID = models.IntegerField(null=True, blank=True)
    actionName = models.CharField(max_length=120)
    perList = models.CharField(max_length=120, blank=True, default='')
    apiList = models.CharField(max_length=120, blank=True, default='')
    mark = models.CharField(max_length=50, blank=True, default='')

class augmentRel3(models.Model):
    sourceID = models.IntegerField()
    sourceAct = models.CharField(max_length=200, blank=True, default='')
    targetID = models.IntegerField()
    targetAct = models.CharField(max_length=200, blank=True, default='')
    relation = models.CharField(max_length=120, blank=True)

class augmentPer3(models.Model):
    # perID = models.IntegerField(blank=True)
    perID = models.IntegerField(null=True, blank=True)
    perName = models.CharField(max_length=200)
    inLevel = models.CharField(max_length=50, blank=True)
    outLevel = models.CharField(max_length=50, blank=True)

# Api表，用于测试扩展
class augmentAPi3(models.Model):
    # apiID = models.IntegerField(blank=True)
    apiID = models.IntegerField(null=True, blank=True)
    apiName = models.CharField(max_length=200)
    inLevel = models.CharField(max_length=50, blank=True)
    outLevel = models.CharField(max_length=50, blank=True)
    addList = models.CharField(max_length=200, blank=True)
    repList = models.CharField(max_length=200, blank=True)


# 中间数据库
class augmentNodeIn(models.Model):
    nodeID = models.IntegerField(null=True, blank=True)
    actionName = models.CharField(max_length=120)
    perList = models.CharField(max_length=120, blank=True, default='')
    apiList = models.CharField(max_length=120, blank=True, default='')
    mark = models.CharField(max_length=50, blank=True, default='')

class augmentRelIn(models.Model):
    sourceID = models.IntegerField()
    sourceAct = models.CharField(max_length=200, blank=True, default='')
    targetID = models.IntegerField()
    targetAct = models.CharField(max_length=200, blank=True, default='')
    relation = models.CharField(max_length=120, blank=True)

class augmentPerIn(models.Model):
    # perID = models.IntegerField(blank=True)
    perID = models.IntegerField(null=True, blank=True)
    perName = models.CharField(max_length=200)
    inLevel = models.CharField(max_length=50, blank=True)
    outLevel = models.CharField(max_length=50, blank=True)

# Api表，用于测试扩展
class augmentAPiIn(models.Model):
    # apiID = models.IntegerField(blank=True)
    apiID = models.IntegerField(null=True, blank=True)
    apiName = models.CharField(max_length=200)
    inLevel = models.CharField(max_length=50, blank=True)
    outLevel = models.CharField(max_length=50, blank=True)
    addList = models.CharField(max_length=200, blank=True)
    repList = models.CharField(max_length=200, blank=True)

from django.contrib import admin

admin.site.register(PerTest)
admin.site.register(augmenTestAPi)
admin.site.register(RepApiTest)
admin.site.register(AddApiTest)
admin.site.register(relTest)
admin.site.register(KgTest)
