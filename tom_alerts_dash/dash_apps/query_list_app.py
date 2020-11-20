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

    def get_callback_inputs(self):
        return self._broker.get_callback_inputs()

    def get_filter_callback(self):
        return self._broker.filter_callback

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
                dbc.Button(
                    'Create targets from selected', 
                    id='create-targets-btn',
                    outline=True,
                    color='info'
                ),
            )
        ),
        dhc.Div(  # Filters go here
                [broker_client.get_filters()],
                id='alerts-table-filters-container',
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

# Create the callback for the initial broker
# TODO: default behavior on this table probably shouldn't be to load MARS alert, but rather prompt for
# broker selection
app.callback(
    Output('alerts-table', 'data'), broker_client.get_callback_inputs()
)(broker_client._broker.filter_callback)

# TODO TODO: Add all broker callbacks to the app callbacks on init, and construct the alerts table
# dynamically, with a different id depending on the broker. As there's no way to remove callbacks,
# this is the only way to support different callbacks per broker.

@app.callback(
    [Output('alerts-table', 'columns'),
     Output('page-header', 'children')],
    [Input('broker-selection', 'value')],
)
def alerts_table_filter(broker_selection):

    if broker_selection and broker_selection != broker_client.broker:
        print(broker_selection)
        broker_client.broker = broker_selection
        # TODO: remove the old callback from app._callback_sets
        app._callback_sets.pop(0)
        app.callback(Output('alerts-table', 'data'), broker_client.get_callback_inputs())(broker_client.get_filter_callback())
        page_current = 0
    for callback in app._callback_sets:
        print(f'callback: {callback}')

    # TODO: Add example filter queries
    # parameters = {'page_num': page_current, 'page_size': page_size}
    # if filter_query:
    #     for filter_part in filter_query.split(' && '):
    #         col_name, operator, filter_value = filter_part.split(' ', 2)
    #         col_name = col_name[col_name.find('{') + 1: col_name.rfind('}')]
    #         parameters[col_name] = {'operator': operator, 'value': filter_value}
    # print(f'parameters: {parameters}')

    columns = broker_client.get_columns()
    page_header = dhc.H3(f'{broker_client._broker.name} Alerts')

    return columns, page_header


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
            # NOTE: an option for handling success/error: put the alert into this view, redirect here, but 
            # add a link to go to the target list in the success message
    
        if successes:
            return dcc.Location(pathname=reverse('tom_targets:list'), id='dash-location')            
