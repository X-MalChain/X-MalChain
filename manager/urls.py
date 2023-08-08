from django.urls import path
from manager.views import alter_table, alter_api, alter_node, delete_api, query_by_id, add_api, test, add_node

urlpatterns = [
    path('altertable', alter_table),
    path('alterapi', alter_api),
    path('alternode', alter_node),
    path('deleteapi', delete_api),
    path('query', query_by_id),
    path('addapi', add_api),
    path('addnode', add_node),
    path('test', test)
]
