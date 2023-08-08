from django.urls import path
from detect.views import mainDetect, test

urlpatterns=[
    path('main', mainDetect),
    path('test', test)
]