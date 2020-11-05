from django.urls import path

from tom_alerts_dash import dash
from tom_alerts_dash.views import BrokerQueryListView

app_name = 'tom_alerts_dash'

urlpatterns = [
    path('query/list/', BrokerQueryListView.as_view(), name='list'),
]
