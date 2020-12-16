from django.urls import path

# This import is necessary for Dash to run, likely because it imports and runs the staticfiles finders
# as defined in settings.STATICFILES_FINDERS
from tom_alerts_dash import dash  # noqa
from tom_alerts_dash.views import BrokerQueryBrowseView, BrokerQueryListView

app_name = 'tom_alerts_dash'

urlpatterns = [
    path('query/list/', BrokerQueryListView.as_view(), name='list'),
    path('query/browse/', BrokerQueryBrowseView.as_view(), name='browse'),
]
