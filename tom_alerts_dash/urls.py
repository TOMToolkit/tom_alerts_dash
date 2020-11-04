from django.urls import path

from tom_alerts_dash import dash
from tom_alerts_dash.views import BrokerQueryListView

app_name = 'skip'

urlpatterns = [
    path('query/list/', BrokerQueryListView.as_view(), name='index'),
]
