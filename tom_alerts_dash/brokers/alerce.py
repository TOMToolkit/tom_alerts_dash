import logging

from astropy.time import Time, TimezoneInfo
from dash.dependencies import Input
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as dhc

from tom_alerts_dash.alerts import GenericDashBroker
from tom_alerts.brokers.alerce import ALeRCEBroker, ALeRCEQueryForm, ALERCE_URL
from tom_common.templatetags.tom_common_extras import truncate_number
from tom_targets.templatetags.targets_extras import deg_to_sexigesimal

logger = logging.getLogger(__name__)


class ALeRCEDashBroker(ALeRCEBroker, GenericDashBroker):
    dash_button_clicks = 0

    def callback(self, page_current, page_size, oid, classearly, pclassearly, classrf, pclassrf, ra, dec, sr,
                 button_click):
        logger.info('Entering ALeRCE callback...')
        if not button_click or button_click == self.btn_clicks:
            raise PreventUpdate
        else:
            self.dash_button_clicks = button_click

        form = ALeRCEQueryForm({
            'query_name': 'ALeRCE Dash Query',
            'broker': self.name,
            'oid': oid,
            'classearly': classearly,
            'ra': ra,
            'dec': dec,
            'sr': sr
        })
        form.is_valid()
        parameters = form.cleaned_data
        parameters['page'] = page_current + 1  # Dash pagination is 0-indexed, but Skip is 1-indexed
        parameters['records_per_pages'] = page_size if page_size else 20  # 20 is the Dash default page size

        alerts = [alert_data for alert, alert_data in self._request_alerts(form.cleaned_data)['result'].items()]
        return self.flatten_dash_alerts(alerts)

    def get_callback_inputs(self):
        inputs = super().get_callback_inputs()
        inputs += [
            Input('oid', 'value'),
            Input('classearly', 'value'),
            Input('pclassearly', 'value'),
            Input('classrf', 'value'),
            Input('pclassrf', 'value'),
            Input('ra', 'value'),
            Input('dec', 'value'),
            Input('sr', 'value'),
            Input('trigger-filter-btn', 'n_clicks')
        ]
        return inputs

    def get_dash_filters(self):
        filters = dhc.Div([
            dbc.Row([
                dbc.Col(dcc.Input(
                    id='oid',
                    type='text',
                    placeholder='Object ID',
                    debounce=True
                )),
            ], style={'padding-bottom': '10px'}),
            dbc.Row([
                dbc.Col(dcc.Dropdown(
                    id='classearly',
                    placeholder='Early Classifier',
                    options=[{'label': classifier[1], 'value': classifier[0]}
                             for classifier in ALeRCEQueryForm.early_classifier_choices()
                             if classifier[0] is not None]
                )),
                dbc.Col(dcc.Input(
                    id='pclassearly',
                    type='number',
                    placeholder='Early Classifier Probability',
                )),
                dbc.Col(dcc.Dropdown(
                    id='classrf',
                    placeholder='Late Classifier',
                    options=[{'label': classifier[1], 'value': classifier[0]}
                             for classifier in ALeRCEQueryForm.late_classifier_choices()
                             if classifier[0] is not None]
                )),
                dbc.Col(dcc.Input(
                    id='pclassrf',
                    type='number',
                    placeholder='Late Classifier Probability',
                )),
            ], style={'padding-bottom': '10px'}, justify='start'),
            dbc.Row([
                dbc.Col(dcc.Input(
                    id='ra',
                    type='text',
                    placeholder='Right Ascension',
                ), width=3),
                dbc.Col(dcc.Input(
                    id='dec',
                    type='text',
                    placeholder='Declination',
                ), width=3),
                dbc.Col(dcc.Input(
                    id='sr',
                    type='text',
                    placeholder='Search Radius',
                ), width=3)
            ], style={'padding-bottom': '10px'}, justify='start'),
            dbc.Row([
                dbc.Col(dbc.Button(
                    'Filter', 
                    id='trigger-filter-btn',
                    outline=True,
                    color='info'
                )),
            ], style={'padding-bottom': '10px'})
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
