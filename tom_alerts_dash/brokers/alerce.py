from astropy.time import Time, TimezoneInfo
from dash.dependencies import Input
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as dhc

from tom_alerts_dash.alerts import GenericDashBroker
from tom_alerts.brokers.alerce import ALeRCEBroker, ALeRCEQueryForm
from tom_common.templatetags.tom_common_extras import truncate_number
from tom_targets.templatetags.targets_extras import deg_to_sexigesimal


class ALeRCEDashBroker(ALeRCEBroker, GenericDashBroker):

    def callback(self, oid, classearly, button_click):
        print('alerce callback')
        if not button_click:
            raise PreventUpdate

        form = ALeRCEQueryForm({
            'query_name': 'ALeRCE Dash Query',
            'broker': self.name,
            'oid': oid,
            'classearly': classearly
        })

        form.is_valid()
        return self._request_alerts(form.cleaned_data)

    def get_callback_inputs(self):
        inputs = super().get_callback_inputs()
        inputs += [
            Input('oid', 'value'),
            Input('classearly', 'value'),
            Input('trigger-filter-btn', 'n_clicks_timestamp')
        ]
        return inputs

    def get_dash_filters(self):
        filters = dhc.Div([
            dbc.Row([
                dcc.Input(
                    id='oid',
                    type='text',
                    placeholder='Object ID',
                    debounce=True
                ),
                dcc.Dropdown(
                    id='classearly',
                    options=[{'label': classifier[1], 'value': classifier[0]}
                             for classifier in ALeRCEQueryForm.early_classifier_choices()
                             if classifier[0] is not None]
                ),
                dbc.Button(
                    'Filter', 
                    id='trigger-filter-btn',
                    outline=True,
                    color='info'
                ),
            ])
        ])
        return filters

    def flatten_dash_alerts(self, alerts):
        flattened_alerts = []
        for alert in alerts:
            url = f'{ALERCE_URL}/object/{alert["oid"]}'
            if alert['pclassrf']:
                classifier_suffix = 'classrf'
                classifier_type = 'late'
            else:
                classifier_suffix = 'classearly'
                classifier_type = 'early'
            classifier_name = ''
            for classifier_dict in ALeRCEQueryForm._get_classifiers()[classifier_type]:
                if classifier_dict['id'] == alert[classifier_suffix]:
                    classifier_name = classifier_dict['name']
            flattened_alerts.append({
                'oid': f'[{alert["oid"]}]({url})',
                'meanra': deg_to_sexigesimal(alert['meanra'], 'hms') if alert['meanra'] else None,
                'meandec': deg_to_sexigesimal(alert['meandec'], 'dms') if alert['meandec'] else None,
                'discovery_date': Time(alert['firstmjd'], format='mjd', scale='utc').to_datetime(),
                'classifier': classifier_name,
                'classifier_type': 'Stamp' if classifier_suffix == 'classearly' else 'Light Curve',
                'classifier_probability': truncate_number(alert[f'p{classifier_suffix}']),
                'alert': alert
            })
        return flattened_alerts

    def get_dash_columns(self):
        return [
            {'id': 'oid', 'name': 'Object ID', 'type': 'text', 'presentation': 'markdown'},
            {'id': 'meanra', 'name': 'Right Ascension', 'type': 'text'},
            {'id': 'meandec', 'name': 'Declination', 'type': 'text'},
            {'id': 'discovery_date', 'name': 'Discovery Date', 'type': 'datetime'},
            {'id': 'classifier', 'name': 'Class', 'type': 'text'},
            {'id': 'classifier_type', 'name': 'Classifier Type', 'type': 'text'},
            {'id': 'classifier_probability', 'name': 'Classifier Probability', 'type': 'text'},
        ]

    def get_dash_data(self, filters):
        alerts = self.filter_alerts(filters)
        return self.flatten_dash_alerts(alerts)
