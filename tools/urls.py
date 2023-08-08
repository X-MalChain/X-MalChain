from django.urls import path
from tools.views import print_kg,test

urlpatterns = [
    path('printkg', print_kg),
    path('test',test)
]