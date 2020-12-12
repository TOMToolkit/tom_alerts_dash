from django.test import TestCase

from tom_alerts_dash.brokers.mars import MARSDashBroker


class TestMARSDashBroker(TestCase):

    def setUp(self):
        self.test_target = Target.objects.create(name='ZTF18aberpsh')

    # def test_flatten_dash_alerts(self, alerts):
