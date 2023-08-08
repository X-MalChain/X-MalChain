from django.urls import path
from createkg.views import test

urlpatterns=[
    path('test', test),
]