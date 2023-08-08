from django.urls import path
from exper.views import mainDetect, test

urlpatterns=[
    path('main', mainDetect),
    path('test', test)
]