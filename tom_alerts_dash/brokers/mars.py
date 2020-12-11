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
    def callback(self, objectId, cone_ra, cone_dec, cone_radius, magpsf__gte, rb__gte):
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

        alerts = self._request_alerts(form.cleaned_data)['results']
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

    # TODO: make this look less ugly
    def get_dash_filters(self):
        filters = dhc.Div([
            dbc.Row([
                dbc.Col(dcc.Input(
                    id='objname-search',
                    type='text',
                    placeholder='Object Name Search',
                    debounce=True
                )),
                dbc.Col(dcc.Input(
                    id='magpsf-min',
                    type='number',
                    placeholder='Magnitude Minimum',
                    debounce=True
                )),
                dbc.Col(dcc.Input(
                    id='rb-min',
                    type='number',
                    placeholder='Real-Bogus Minimum',
                    debounce=True
                ))
            ]),
            dbc.Row([
                dbc.Col(dcc.Input(
                    id='cone-ra',
                    type='text',
                    placeholder='Right Ascension',
                    debounce=True
                )),
                dbc.Col(dcc.Input(
                    id='cone-dec',
                    type='text',
                    placeholder='Declination',
                    debounce=True
                )),
                dbc.Col(dcc.Input(
                    id='cone-radius',
                    type='text',
                    placeholder='Radius',
                    debounce=True
                ))
            ])
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

    # def filter_alerts(self, filters):
    #     parameters = {}
    #     parameters['page'] = filters.get('page_num', 0) + 1  # Dash pages are 0-indexed, MARS is 1-indexed
    #     filter_mapping = {'>': 'gt', '>=': 'gt', '<': 'lt', '<=': 'lt'}
    #     parameters['objectId'] = filters.get('objectId', {}).get('value')
    #     for key in ['ra', 'dec', 'magpsf']:
    #         if key in filters:
    #             filter_expression = filter_mapping[filters[key]['operator']]
    #             parameters[f'{key}__{filter_expression}'] = filters[key]['value']
    #     parameters['rb__gte'] = filters.get('rb', '')

    #     alerts = self.fetch_alerts(parameters)  # TODO: this returns an iterator--how to find number of pages?
    #     return alerts

    def get_dash_data(self, filters):
        alerts = self._request_alerts(filters)['results']
        return self.flatten_dash_alerts(alerts)
