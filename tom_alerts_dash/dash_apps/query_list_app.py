import re

import dash
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as dhc
from dash_table import DataTable
from django.conf import settings
from django_plotly_dash import DjangoDash
from django.shortcuts import reverse

from tom_alerts.alerts import get_service_class, get_service_classes


app = DjangoDash('BrokerQueryListViewDash', external_stylesheets=[dbc.themes.BOOTSTRAP], add_bootstrap_links=True)


class BrokerClient:
    _broker = None

    def __init__(self, broker_name, *args, **kwargs):
        self._broker = get_service_class(broker_name)()

    @property
    def broker(self):
        return self._broker

    @broker.setter
    def broker(self, new_broker_name):
        self._broker = get_service_class(new_broker_name)()

    def get_columns(self):
        return self._broker.get_dash_columns()

    def get_alerts(self, parameters):
        return self._broker.get_dash_data(parameters)


broker_client = BrokerClient('SCIMMA')


app.layout = dbc.Container([
    dhc.Div([
        dhc.Div(
            id='redirection'
        ),
        dhc.Div(
            dhc.H3('Browse Alerts')
        ),
        dhc.Div(
            dhc.P(
                dcc.Dropdown(
                    id='broker-selection',
                    placeholder='Select Broker',
                    options=[{'label': clazz, 'value': clazz} for clazz in get_service_classes().keys()]
                )
            )
        ),
        dhc.Div(
            dhc.P(
                dbc.Button('Create targets from selected', 
                           id='create-targets-btn',
                           className='btn btn-outline-primary'
                )
            )
        ),
        dhc.Div(  # Filters go here
            # dcc.Input(
            #     id='name-search',
            #     type='text',
            #     placeholder='Alert name search',
            #     debounce=True
            # ),
            id='alerts-table-filters-container'
        ),
        dhc.Div(  # Alerts datatable goes here
            DataTable(
                id='alerts-table',
                columns=broker_client.get_columns(),
                data=broker_client.get_alerts({}),
                filter_action='custom',
                row_selectable='multi',
                page_current=0,
                page_size=20,
                page_action='custom',
            ),
            id='alerts-table-container'
        ),
    ])
])


@app.callback(
    [Output('alerts-table', 'columns'),
     Output('alerts-table', 'data')],
    [Input('broker-selection', 'value'),
     Input('alerts-table', 'filter_query')]
)
def alerts_table_filter(broker_selection, filter_query):
    print(filter_query)
    if broker_selection:
        print(broker_selection)
        broker_client.broker = broker_selection

    parameters = {}
    if filter_query:
        for filter_part in filter_query.split(' && '):
            col_name, operator, filter_value = filter_part.split()
            col_name = col_name[col_name.find('{') + 1: col_name.rfind('}')]
            parameters[col_name] = {'operator': operator, 'value': filter_value}
    print(f'parameters: {parameters}')

    return broker_client.get_columns(), broker_client.get_alerts(parameters)


@app.callback(
    Output('redirection', 'children'),
    [Input('alerts-table', 'derived_virtual_selected_rows'),
     Input('alerts-table', 'derived_virtual_data'),
     Input('create-targets-btn', 'n_clicks_timestamp')]
)
def create_targets(selected_rows, row_data, create_targets):
    if create_targets:
        errors = []
        successes = []
        for row in selected_rows:
            print(row_data[row])
            target = broker_client._broker.to_target(row_data[row]['alert'])
            # alert = row_data[row]
            # data = {'ra': alert['right_ascension'], 'dec': alert['declination'], 'type': 'SIDEREAL',
            #         'targetextra_set': [], 'aliases': []}
            # if alert['topic'] == 'lvc-counterpart':
            #     data['name'] = alert['alert_identifier']
            # elif alert['topic'] == 'gcn':
            #     data['name'] = f'SCiMMA-{alert["id"]}'
            # serializer = TargetSerializer(data=data)
            # serializer.is_valid()
            if target:
                successes.append(target.name)
            else:
                errors.append(target.name)
    
        print(create_targets)
        print(successes)

        if successes:
            print('here')
            return dcc.Location(pathname=reverse('tom_targets:list'), id='dash-location')            
