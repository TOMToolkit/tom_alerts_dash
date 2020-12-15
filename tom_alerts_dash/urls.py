from django.urls import path

from tom_alerts_dash import dash  # noqa - this import is necessary for Dash to run
from tom_alerts_dash.views import BrokerQueryBrowseView, BrokerQueryListView

app_name = 'tom_alerts_dash'

urlpatterns = [
    path('query/list/', BrokerQueryListView.as_view(), name='list'),
    path('query/browse/', BrokerQueryBrowseView.as_view(), name='browse'),
]
