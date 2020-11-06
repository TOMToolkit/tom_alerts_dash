from django.urls import path

from tom_alerts_dash import dash
from tom_alerts_dash.views import BrokerQueryBrowseView, RunQueryView

app_name = 'tom_alerts_dash'

urlpatterns = [
    path('query/browse/', BrokerQueryBrowseView.as_view(), name='browse'),
    path('query/<int:pk>/run', RunQueryView.as_view(), name='run')
]
