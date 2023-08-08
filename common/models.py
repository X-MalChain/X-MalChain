from django.db import models


# Create your models here.

# Basic Knowledge graph
class KgTest(models.Model):
    nodeID = models.IntegerField()
    actionName = models.CharField(max_length=120)
    perList = models.CharField(max_length=120, blank=True)
    apiList = models.CharField(max_length=120, blank=True)


# After the first augmentation
class KgBackup(models.Model):
    nodeID = models.IntegerField(null=True, blank=True)
    actionName = models.CharField(max_length=120)
    perList = models.CharField(max_length=120, blank=True, default='')
    apiList = models.CharField(max_length=120, blank=True, default='')

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


# Renew
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

class apiRequsetPer(models.Model):
    api = models.CharField(max_length=250, blank=True, default='')
    per = models.CharField(max_length=250, blank=True, default='')


# Test for upgrading
class augmenTestNode(models.Model):
    nodeID = models.IntegerField(null=True, blank=True)
    actionName = models.CharField(max_length=120)
    perList = models.CharField(max_length=120, blank=True, default='')
    apiList = models.CharField(max_length=120, blank=True, default='')
    mark = models.CharField(max_length=50, blank=True, default='')

class augmenTestRel(models.Model):
    sourceID = models.IntegerField()
    sourceAct = models.CharField(max_length=200, blank=True, default='')
    targetID = models.IntegerField()
    targetAct = models.CharField(max_length=200, blank=True, default='')
    relation = models.CharField(max_length=120, blank=True)

class augmenTestPer(models.Model):
    # perID = models.IntegerField(blank=True)
    perID = models.IntegerField(null=True, blank=True)
    perName = models.CharField(max_length=200)
    inLevel = models.CharField(max_length=50, blank=True)
    outLevel = models.CharField(max_length=50, blank=True)

class augmenTestAPi(models.Model):
    # apiID = models.IntegerField(blank=True)
    apiID = models.IntegerField(null=True, blank=True)
    apiName = models.CharField(max_length=200)
    inLevel = models.CharField(max_length=50, blank=True)
    outLevel = models.CharField(max_length=50, blank=True)
    addList = models.CharField(max_length=200, blank=True)
    repList = models.CharField(max_length=200, blank=True)


# Backup
# the first round upgrading
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

# the second upgrading
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

class augmentAPi2(models.Model):
    # apiID = models.IntegerField(blank=True)
    apiID = models.IntegerField(null=True, blank=True)
    apiName = models.CharField(max_length=200)
    inLevel = models.CharField(max_length=50, blank=True)
    outLevel = models.CharField(max_length=50, blank=True)
    addList = models.CharField(max_length=200, blank=True)
    repList = models.CharField(max_length=200, blank=True)

# The third upgrading
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

class augmentAPi3(models.Model):
    # apiID = models.IntegerField(blank=True)
    apiID = models.IntegerField(null=True, blank=True)
    apiName = models.CharField(max_length=200)
    inLevel = models.CharField(max_length=50, blank=True)
    outLevel = models.CharField(max_length=50, blank=True)
    addList = models.CharField(max_length=200, blank=True)
    repList = models.CharField(max_length=200, blank=True)


# The inter-upgrading
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
