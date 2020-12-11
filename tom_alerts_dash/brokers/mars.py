import logging

from dash.dependencies import Input
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_html_components as dhc
import dash_core_components as dcc

from tom_alerts_dash.alerts import GenericDashBroker
from tom_alerts.brokers.mars import MARSBroker, MARSQueryForm, MARS_URL
from tom_common.templatetags.tom_common_extras import truncate_number
from tom_targets.templatetags.targets_extras import deg_to_sexigesimal

logger = logging.getLogger(__name__)


class MARSDashBroker(MARSBroker, GenericDashBroker):

    # TODO: don't trigger callback unless all of ra/dec/cone are populated
    def callback(self, page_current, page_size, objectId, cone_ra, cone_dec, cone_radius, magpsf__gte, rb__gte):
        logger.info('Entering MARS callback...')
        cone_search = ''
        if any([cone_ra, cone_dec, cone_radius]):
            if all([cone_ra, cone_dec, cone_radius]):
                cone_search = ','.join([cone_ra, cone_dec, cone_radius])
            else:
                raise PreventUpdate

        form = MARSQueryForm({
            'query_name': 'dash query',
            'broker': self.name,
            'objectId': objectId,
            'magpsf__gte': magpsf__gte,
            'rb__gte': rb__gte,
            'cone': cone_search
        })
        form.is_valid()

        parameters = form.cleaned_data
        parameters['page'] = page_current + 1  # Dash pagination is 0-indexed, but MARS is 1-indexed

        alerts = self._request_alerts(parameters)['results']
        return self.flatten_dash_alerts(alerts)


    def get_callback_inputs(self):
        inputs = super().get_callback_inputs()
        inputs += [
            Input('objname-search', 'value'),
            Input('cone-ra', 'value'),
            Input('cone-dec', 'value'),
            Input('cone-radius', 'value'),
            Input('magpsf-min', 'value'),
            Input('rb-min', 'value'),
        ]
        return inputs

    def get_dash_filters(self):
        filters = dhc.Div([
            dbc.Row([
                dbc.Col(dcc.Input(
                    id='objname-search',
                    type='text',
                    placeholder='Object Name Search',
                    debounce=True
                ), width=3),
                dbc.Col(dcc.Input(
                    id='magpsf-min',
                    type='number',
                    placeholder='Magnitude Minimum',
                    debounce=True
                ), width=3),
                dbc.Col(dcc.Input(
                    id='rb-min',
                    type='number',
                    placeholder='Real-Bogus Minimum',
                    debounce=True
                ), width=3)
            ], style={'padding-bottom': '10px'}, justify='start'),
            dbc.Row([
                dbc.Col(dcc.Input(
                    id='cone-ra',
                    type='text',
                    placeholder='Right Ascension',
                    debounce=True
                ), width=3),
                dbc.Col(dcc.Input(
                    id='cone-dec',
                    type='text',
                    placeholder='Declination',
                    debounce=True
                ), width=3),
                dbc.Col(dcc.Input(
                    id='cone-radius',
                    type='text',
                    placeholder='Radius',
                    debounce=True
                ), width=3)
            ], style={'padding-bottom': '10px'}, justify='start')
        ])
        return filters

    def get_dash_columns(self):
        return [
            {'id': 'objectId', 'name': 'Name', 'type': 'text', 'presentation': 'markdown'},
            {'id': 'ra', 'name': 'Right Ascension', 'type': 'text'},
            {'id': 'dec', 'name': 'Declination', 'type': 'text'},
            {'id': 'magpsf', 'name': 'Magnitude', 'type': 'text'},
            {'id': 'rb', 'name': 'Real-Bogus Score', 'type': 'text'},
        ]

    def flatten_dash_alerts(self, alerts):
        flattened_alerts = []
        for alert in alerts:
            url = f'{MARS_URL}/{alert["lco_id"]}/'
            flattened_alerts.append({
                'objectId': f'[{alert["objectId"]}]({url})',
                'ra': deg_to_sexigesimal(alert['candidate']['ra'], 'hms'),
                'dec': deg_to_sexigesimal(alert['candidate']['dec'], 'dms'),
                'magpsf': truncate_number(alert['candidate']['magpsf']),
                'rb': truncate_number(alert['candidate']['rb']),
                'alert': alert
            })
        return flattened_alerts
