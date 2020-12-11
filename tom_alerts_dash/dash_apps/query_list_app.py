import re

import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as dhc
from dash_table import DataTable
from django.conf import settings
from django_plotly_dash import DjangoDash
from django.shortcuts import reverse

from tom_alerts_dash.alerts import get_service_class, get_service_classes


app = DjangoDash('BrokerQueryListViewDash', external_stylesheets=[dbc.themes.BOOTSTRAP], add_bootstrap_links=True)


def create_datatable(broker):
    return dhc.Div(
        dcc.Loading(children=[
            dhc.Div(
                get_service_class(broker)().get_dash_filters()
            ),
            DataTable(
                id=f'alerts-table-{broker}',
                columns=get_service_class(broker)().get_dash_columns(),
                data=[],
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
                }
            )
        ], id=f'alerts-loading-container-{broker}'),
        id=f'alerts-container-{broker}', style={'display': 'none'}
    )


app.layout = dbc.Container([
    dhc.Div([
        dhc.Div(
            id='redirection'
        ),
        dhc.Div(
            dhc.H3(f'View Alerts for a Broker'),
            id='page-header'
        ),
        dhc.Div(children=[
            dcc.Input(id='broker-state', type='hidden', value=''),
            dhc.P(
                dcc.Dropdown(
                    id='broker-selection',
                    placeholder='Select Broker',
                    options=[{'label': clazz, 'value': clazz} for clazz in get_service_classes().keys()]
                )
            )
        ]),
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
        dhc.Div(  # Alerts datatable goes here
            children=[create_datatable(class_name) for class_name in get_service_classes().keys()],
        ),
    ])
])

# @app.callback(
#     [Output('alerts-table-filter-container', 'children'),
#      Output('alerts-table', 'columns')],
#     [Input('broker-selection', 'value')]
# )
# def broker_selection(broker_selection):
#     if broker_selection.has_changed:
#         app._callback_sets.pop()
#         app.callback(Output('alerts-table', 'data'), broker_client.get_callback_inputs())(broker_client.get_filter_callback())
#         return broker_client.get_filters(), broker_client.get_columns()


def create_targets_callback(create_targets, selected_rows, row_data, broker_state):
    print('create targets callback')
    if create_targets:
        broker_class = get_service_class(broker_state)()
        errors = []
        successes = []
        print('here1')
        for row in selected_rows:
            print('here2')
            target = broker_class.to_target(row_data[row]['alert'])
            if target:
                successes.append(target.name)  # TODO: How to indicate successes?
            else:
                errors.append(target.name)  # TODO: How to handle errors?
            # NOTE: an option for handling success/error: put the alert into this view, redirect here, but 
            # add a link to go to the target list in the success message
    
        if successes:
            return dcc.Location(pathname=reverse('tom_targets:list'), id='dash-location')
    
    return dhc.Div()


# NOTE: hidden datatables/input containers should be created for each broker, along with corresponding callbacks, on init
# NOTE: change in broker selection should hide current datatable and show the new datatable, and update the broker-state value
@app.callback(
    [Output('broker-state', 'value'), Output('page-header', 'children')] + [Output(f'alerts-container-{clazz}', 'style') for clazz in get_service_classes().keys()],
    [Input('broker-selection', 'value')],
    [State('broker-state', 'value')]
)
def broker_selection_callback(broker_selection, broker_state):
    print(broker_selection)
    print(broker_state)
    callback_return_values = ()
    if broker_selection and broker_selection != broker_state:

        # Modify page header to display correct broker name
        page_header = dhc.H3(f'{broker_selection} Alerts')
        callback_return_values += (broker_selection, page_header)

        # Hide all DataTables other than the one that corresponds with the selected broker
        for clazz in get_service_classes().keys():
            if broker_selection == clazz:
                callback_return_values += ({'display': 'block'},)
            else:
                callback_return_values += ({'display': 'none'},)

        # Register the create_targets_callback with the correct inputs and deregister the old one
        app._callback_sets.pop()  # TODO: do not pop the callback if one isn't registered yet
        app.callback(
            Output('redirection', 'children'),
            [Input('create-targets-btn', 'n_clicks'),
             Input(f'alerts-table-{broker_selection}', 'derived_virtual_selected_rows'),
             Input(f'alerts-table-{broker_selection}', 'derived_virtual_data')],
            [State('broker-state', 'value')]
        )(create_targets_callback)
        for callback in app._callback_sets:
            print(callback)
            print()

        print(callback_return_values)
        return callback_return_values
    else:
        raise PreventUpdate


# TODO TODO: Add all broker callbacks to the app callbacks on init, and construct the alerts table
# dynamically, with a different id depending on the broker. As there's no way to remove callbacks,
# this is the only way to support different callbacks per broker.
for class_name in get_service_classes().keys():
    broker_class = get_service_class(class_name)()
    table_callback = app.callback(
        Output(f'alerts-table-{class_name}', 'data'),
        [Input(f'alerts-table-{class_name}', 'page_current'), Input(f'alerts-table-{class_name}', 'page_size')] +
         broker_class.get_callback_inputs()
    )
    table_callback(broker_class.callback)


# create_targets_callback_inputs = [Input('create-targets-btn', 'n_clicks_timestamp')]
# for clazz in get_service_classes().keys():
#     create_targets_callback_inputs.append(Input(f'alerts-table-{clazz}', 'derived_virtual_selected_rows'))
#     create_targets_callback_inputs.append(Input(f'alerts-table-{clazz}', 'derived_virtual_data'))


# @app.callback(
#     Output('redirection', 'children'),
#     create_targets_callback_inputs,
#     State('broker-state', 'value')
# )
# def create_targets_callback(create_targets, *args):
#     broker_classes = get_service_classes().keys()
#     index = 0
#     broker_index = -1
#     for broker_class in broker_classes:
#         if broker_class == args[-1]:
#             broker_index = index
#             break
#         index += 1
#     print('create targets callback')
#     print(len(args))
#     print(args[0], args[2], args[3])
#     selected_rows = args[broker_index + 1]  # TODO: the index calculation is an incorrect placeholder
#     if create_targets and False:
#         errors = []
#         successes = []
#         for row in selected_rows:
#             target = broker_client._broker.to_target(row_data[row]['alert'])
#             if target:
#                 successes.append(target.name)  # TODO: How to indicate successes?
#             else:
#                 errors.append(target.name)  # TODO: How to handle errors?
#             # NOTE: an option for handling success/error: put the alert into this view, redirect here, but 
#             # add a link to go to the target list in the success message
    
#         if successes:
#             return dcc.Location(pathname=reverse('tom_targets:list'), id='dash-location')


# app.callback(
#     [Output('redirection', 'children')],
#     [Input('create-targets-btn', 'n_clicks_timestamp')] + 
#     [Input(f'alerts-table-{clazz}', 'derived_virtual_selected_rows') for clazz in get_service_classes().keys()] +
#     [Input(f'alerts-table-{clazz}', 'derived_virtual_data') for clazz in get_service_classes().keys()]
# )(create_targets_callback)
