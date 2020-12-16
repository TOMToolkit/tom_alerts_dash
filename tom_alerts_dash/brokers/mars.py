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

    def callback(self, page_current, page_size, objectId, cone_ra, cone_dec, cone_radius, magpsf_lte, rb_gte):
        """
        MARS-specific callback function for BrokerQueryBrowseView. Queries MARS based on parameters from DataTable
        inputs. The callback will not modify any bound components if one or more, but not all, cone search inputs are
        submitted, or if the form validation fails.

        :param page_current: Currently selected page
        :type page_current: int

        :param page_size: Page size for pagination. Not currently used.
        :type page_size: int

        :param objectId: ZTF objectId to search for
        :type objectId: string

        :param cone_ra: Right Ascension to use in cone search
        :type cone_ra: string

        :param cone_dec: Declination to use in cone search
        :type cone_dec: string

        :param cone_radius: Radius to use in cone search, in degrees
        :type cone_radius: string

        :param magpsf_lte: Maximum magnitude to filter by
        :param magpsf_lte: string

        :param rb_gte: Minimum real-bogus score to filter by
        :param rb_gte: string

        :returns: list of flattened alerts
        :rtype: list of dicts

        :raises: PreventUpdate exception if some but not all cone search parameters are submitted
        """
        logger.info('Entering MARS callback...')
        errors = self.validate_filters(page_current, page_size, objectId, cone_ra, cone_dec, cone_radius, magpsf_lte,
                                       rb_gte, [])
        if errors:
            raise PreventUpdate

        cone_search = ''
        if all([cone_ra, cone_dec, cone_radius]):
            cone_search = ','.join([cone_ra, cone_dec, cone_radius])
        form = MARSQueryForm({
            'query_name': 'dash query',
            'broker': self.name,
            'objectId': objectId,
            'magpsf__lte': magpsf_lte,
            'rb__gte': rb_gte,
            'cone': cone_search
        })
        form.is_valid()

        parameters = form.cleaned_data
        parameters['page'] = page_current + 1  # Dash pagination is 0-indexed, but MARS is 1-indexed

        alerts = self._request_alerts(parameters)['results']
        return self.flatten_dash_alerts(alerts)

    def get_callback_inputs(self):
        """
        Returns MARS-specific inputs used to trigger callback function.

        :returns: list of inputs corresponding to dash filters
        :rtype: list
        """
        inputs = super().get_callback_inputs()
        inputs += [
            Input('objname-search', 'value'),
            Input('cone-ra', 'value'),
            Input('cone-dec', 'value'),
            Input('cone-radius', 'value'),
            Input('magpsf-max', 'value'),
            Input('rb-min', 'value'),
        ]
        return inputs

    def get_dash_filters(self):
        """
        Returns MARS-specific filter inputs layout

        :returns: layout of Dash input components
        :rtype: dash_html_components.Div
        """
        filters = dhc.Div([
            dbc.Row([
                dbc.Col(dcc.Input(
                    id='objname-search',
                    type='text',
                    placeholder='Object Name Search',
                    debounce=True
                ), width=3),
                dbc.Col(dcc.Input(
                    id='magpsf-max',
                    type='number',
                    placeholder='Magnitude Maximum',
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
        """
        Returns MARS-specific Dash DataTable columns.

        :returns: columns for display
        :rtype: list of dicts
        """
        return [
            {'id': 'objectId', 'name': 'Name', 'type': 'text', 'presentation': 'markdown'},
            {'id': 'ra', 'name': 'Right Ascension', 'type': 'text'},
            {'id': 'dec', 'name': 'Declination', 'type': 'text'},
            {'id': 'magpsf', 'name': 'Magnitude', 'type': 'text'},
            {'id': 'rb', 'name': 'Real-Bogus Score', 'type': 'text'},
        ]

    def flatten_dash_alerts(self, alerts):
        """
        Transforms alerts returned by MARS into a Dash DataTable format. Adds an embedded link to the original alert.
        Converts decimal degrees to sexagesimal. Truncates decimals to 4 places.

        :param alerts: list of alerts from MARS
        :type alerts: list of dicts

        :returns: flattened alerts
        :rtype: list of dicts
        """
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

    def validate_filters(self, page_current, page_size, objectId, cone_ra, cone_dec, cone_radius, magpsf_lte, rb_gte,
                         errors_state):
        """
        Validates the input filters for MARS. Returns an error if one, but not all, of RA, Dec, and radius are submitted
        for cone search. Returns any errors generated by form validation.

        :param page_current: The page number for the paginated alerts to display
        :type page_current: int

        :param page_size: The page size used for the pagination
        :type page_size: int

        :param objectId: ZTF objectId to search for
        :type objectId: string

        :param cone_ra: Right Ascension to use in cone search
        :type cone_ra: string

        :param cone_dec: Declination to use in cone search
        :type cone_dec: string

        :param cone_radius: Radius to use in cone search, in degrees
        :type cone_radius: string

        :param magpsf_lte: Maximum magnitude to filter by
        :param magpsf_lte: string

        :param rb_gte: Minimum real-bogus score to filter by
        :param rb_gte: string

        :param errors_state: The currently displayed errors relating to filters
        :type errors_state: list of dbc.Alert objects

        :returns: errors from validation of filters
        :rtype: list of dbc.Alert objects
        """
        errors = []

        cone_search = ''
        if any([cone_ra, cone_dec, cone_radius]):
            if all([cone_ra, cone_dec, cone_radius]):
                cone_search = ','.join([cone_ra, cone_dec, cone_radius])
            else:
                errors.append('All of RA, Dec, and Radius are required for a cone search.')

        form = MARSQueryForm({
            'query_name': 'dash query',
            'broker': self.name,
            'objectId': objectId,
            'magpsf__lte': magpsf_lte,
            'rb__gte': rb_gte,
            'cone': cone_search
        })
        form.is_valid()

        for field, field_errors in form.errors.items():
            for field_error in field_errors.get_json_data():
                errors.append(f'{field}: {field_error["message"]}')

        for error in errors:
            errors_state.append(dbc.Alert(error, dismissable=True, is_open=True, duration=5000, color='warning'))

        return errors_state
