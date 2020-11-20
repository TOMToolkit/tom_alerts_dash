import dash_bootstrap_components as dbc
import dash_core_components as dcc

from tom_alerts_dash.alerts import GenericDashBroker
from tom_alerts.brokers.mars import MARSBroker, MARS_URL
from tom_common.templatetags.tom_common_extras import truncate_number
from tom_targets.templatetags.targets_extras import deg_to_sexigesimal


class MARSDashBroker(MARSBroker, GenericDashBroker):

    def get_dash_filters(self):
        return dcc.Input(
                id={'type': 'broker-filter'},
                type='text',
                placeholder='Object Name Search',
                debounce=True
            )
        # return dbc.Row([
        #     dbc.Col(dcc.Input(
        #         id={'type': 'broker-filter'},
        #         type='text',
        #         placeholder='Object Name Search',
        #         debounce=True
        #     )),
        #     dbc.Col(dcc.Input(
        #         id={'type': 'broker-filter'},
        #         type='number',
        #         placeholder='Real-Bogus Minimum',
        #         debounce=True
        #     ))
        # ])

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

    def filter_alerts(self, filters):
        parameters = {}
        parameters['page'] = filters.get('page_num', 0) + 1  # Dash pages are 0-indexed, MARS is 1-indexed
        filter_mapping = {'>': 'gt', '>=': 'gt', '<': 'lt', '<=': 'lt'}
        parameters['objectId'] = filters.get('objectId', {}).get('value')
        for key in ['ra', 'dec', 'magpsf']:
            if key in filters:
                filter_expression = filter_mapping[filters[key]['operator']]
                parameters[f'{key}__{filter_expression}'] = filters[key]['value']
        parameters['rb__gte'] = filters.get('rb', '')

        alerts = self.fetch_alerts(parameters)  # TODO: this returns an iterator--how to find number of pages?
        return alerts

    def get_dash_columns(self):
        return [
            {'id': 'objectId', 'name': 'Name', 'type': 'text', 'presentation': 'markdown'},
            {'id': 'ra', 'name': 'Right Ascension', 'type': 'text'},
            {'id': 'dec', 'name': 'Declination', 'type': 'text'},
            {'id': 'magpsf', 'name': 'Magnitude', 'type': 'text'},
            {'id': 'rb', 'name': 'Real-Bogus Score', 'type': 'text'},
        ]

    def get_dash_data(self, filters):
        alerts = self.filter_alerts(filters)
        return self.flatten_dash_alerts(alerts)
