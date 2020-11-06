from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


# class BrokerQueryListView(LoginRequiredMixin, TemplateView):
class BrokerQueryBrowseView(TemplateView):
    template_name = 'tom_alerts_dash/brokerquery_browse.html'


class RunQueryView(TemplateView):
    template_name = 'tom_alerts_dash/brokerquery_browse.html'
