from astropy.time import Time, TimezoneInfo
from dash.dependencies import Input
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as dhc

from tom_alerts_dash.alerts import GenericDashBroker
from tom_alerts.brokers.alerce import ALeRCEBroker, ALeRCEQueryForm
from tom_common.templatetags.tom_common_extras import truncate_number
from tom_targets.templatetags.targets_extras import deg_to_sexigesimal


class ALeRCEDashBroker(ALeRCEBroker, GenericDashBroker):

    def callback(self, filters_container, classearly, button_click):
        # if not button_click:
        #     raise PreventUpdate
        
        print('filter classback')
        return self._request_alerts({
            'classearly': classearly
        })

    def get_callback_inputs(self):
        inputs = super().get_callback_inputs()
        inputs += [
            # Input('oid', 'value'),
            Input('classearly', 'value'),
            Input('trigger-filter-btn', 'n_clicks_timestamp')
        ]
        return inputs

    def get_dash_filters(self):
        filters = dhc.Div([
            dbc.Row([
                # dcc.Input(
                #     id='oid',
                #     type='text',
                #     placeholder='Object ID',
                #     debounce=True
                # ),
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

    def filter_alerts(self, filters):
        parameters = {'query_name': 'Dash Query', 'broker': self.name, 'nobs__gt': None, 'nobs__lt': 1,
                      'classrf': '', 'pclassrf': None, 'classearly': '', 'pclassearly': None, 'ra': None,
                      'dec': None, 'sr': None, 'mjd__gt': None, 'mjd__lt': None, 'relative_mjd__gt': None,
                      'sort_by': 'lastmjd', 'max_pages': 1, 'records': 20}

        parameters['page'] = filters.get('page_num', 0) + 1  # Dash pages are 0-indexed, ALeRCE is 1-indexed

        if all(k not in filters
               for k in ['oid', 'ra', 'dec', 'discovery_date', 'classifier', 'classifier_probability']):
            parameters['relative_mjd__gt'] = Time(datetime.today() - timedelta(days=7), scale='utc').mjd
            return self.fetch_alerts(parameters)

        parameters['oid'] = filters['oid']['value'] if 'oid' in filters else ''
        if all(k in filters for k in ['ra', 'dec']):
            parameters['ra'] = filters['ra']['value']
            parameters['dec'] = filters['dec']['value']
            parameters['sr'] = 1
        if 'discovery_date' in filters:
            date_range = filters['discovery_date']['value'].strip('\"').split(' - ')
            parameters['mjd__gt'] = Time(parse(date_range[0]), format='datetime', scale='utc').mjd
            if len(date_range) >= 2:
                parameters['mjd__lt'] = Time(parse(date_range[1]), format='datetime', scale='utc').mjd
        if 'classifier' in filters:
            classifier_id = None
            classifier_type = ''
            for key, classifier_list in ALeRCEQueryForm._get_classifiers().items():
                for classifier_dict in classifier_list:
                    if filters['classifier']['value'] == classifier_dict['name']:
                        classifier_id = classifier_dict['id']
                        classifier_type = key
                        break
            parameters['classrf'] = classifier_id if classifier_type == 'late' else ''
            parameters['classearly'] = classifier_id if classifier_type == 'early' else ''
        if 'classifier_probability' in filters:
            parameters['classrf'] = filters['classifier_probability']['value']
            parameters['classearly'] = filters['classifier_probability']['value']  # TODO: this will return nothing

        return self.fetch_alerts(parameters)

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
