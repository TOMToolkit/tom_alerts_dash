import logging

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as dhc
from dash_table import DataTable
from django_plotly_dash import DjangoDash
from django.shortcuts import reverse

from tom_alerts_dash.alerts import get_service_class, get_service_classes

# This module creates the browseable alert tables for the supported brokers. It does so by creating a Dash container for
# each registered broker in settings.py. The containers include two messages containers, a create-targets button, a set
# of broker-specific filter inputs, and a DataTable. The containers are set to {display: none;} on load with no alerts
# in them. A callback is registered that listens to a dropdown allowing the user to select a broker--when the broker
# selection changes, the corresponding broker container is displayed. Additionally, a callback is registered for each
# broker, with the broker-specific filters as the inputs, and the broker-specific DataTable as the output. Finally, two
# callbacks are registered for each broker for error or success messages. The first uses the broker-specific filters as
# the inputs, and one of the two broker-specific messages containers as the output. The second uses the broker-specific
# create-targets button as the input, and the other broker-specific messages container as the output.

logger = logging.getLogger(__name__)

app = DjangoDash('BrokerQueryListViewDash', external_stylesheets=[dbc.themes.BOOTSTRAP], add_bootstrap_links=True)


def create_targets(create_targets, selected_rows, row_data, broker_state, messages_state):
    """
    Create TOM Toolkit target objects for each selected target for the current broker. Callback is triggered by a click
    of the broker-specific create-targets-{broker_name} button. Upon clicking, the callback gets the current-selected
    rows in the broker-specific DataTable and calls ``tom_alerts.alerts.to_target`` on each one.

    This fires on page load, but should not. However, the ``prevent_initial_call`` kwargs does not appear to work in
    django-plotly-dash.

    :param create_targets: Number of times the create-targets button has been clicked.
    :type create_targets: int

    :param selected_rows: indices of rows selected in the DataTable. As a State value, this does not trigger callback.
    :type selected_rows: list

    :param row_data: Data currently displayed in the DataTable. As a State value, this does not trigger callback.
    :type row_data: list of dicts

    :param broker_state: Currently selected broker. As a State value, this does not trigger callback.
    :type broker_state: str

    :param messages_state: Currently displayed messages. As a State value, this does not trigger callback.
    :type messages_state: list of dbc.Alert object
    """
    logger.info(f'Entering create targets callback for broker: {broker_state}')
    # Ensure the create-targets button has actually been clicked and that there are selected rows
    if create_targets and selected_rows:
        broker_class = get_service_class(broker_state)()
        messages = messages_state
        for row in selected_rows:
            try:
                target = broker_class.to_target(row_data[row]['alert'])  # Get the data for each selected row
                target_url = reverse('targets:detail', kwargs={'pk': target.id})
                messages.append(
                    dbc.Alert(['Successfully created ', dhc.A('View Target', href=target_url)],
                              color='success', dismissable=True, duration=5000, is_open=True)
                )
            except Exception as e:
                logger.error(f'Unable to create target from alert {row_data[row]["alert"]} due to exception {e}.')
                messages.append(
                    dbc.Alert(f'Unable to create target from alert.',  # TODO: how to give the alert name?
                              color='danger', is_open=True, dismissable=True, duration=5000)
                )

        return messages
    else:
        raise PreventUpdate


def create_broker_callbacks():
    """
    Add all broker-specific callbacks to the app callbacks on init, and construct the alerts table
    dynamically, with a different id depending on the broker. As there's no way to remove callbacks,
    this is the only way to support different callbacks per broker.

    There are three broker-specific callbacks per broker. The first is a callback that fires on a change in any
    broker-specific inputs and updates the data in the broker-specific DataTable. The second fires on a click of the
    broker-specific create-targets button and updates the broker-specific messages container in order to convey success
    or failure of target creation. The third fires on any change in broker-specific inputs and validates the inputs,
    then returns Alert objects to display to the user any validation errors.
    """

    for class_name in get_service_classes().keys():
        broker_class = get_service_class(class_name)()
        table_callback = app.callback(  # Create the broker-specific filters callback
            Output(f'alerts-table-{class_name}', 'data'),
            broker_class.get_callback_inputs()
        )
        table_callback(broker_class.callback)  # Instantiate the broker-specific filters callback

        filter_validation_callback = app.callback(  # Create the broker-specific filter validation callback
            Output(f'messages-filters-{class_name}', 'children'),
            broker_class.get_callback_inputs(),
            [State(f'messages-filters-{class_name}', 'children')]
        )
        filter_validation_callback(broker_class.validate_filters)

        create_targets_callback = app.callback(  # Create the broker-specific create-targets callback
            Output(f'messages-targets-{class_name}', 'children'),
            [Input(f'create-targets-btn-{class_name}', 'n_clicks')],
            [State(f'alerts-table-{class_name}', 'derived_virtual_selected_rows'),
             State(f'alerts-table-{class_name}', 'derived_virtual_data'),
             State('broker-state', 'value'),
             State(f'messages-targets-{class_name}', 'children')]
        )
        create_targets_callback(create_targets)  # Create the broker-specific create-targets callback


