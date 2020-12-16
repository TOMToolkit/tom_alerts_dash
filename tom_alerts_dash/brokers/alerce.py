import logging

from astropy.time import Time
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
        """
        ALeRCE-specific callback function for BrokerQueryBrowseView. Queries ALeRCE based on parameters from DataTable
        inputs. The callback will not trigger a query unless the "Filter" button is clicked, due to the fact that ALeRCE
        queries run very long.

        :param page_current: Currently selected page
        :type page_current: int

        :param page_size: Page size for pagination. Not currently used.
        :type page_size: int

        :param oid: ZTF objectId to search for
        :type oid: string

        :param ra: Right Ascension to use in cone search
        :type ra: string

        :param classearly: Stamp classification to filter by
        :param classearly: string

        :param pclassearly: Probability of stamp classification specified by classrf filter
        :param pclassearly: string

        :param classrf: Light curve classification to filter by
        :param classrf: string

        :param pclassrf: Probability of light curve classification specified by classrf filter
        :param pclassrf: string

        :param dec: Declination to use in cone search
        :type dec: string

        :param sr: Radius to use in cone search, in degrees
        :type sr: string

        :param button_click: Number of times the filter-button has been clicked
        :param button_click: int

        :returns: list of flattened alerts
        :rtype: list of dicts

        :raises: PreventUpdate exception if some but not all cone search parameters are submitted
        """
        logger.info('Entering ALeRCE callback...')
        errors = self.validate_filters(page_current, page_size, oid, classearly, pclassearly, classrf, pclassrf, ra,
                                       dec, sr, button_click, [])

        # Dash does not return the state of a button, but rather the number of clicks. To determine if the callback was
        # triggered by a new button click, the broker tracks the number of clicks, and we check that it has changed
        # before querying ALeRCE.
        if not button_click or button_click == self.dash_button_clicks or errors:
            raise PreventUpdate
        else:
            self.dash_button_clicks = button_click

        form = ALeRCEQueryForm({
            'query_name': 'ALeRCE Dash Query',
            'broker': self.name,
            'oid': oid,
            'classearly': classearly,
            'pclassearly': pclassearly,
            'classrf': classrf,
            'pclassrf': pclassrf,
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
        """
        Returns SCIMMA-specific inputs used to trigger callback function.

        :returns: list of inputs corresponding to dash filters
        :rtype: list
        """
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
        """
        Returns SCIMMA-specific filter inputs layout

        :returns: layout of Dash input components
        :rtype: dash_html_components.Div
        """
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
                    debounce=True
                ), width=3),
                dbc.Col(dcc.Input(
                    id='dec',
                    type='text',
                    placeholder='Declination',
                    debounce=True
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

    def get_dash_columns(self):
        """
        Returns ALeRCE-specific Dash DataTable columns.

        :returns: columns for display
        :rtype: list of dicts
        """
        return [
            {'id': 'oid', 'name': 'Object ID', 'type': 'text', 'presentation': 'markdown'},
            {'id': 'meanra', 'name': 'Right Ascension', 'type': 'text'},
            {'id': 'meandec', 'name': 'Declination', 'type': 'text'},
            {'id': 'discovery_date', 'name': 'Discovery Date', 'type': 'datetime'},
            {'id': 'classifier', 'name': 'Class', 'type': 'text'},
            {'id': 'classifier_type', 'name': 'Classifier Type', 'type': 'text'},
            {'id': 'classifier_probability', 'name': 'Classifier Probability', 'type': 'text'},
        ]

    def flatten_dash_alerts(self, alerts):
        """
        Transforms alerts returned by ALeRCE into a Dash DataTable format. Adds an embedded link to the original alert.
        Converts decimal degrees to sexagesimal. Truncates decimals to 4 places. Converts MJD value to datetime.
        Includes light curve classifier if it exists, and stamp classifier otherwise. Displays classifier name instead
        of classifier number.

        :param alerts: dict of alerts from ALeRCE
        :type alerts: dict of dicts

        :returns: flattened alerts
        :rtype: list of dicts
        """
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

    def validate_filters(self, page_current, page_size, oid, classearly, pclassearly, classrf, pclassrf, ra, dec, sr,
                         button_click, errors_state):
        """
        Validates the input filters for ALeRCE. Returns an error if one, but not all, of RA, Dec, and radius are
        submitted for cone search. Returns any errors generated by form validation.

        :param page_current: The page number for the paginated alerts to display
        :type page_current: int

        :param page_size: The page size used for the pagination
        :type page_size: int

        :param oid: ZTF objectId to search for
        :type oid: string

        :param classearly: Stamp classification to filter by
        :param classearly: string

        :param pclassearly: Probability of stamp classification specified by classrf filter
        :param pclassearly: string

        :param classrf: Light curve classification to filter by
        :param classrf: string

        :param pclassrf: Probability of light curve classification specified by classrf filter
        :param pclassrf: string

        :param ra: Right Ascension to use in cone search
        :type ra: string

        :param dec: Declination to use in cone search
        :type dec: string

        :param sr: Radius to use in cone search, in degrees
        :type sr: string

        :param button_click: Number of times the filter-button has been clicked
        :param button_click: int

        :param errors_state: The currently displayed errors relating to filters
        :type errors_state: list of dbc.Alert objects

        :returns: errors from validation of filters
        :rtype: list of dbc.Alert objects
        """
        errors = []

        if not button_click or button_click == self.dash_button_clicks:
            raise PreventUpdate

        form = ALeRCEQueryForm({
            'query_name': 'ALeRCE Dash Query',
            'broker': self.name,
            'oid': oid,
            'classearly': classearly,
            'pclassearly': pclassearly,
            'classrf': classrf,
            'pclassrf': pclassrf,
            'ra': ra,
            'dec': dec,
            'sr': sr
        })
        form.is_valid()

        for field, field_errors in form.errors.items():
            for field_error in field_errors.get_json_data():
                errors.append(f'{field}: {field_error["message"]}')

        for error in errors:
            errors_state.append(dbc.Alert(error, dismissable=True, is_open=True, duration=5000, color='warning'))

        return errors_state
