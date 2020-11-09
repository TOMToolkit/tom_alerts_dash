from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from tom_alerts.views import BrokerQueryListView


# class BrokerQueryListView(LoginRequiredMixin, TemplateView):
class BrokerQueryBrowseView(TemplateView):
    template_name = 'tom_alerts_dash/brokerquery_browse.html'


class RunQueryView(TemplateView):
    template_name = 'tom_alerts_dash/brokerquery_browse.html'


class BrokerQueryListView(BrokerQueryListView):
    template_name = 'tom_alerts_dash/brokerquery_list.html'
