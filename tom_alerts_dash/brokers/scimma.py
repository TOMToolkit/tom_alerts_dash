from datetime import datetime
import logging

from dash.dependencies import Input
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_html_components as dhc
import dash_core_components as dcc

from tom_alerts_dash.alerts import GenericDashBroker
from tom_scimma.scimma import SCIMMABroker, SCIMMAQueryForm

logger = logging.getLogger(__name__)

GRACE_DB_URL = 'https://gracedb.ligo.org'


# TODO: how will this jive with tom_scimma as a non-default?
# TODO: should external apps have pip "extras" such as `pip install tom_alerts_dash[scimma]`?
# TODO: or should tom_scimma be a dependency of tom_alerts_dash?
class SCIMMADashBroker(SCIMMABroker, GenericDashBroker):

    def callback(self, page_current, page_size, event_trigger_number, keyword, cone_ra, cone_dec, cone_radius,
                 start_date, end_date):
        """
        SCIMMA-specific callback function for BrokerQueryBrowseView. Queries SCIMMA based on parameters from DataTable
        inputs. The callback will not modify any bound components if one or more, but not all, cone search inputs are
        submitted.

        :param page_current: Currently selected page
        :type page_current: int

        :param page_size: Page size for pagination. Not currently used.
        :type page_size: int

        :param event_trigger_number: Event trigger number to search for
        :type event_trigger_number: string

        :param keyword: Keyword to search for
        :type keyword: string

        :param cone_ra: Right Ascension to use in cone search
        :type cone_ra: string

        :param cone_dec: Declination to use in cone search
        :type cone_dec: string

        :param cone_radius: Radius to use in cone search, in degrees
        :type cone_radius: string

        :param start_date: Earliest date to filter by
        :param start_date: string

        :param end_date: Latest date to filter by
        :param end_date: string

        :returns: list of flattened alerts
        :rtype: list of dicts

        :raises: PreventUpdate exception if some but not all cone search parameters are submitted
        """
        logger.info('Entering SCIMMA callback...')
        cone_search = ''
        if any([cone_ra, cone_dec, cone_radius]):
            if all([cone_ra, cone_dec, cone_radius]):
                cone_search = ','.join([cone_ra, cone_dec, cone_radius])
            else:
                raise PreventUpdate

        form = SCIMMAQueryForm({
            'query_name': 'SCIMMA Dash Query',
            'broker': self.name,
            'keyword': keyword,
            'cone_search': cone_search,
            'event_trigger_number': event_trigger_number,
            'alert_timestamp_after': start_date,
            'alert_timestamp_before': end_date,
        })
        form.is_valid()

        parameters = form.cleaned_data
        parameters['topic'] = 3  # form isn't valid with both topic and event trigger number, so this circumvents that
        parameters['page'] = page_current + 1  # Dash pagination is 0-indexed, but Skip is 1-indexed
        parameters['page_size'] = page_size if page_size else 20  # 20 is the Dash default page size
        alerts = self._request_alerts(parameters)['results']
        return self.flatten_dash_alerts(alerts)

    def get_callback_inputs(self):
        """
        Returns SCIMMA-specific inputs used to trigger callback function.

        :returns: list of inputs corresponding to dash filters
        :rtype: list
        """
        inputs = super().get_callback_inputs()
        inputs += [
            Input('keyword', 'value'),
            Input('event-trigger-number', 'value'),
            Input('scimma-ra', 'value'),
            Input('scimma-dec', 'value'),
            Input('scimma-radius', 'value'),
            Input('date-filter', 'start_date'),
            Input('date-filter', 'end_date'),
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
                    id='keyword',
                    type='text',
                    placeholder='Keyword Search',
                    debounce=True
                ), width=3),
                dbc.Col(dcc.Input(
                    id='event-trigger-number',
                    type='text',
                    placeholder='LVC Trigger Number',
                    debounce=True
                ), width=3)
            ], style={'padding-bottom': '10px'}, justify='start'),
            dbc.Row([
                dbc.Col(dcc.Input(
                    id='scimma-ra',
                    type='text',
                    placeholder='Right Ascension',
                    debounce=True
                ), width=3),
                dbc.Col(dcc.Input(
                    id='scimma-dec',
                    type='text',
                    placeholder='Declination',
                    debounce=True
                ), width=3),
                dbc.Col(dcc.Input(
                    id='scimma-radius',
                    type='text',
                    placeholder='Radius',
                    debounce=True
                ), width=3)
            ], style={'padding-bottom': '10px'}, justify='start'),
            dbc.Row([
                dbc.Col(dcc.DatePickerRange(
                    id='date-filter',
                    min_date_allowed=datetime(2020, 1, 1),
                    initial_visible_month=datetime.now(),
                    clearable=True
                ))
            ], style={'padding-bottom': '10px'}, justify='start'),
        ])
        return filters

    def get_dash_columns(self):
        """
        Returns SCIMMA-specific Dash DataTable columns.

        :returns: columns for display
        :rtype: list of dicts
        """
        return [
            {'id': 'alert_identifier', 'name': 'Alert Identifier', 'type': 'text', 'presentation': 'markdown'},
            {'id': 'counterpart_identifier', 'name': 'Counterpart Identifier', 'type': 'text'},
            {'id': 'ra', 'name': 'Right Ascension', 'type': 'text'},
            {'id': 'dec', 'name': 'Declination', 'type': 'text'},
            {'id': 'rank', 'name': 'Rank', 'type': 'text'},
            {'id': 'comments', 'name': 'Comments', 'type': 'text'}
        ]

    def flatten_dash_alerts(self, alerts):
        """
        Transforms alerts returned by SCIMMA into a Dash DataTable format. Adds an embedded link to the original alert.
        Converts decimal degrees to sexagesimal.

        :param alerts: list of alerts from SCIMMA
        :type alerts: list of dicts

        :returns: flattened alerts
        :rtype: list of dicts
        """
        flattened_alerts = []
        for alert in alerts:
            url = f'{GRACE_DB_URL}/superevents/{alert["message"]["event_trig_num"]}/view/'
            flattened_alerts.append({
                'alert_identifier': f'[{alert["alert_identifier"]}]({url})',
                'counterpart_identifier': alert['extracted_fields']['counterpart_identifier'],
                'ra': alert['right_ascension_sexagesimal'],
                'dec': alert['declination_sexagesimal'],
                'rank': alert['message']['rank'],
                'comments': alert['extracted_fields']['comment_warnings'],
                'alert': alert
            })
        return flattened_alerts
