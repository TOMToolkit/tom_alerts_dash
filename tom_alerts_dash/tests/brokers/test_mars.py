import json
from requests import Response
from unittest.mock import patch

from dash.exceptions import PreventUpdate
from django.test import TestCase

from tom_alerts_dash.brokers.mars import MARSDashBroker
from tom_alerts_dash.tests.factories import create_mars_alert, SiderealTargetFactory


class TestMARSDashBroker(TestCase):

    def setUp(self):
        self.broker = MARSDashBroker()

        self.test_target = SiderealTargetFactory.create()
        self.test_alerts = [create_mars_alert() for i in range(0, 5)]

    def test_flatten_dash_alerts(self):
        flattened_alerts = self.broker.flatten_dash_alerts(self.test_alerts)
        for key in ['objectId', 'ra', 'dec', 'magpsf', 'rb']:
            self.assertIn(key, flattened_alerts[0])
        for key in ['drb', 'test_bad_key']:
            self.assertNotIn('drb', flattened_alerts[0])  # Test that no unwanted attributes are included

    def test_callback_partial_cone_search(self):
        with self.assertRaises(PreventUpdate):
            self.broker.callback(1, 20, '', 100, None, None, None, None)

    @patch('tom_alerts.brokers.mars.MARSBroker._request_alerts')
    def test_callback_full_cone_search(self, mock_request_alerts):
        mock_request_alerts.return_value = {'results': self.test_alerts}
        self.broker.callback(1, 20, '', '100', '100', '100', None, None)
        self.assertDictContainsSubset({'cone': '100,100,100'}, mock_request_alerts.call_args.args[0])
