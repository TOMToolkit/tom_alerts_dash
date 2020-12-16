from inspect import signature
from unittest.mock import patch

from dash.exceptions import PreventUpdate
from django.test import TestCase

from tom_alerts_dash.brokers.scimma import SCIMMADashBroker
from tom_alerts_dash.tests.factories import create_scimma_alert, SiderealTargetFactory


class TestSCIMMADashBroker(TestCase):

    def setUp(self):
        self.broker = SCIMMADashBroker()

        self.test_target = SiderealTargetFactory.create()
        self.test_alerts = [create_scimma_alert() for i in range(0, 5)]

    def test_flatten_dash_alerts(self):
        test_alert = create_scimma_alert()
        flattened_alerts = self.broker.flatten_dash_alerts([test_alert])
        for key in ['alert_identifier', 'counterpart_identifier', 'ra', 'dec', 'rank', 'comments']:
            self.assertIn(key, flattened_alerts[0])
        for key in ['topic', 'test_bad_key']:
            self.assertNotIn(key, flattened_alerts[0])  # Test that no unwanted attributes are included

        expected_url = f'https://gracedb.ligo.org/superevents/{test_alert["message"]["event_trig_num"]}/view/'
        self.assertDictContainsSubset(
            {'alert_identifier': f'[{test_alert["alert_identifier"]}]({expected_url})',
             'counterpart_identifier': test_alert['extracted_fields']['counterpart_identifier'],
             'ra': test_alert['right_ascension_sexagesimal'],
             'dec': test_alert['declination_sexagesimal'],
             'rank': test_alert['message']['rank'],
             'comments': test_alert['extracted_fields']['comment_warnings'],
             'alert': test_alert},
            flattened_alerts[0])

    def test_callback_partial_cone_search(self):
        with self.assertRaises(PreventUpdate):
            self.broker.callback(1, 20, '', '', '100', None, None, None, None)

    @patch('tom_scimma.scimma.SCIMMABroker._request_alerts')
    def test_callback_full_cone_search(self, mock_request_alerts):
        mock_request_alerts.return_value = {'results': self.test_alerts}
        alerts = self.broker.callback(1, 20, '', '', '100', '100', '100', None, None)

        self.assertDictContainsSubset({'cone_search': '100,100,100'}, mock_request_alerts.call_args.args[0])
        for key in ['alert_identifier', 'counterpart_identifier', 'ra', 'dec', 'rank', 'comments']:
            self.assertIn(key, alerts[0])
        for key in ['topic', 'test_bad_key']:
            self.assertNotIn(key, alerts[0])  # Test that no unwanted attributes are included

    def test_validate_filters(self):
        errors = self.broker.validate_filters(1, 20, '', '', '100', None, None, None, None, [])
        self.assertIn('All of RA, Dec, and Radius are required for a cone search.', errors[0].children)

    def test_callback_parameters_match_inputs(self):
        """Test that callback function has the same number of parameters as the inputs."""
        callback_num_params = len(signature(self.broker.callback).parameters)
        inputs = self.broker.get_callback_inputs()
        self.assertEqual(callback_num_params, len(inputs))

    def test_inputs_match_filters(self):
        callback_inputs = self.broker.get_callback_inputs()
        dash_filters = self.broker.get_dash_filters()
        for callback_input in callback_inputs:
            if callback_input.component_property in ['page_current', 'page_size']:
                continue
            with self.subTest():
                found = False
                for row in dash_filters.children:
                    for column in row.children:
                        for input_obj in column:
                            if input_obj == callback_input.component_id:
                                found = True
                self.assertTrue(found)
