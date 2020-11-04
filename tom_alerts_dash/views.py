from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class BrokerQueryListView(LoginRequiredMixin, TemplateView):
    template_name = 'tom_alerts_dash/brokerquery_list.html.html'
