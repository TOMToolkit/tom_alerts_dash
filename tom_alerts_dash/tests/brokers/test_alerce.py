import json
from requests import Response
from unittest.mock import patch

from dash.exceptions import PreventUpdate
from django.test import TestCase

from tom_alerts_dash.brokers.alerce import ALeRCEDashBroker
from tom_alerts_dash.tests.factories import create_alerce_alert, SiderealTargetFactory


class TestALeRCEDashBroker(TestCase):

    def setUp(self):
        self.broker = ALeRCEDashBroker()

        self.test_target = SiderealTargetFactory.create()
        self.test_alerts = [create_alerce_alert() for i in range(0, 5)]

    def test_flatten_dash_alerts(self):
        flattened_alerts = self.broker.flatten_dash_alerts(self.test_alerts)
        for key in ['oid', 'meanra', 'meandec', 'discovery_date', 'classifier', 'classifier_type',
                    'classifier_probability']:
            self.assertIn(key, flattened_alerts[0])
        for key in ['last_mjd', 'test_bad_key']:
            self.assertNotIn('last_mjd', flattened_alerts[0])  # Test that no unwanted attributes are included

    def test_callback_no_button_click(self):
        with self.assertRaises(PreventUpdate):
            self.broker.callback(1, 20, None, None, None, None, None, None, None, None, None)

        with self.assertRaises(PreventUpdate):
            self.broker.dash_button_clicks = 1
            self.broker.callback(1, 20, None, None, None, None, None, None, None, None, 1)

    @patch('tom_alerts.brokers.mars.MARSBroker._request_alerts')
    def test_callback_full_cone_search(self, mock_request_alerts):
        # TODO: this
        mock_request_alerts.return_value = {'results': self.test_alerts}
        self.broker.callback(1, 20, '', '100', '100', '100', None, None)
        self.assertDictContainsSubset({'cone': '100,100,100'}, mock_request_alerts.call_args.args[0])

    @patch('tom_alerts.brokers.mars.MARSBroker._request_alerts')
    def test_callback(self, mock_request_alerts):
        # TODO: this
        test_alert = create_mars_alert(ra=60, dec=120, magpsf=15.12345, rb=0.87654)
        mock_request_alerts.return_value = {'results': [test_alert]}
        alerts = self.broker.callback(1, 20, '', None, None, None, None, 0.90)
        self.assertDictContainsSubset(
            {'objectId': f'[{test_alert["objectId"]}](https://mars.lco.global/{test_alert["lco_id"]}/)',
             'ra': '04:00:0.000',
             'dec': '+120:00:0.000',
             'magpsf': '15.1235',  # Number should be truncated to four decimal places
             'rb': '0.8765',  # Number should be truncated to four decimal places
             'alert': test_alert},
            alerts[0])
