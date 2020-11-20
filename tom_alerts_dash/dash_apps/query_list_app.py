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

from tom_alerts_dash.alerts import get_service_class, get_service_classes


app = DjangoDash('BrokerQueryListViewDash', external_stylesheets=[dbc.themes.BOOTSTRAP], add_bootstrap_links=True)


class BrokerClient:
    _broker = None

    def __init__(self, broker_name, *args, **kwargs):
        self._broker = get_service_class(broker_name)()

    @property
    def broker(self):
        return self._broker

    @broker.getter
    def broker(self):
        return self._broker.name

    @broker.setter
    def broker(self, new_broker_name):
        self._broker = get_service_class(new_broker_name)()

    def get_filters(self):
        return self._broker.get_dash_filters()

    def get_columns(self):
        return self._broker.get_dash_columns()

    def get_alerts(self, parameters):
        return self._broker.get_dash_data(parameters)


broker_client = BrokerClient('MARS')


app.layout = dbc.Container([
    dhc.Div([
        dhc.Div(
            id='redirection'
        ),
        dhc.Div(
            dhc.H3(f'{broker_client._broker.name} Alerts'),
            id='page-header'
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
                           outline=True,
                           color='info'
                ),
            )
        ),
        dhc.Div(  # Filters go here
            dhc.Form(
                [broker_client.get_filters()],
                id='alerts-table-filters-form',
                action='/post', method='post'
            )
        ),
        dhc.Div(  # Alerts datatable goes here
            dcc.Loading(children=[
                DataTable(
                    id='alerts-table',
                    columns=broker_client.get_columns(),
                    data=broker_client.get_alerts({}),
                    filter_action='custom',
                    row_selectable='multi',
                    page_current=0,
                    page_size=20,
                    page_action='custom',
                    css=[
                        {'selector': '.dash-cell-value', 'rule': 'backgroundColor: blue;'}
                    ],
                    style_cell_conditional=[
                        {
                            # 'if': {'column_id': 'objectId'}, 'backgroundColor': 'blue'
                        }
                    ],
                    style_cell={
                        'textAlign': 'right'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(233, 243, 256)'
                        },
                    ],
                    style_data={'font-family': 'Helvetica Neue, Helvetica, Arial, sans-serif'},
                    style_filter={
                        'font-family': 'Helvetica Neue, Helvetica, Arial, sans-serif',
                        'backgroundColor': 'rgb(256, 233, 233)'
                    },
                    style_header={
                        'backgroundColor': 'rgb(213, 223, 242)', 
                        'font-family': 'Helvetica Neue, Helvetica, Arial, sans-serif',
                        'fontWeight': 'bold'
                    },
                )], type='dot', fullscreen=True
            ),
            id='alerts-table-container'
        ),
    ])
])


@app.callback(
    [Output('alerts-table', 'columns'),
     Output('alerts-table', 'data'),
     Output('alerts-table-filters-container', 'children'),
     Output('page-header', 'children')],
    [Input('broker-selection', 'value'),
     Input('alerts-table', 'filter_query'),
     Input('alerts-table', 'page_current'),
     Input('alerts-table', 'page_size'),
     Input('alerts-table-filters-form', 'data')],
)
def alerts_table_filter(broker_selection, filter_query, page_current, page_size, broker_filters):
    print(filter_query)
    print(broker_filters)
    if broker_selection and broker_selection != broker_client.broker:
        print(broker_selection)
        broker_client.broker = broker_selection
        page_current = 0

    # TODO: Add example filter queries
    parameters = {'page_num': page_current, 'page_size': page_size}
    if filter_query:
        for filter_part in filter_query.split(' && '):
            col_name, operator, filter_value = filter_part.split(' ', 2)
            col_name = col_name[col_name.find('{') + 1: col_name.rfind('}')]
            parameters[col_name] = {'operator': operator, 'value': filter_value}
    print(f'parameters: {parameters}')

    # NOTE: do this for the other two return values
    columns = broker_client.get_columns()

    print(broker_client.get_filters())

    return columns, broker_client.get_alerts(parameters), broker_client.get_filters(), dhc.H3(f'{broker_client._broker.name} Alerts')


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
            target = broker_client._broker.to_target(row_data[row]['alert'])
            if target:
                successes.append(target.name)  # TODO: How to indicate successes?
            else:
                errors.append(target.name)  # TODO: How to handle errors?
    
        if successes:
            return dcc.Location(pathname=reverse('tom_targets:list'), id='dash-location')            