def create_broker_container(broker):
    """
    This method creates the container with the broker-specific components. It is hidden by default. The components are
    a redirection container, a series of filter input components, a create-targets button, and a Dash DataTable. Each
    component id includes the name of the broker, in order to distinguish it for use in a specific callback function.

    :param broker: The name of the broker class for which to create a container
    :type broker: str

    :returns: The container with the redirection, filter inputs, button, and DataTable
    :rtype: dhc.Div
    """
    broker_class = get_service_class(broker)()
    return dhc.Div(children=[
        dcc.Loading(children=[
            dhc.Div(
                broker_class.get_dash_filters()
            ),
            dhc.Div(
                dhc.P(
                    dbc.Button(
                        'Create targets from selected',
                        id=f'create-targets-btn-{broker}',
                        outline=True,
                        color='info'
                    ),
                )
            ),
            DataTable(
                id=f'alerts-table-{broker}',
                columns=broker_class.get_dash_columns(),
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
    ], id=f'alerts-container-{broker}', style={'display': 'none'})


@app.callback(
    [Output('broker-state', 'value'), Output('page-header', 'children')] +
    [Output(f'alerts-container-{clazz}', 'style') for clazz in get_service_classes().keys()],
    [Input('broker-selection', 'value')],
    [State('broker-state', 'value')]
)
def broker_selection_callback(broker_selection, broker_state):
    """
    Callback triggered by a selection of the broker dropdown. The callback also takes the previously selected broker.
    The outputs are the broker state container, the header displaying which broker alerts are being viewed,
    and an output bound to the style property of each broker container.

    If the broker selection did not change from the previously selected broker, no update occurs.

    If the broker selection did change, the following events occur:
    - The newly selected broker is added to the return values in order to update the broker-state component
    - A new dhc.H3 element with the correct broker display name is added to the return values
    - A style property is added to the return values for each broker container. The style property is
      {'display': 'none'} for all brokers save the selected broker, which instead is {'display': 'block'}. This will
      hide all containers except the one for the selected broker.

    :param broker_selection: The newly selected broker
    :type broker_selection: str

    :param broker_state: The previously selected broker. As a State value, a value change does not trigger the callback.
    :type broker_state: str

    :returns: The value of the newly selected broker
    :rtype: str

    :returns: A header showing the name of the newly selected broker
    :rtype: dash_html_component.H3

    :returns: A CSS style dictionary for each broker, either {'display': 'none'} or {'display': 'block'}
    :rtype: dict

    :raises: PreventUpdate when the newly selected broker does not change
    """
    callback_return_values = ()
    if broker_selection and broker_selection != broker_state:  # Broker selection has changed

        # Modify page header to display correct broker name
        page_header = dhc.H3(f'{broker_selection} Alerts')

        # Add the newly selected broker and new page_header to the return tuple
        callback_return_values += (broker_selection, page_header)

        # Hide all DataTables other than the one that corresponds with the selected broker
        for clazz in get_service_classes().keys():
            if broker_selection == clazz:  # newly selected broker should be displayed
                callback_return_values += ({'display': 'block'},)
            else:  # all other brokers should be hidden
                callback_return_values += ({'display': 'none'},)

        return callback_return_values
    else:  # Broker selection has not changed from previous value
        raise PreventUpdate  # Don't update any components


create_broker_callbacks()

app.layout = dbc.Container([
    dhc.Div(
        # Messages containers for validation messages related to filter inputs
        [dhc.Div(children=[], id=f'messages-filters-{class_name}') for class_name in get_service_classes().keys()] +
        # Messages containers for validation messages related to target creation
        [dhc.Div(children=[], id=f'messages-targets-{class_name}') for class_name in get_service_classes().keys()] +
        [
            dhc.Div(  # Create an initial header. This div will be replaced by the broker_selection callback
                dhc.H3('View Alerts for a Broker'),
                id='page-header'
            ),
            dhc.Div(children=[
                # Hidden component to store the currently selected broker. This is used for the create_targets callback.
                dcc.Input(id='broker-state', type='hidden', value=''),
                dhc.P(
                    dcc.Dropdown(  # Dropdown component to select the active broker
                        id='broker-selection',
                        placeholder='Select Broker',
                        options=[{'label': clazz, 'value': clazz} for clazz in get_service_classes().keys()]
                    )
                )
            ]),
            dhc.Div(  # Creates a container for each broker
                children=[create_broker_container(class_name) for class_name in get_service_classes().keys()],
            ),
        ]
    )
])
