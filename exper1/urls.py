from django.urls import path
from exper1.views import mainDetect, test

urlpatterns=[
    path('main', mainDetect),
    path('test', test)
]