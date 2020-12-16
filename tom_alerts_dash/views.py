from django.views.generic import TemplateView

from tom_alerts.views import BrokerQueryListView


class BrokerQueryBrowseView(TemplateView):
    template_name = 'tom_alerts_dash/brokerquery_browse.html'


class BrokerQueryListView(BrokerQueryListView):
    template_name = 'tom_alerts_dash/brokerquery_list.html'
