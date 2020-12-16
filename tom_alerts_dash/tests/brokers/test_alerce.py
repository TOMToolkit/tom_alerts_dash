from datetime import datetime
from inspect import signature
from unittest.mock import patch

from dash.exceptions import PreventUpdate
from django.test import TestCase

from tom_alerts_dash.brokers.alerce import ALeRCEDashBroker
from tom_alerts_dash.tests.factories import create_alerce_alert, SiderealTargetFactory


class TestALeRCEDashBroker(TestCase):

    def setUp(self):
        self.broker = ALeRCEDashBroker()
        self.test_target = SiderealTargetFactory.create()

        self.mock_classifiers = {
            'early': [{'name': 'AGN', 'id': 18}, {'name': 'SN', 'id': 19}],
            'late': [{'name': 'AGN-I', 'id': 7}, {'name': 'Blazar', 'id': 8}]
        }

    @patch('tom_alerts.brokers.alerce.ALeRCEQueryForm._get_classifiers')
    def test_flatten_dash_alerts(self, mock_get_classifiers):
        mock_get_classifiers.return_value = self.mock_classifiers

        test_alert_late_class = create_alerce_alert(meanra=60, meandec=120, classrf=7, pclassrf=0.98765)
        test_alert_early_class = create_alerce_alert(firstmjd=59196.441261574075, classearly=19, pclassearly=0.54321)
        test_alert_early_class['pclassrf'] = None
        alerts = [test_alert_late_class,
                  test_alert_early_class]
        flattened_alerts = self.broker.flatten_dash_alerts(alerts)
        for key in ['oid', 'meanra', 'meandec', 'discovery_date', 'classifier', 'classifier_type',
                    'classifier_probability']:
            self.assertIn(key, flattened_alerts[0])
        for key in ['last_mjd', 'test_bad_key']:
            self.assertNotIn('last_mjd', flattened_alerts[0])  # Test that no unwanted attributes are included
        self.assertDictContainsSubset(
            {'oid': f'[{test_alert_late_class["oid"]}](https://alerce.online/object/{test_alert_late_class["oid"]})',
             'meanra': '04:00:0.000',
             'meandec': '+120:00:0.000',
             'classifier': 'AGN-I',
             'classifier_type': 'Light Curve',
             'classifier_probability': '0.9877'},
            flattened_alerts[0]
        )

        self.assertDictContainsSubset(
            {'discovery_date': datetime(2020, 12, 13, 10, 35, 25),
             'classifier': 'SN',
             'classifier_type': 'Stamp',
             'classifier_probability': '0.5432'},
            flattened_alerts[-1])

    def test_callback_no_button_click(self):
        with self.assertRaises(PreventUpdate):
            self.broker.callback(1, 20, None, None, None, None, None, None, None, None, None)

        with self.assertRaises(PreventUpdate):
            self.broker.dash_button_clicks = 1
            self.broker.callback(1, 20, None, None, None, None, None, None, None, None, 1)

    @patch('tom_alerts.brokers.alerce.ALeRCEQueryForm._get_classifiers')
    @patch('tom_alerts.brokers.alerce.ALeRCEBroker._request_alerts')
    def test_callback(self, mock_request_alerts, mock_get_classifiers):
        mock_get_classifiers.return_value = self.mock_classifiers
        test_alerts = [create_alerce_alert() for i in range(0, 5)]
        test_result = {alert['oid']: alert for alert in test_alerts}
        mock_request_alerts.return_value = {'result': test_result}

        alerts = self.broker.callback(1, 20, None, None, None, None, None, None, None, None, 10)
        self.assertEqual(len(alerts), len(test_alerts))
        self.assertEqual(self.broker.dash_button_clicks, 10)

    def test_callback_parameters_match_inputs(self):
        """Test that callback function has the same number of parameters as the inputs."""
        callback_num_params = len(signature(self.broker.callback).parameters)
        inputs = self.broker.get_callback_inputs()
        self.assertEqual(callback_num_params, len(inputs))

    def test_validate_filters(self):
        with self.assertRaises(PreventUpdate):
            self.broker.validate_filters(1, 20, None, None, None, None, None, 100, '', '', None, [])

        errors = self.broker.validate_filters(1, 20, None, None, None, None, None, 100, '', '', 10, [])
        self.assertIn('__all__: All of RA, Dec, and Search Radius must be included to execute a cone search.',
                      errors[0].children)

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
