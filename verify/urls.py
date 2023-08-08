from django.urls import path
from verify.views import mainTask,verifyByFeature,verifyByNode

urlpatterns=[
    path('test0', mainTask),
    path('test1', verifyByFeature),
    path('test2', verifyByNode),
]