from http import HTTPStatus
from unittest.mock import patch

from dash.dependencies import Input
from dash.exceptions import PreventUpdate
import dash_core_components as dcc
import dash_html_components as dhc
from django.test import override_settings, TestCase
from django.urls import reverse

from tom_alerts_dash.alerts import GenericDashBroker
from tom_alerts_dash.dash_apps.query_list_app import broker_selection_callback, create_broker_container, create_targets
from tom_targets.models import Target


class TestDashBroker(GenericDashBroker):
    name = 'Test Broker'

    def callback(self, page_current, page_size, test_input):
        return [
            {'test_key': test_input}
        ]

    def fetch_alerts(self):
        return []

    def get_callback_inputs(self):
        inputs = super().get_callback_inputs()
        return inputs + [Input('test-input', 'value')]

    def get_dash_filters(self):
        return dhc.Div([
            dcc.Input(
                id='test-input',
                type='text'
            )
        ])

    def get_dash_columns(self):
        return [{'id': 'test_key', 'name': 'Test Key', 'type': 'text'}]

    def to_generic_alert(self):
        return


class TestDashViews(TestCase):

    def setUp(self):
        pass

    def test_broker_query_list_view(self):
        """Test that the tom_alerts_dash ListView is used rather than the tom_alerts ListView."""
        response = self.client.get(reverse('tom_alerts_dash:list'))
        self.assertContains(response, 'Browse Alerts')

    def test_broker_query_browse_view(self):
        """Test that the BrokerQueryBrowseView loads."""
        response = self.client.get(reverse('tom_alerts_dash:browse'))
        self.assertEqual(response.status_code, HTTPStatus.OK)


@override_settings(TOM_ALERT_DASH_CLASSES=['tom_alerts_dash.tests.tests.TestDashBroker'])
class TestQueryListApp(TestCase):

    def setUp(self):
        pass

    def test_create_broker_container(self):
        broker_container = create_broker_container('Test Broker')
        for key in ['create-targets-btn-Test Broker', 'alerts-table-Test Broker']:
            self.assertIn(key, broker_container)
        self.assertEqual(broker_container.style, {'display': 'none'})

    @patch('tom_alerts_dash.dash_apps.query_list_app.reverse')
    @patch('tom_alerts_dash.tests.tests.TestDashBroker.to_target')
    def test_create_targets(self, mock_to_target, mock_reverse):
        mock_reverse.return_value = 'http://localhost:8000/targets/1/'

        params = [('', [1, 2], [], 'Test Broker', []), (1, [], [], 'Test Broker', [])]
        for param in params:
            with self.subTest():
                with self.assertRaises(PreventUpdate):
                    create_targets(*param)

        mock_to_target.side_effect = lambda target: target
        rows = [{'alert': Target(id=1, name='test1')}, {'alert': None}]
        with self.subTest():
            messages = create_targets(1, [0], rows, 'Test Broker', [])
            self.assertIn('Successfully created ', messages[0].children)

        with self.subTest():
            messages = create_targets(1, [1], rows, 'Test Broker', [])
            self.assertIn('Unable to create target from alert.', messages[0].children)

    def test_broker_selection_callback(self):
        params = [('', ''), ('Test Broker', 'Test Broker')]
        for param in params:
            with self.subTest():
                with self.assertRaises(PreventUpdate):
                    broker_selection_callback(*param)

        with self.subTest():
            callback_return_values = broker_selection_callback('Test Broker', '')
            self.assertEqual('Test Broker', callback_return_values[0])
            self.assertEqual('Test Broker Alerts', callback_return_values[1].children)
            self.assertDictEqual({'display': 'block'}, callback_return_values[2])

        with self.subTest():
            callback_return_values = broker_selection_callback('Other Broker', 'Test Broker')
            self.assertDictEqual({'display': 'none'}, callback_return_values[2])
