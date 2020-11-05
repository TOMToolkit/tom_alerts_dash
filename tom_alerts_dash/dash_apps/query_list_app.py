import dash
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as dhc
from dash_table import DataTable
from django.conf import settings
from django_plotly_dash import DjangoDash

from tom_alerts.alerts import get_service_class, get_service_classes


app = DjangoDash('BrokerQueryListViewDash', external_stylesheets=[dbc.themes.BOOTSTRAP], add_bootstrap_links=True)


class BrokerClient:
    _broker = None

    def __init__(self, broker_name, *args, **kwargs):
        self._broker = get_service_class(broker_name)()

    def get_columns(self):
        print(self._broker)
        return self._broker.get_dash_columns()

    def get_alerts(self):
        return self._broker.get_dash_data({})
        return [{
            'objectId': 1,
            'ra': 1,
            'dec': 1,
            'magpsf': 1,
            'rb': 1,
        }]

    def set_broker(self, new_broker_name):
        self._broker = get_service_class(new_broker_name)()


broker_client = BrokerClient('MARS')
print(get_service_classes())
print([{'label': clazz, 'value': clazz} for clazz in get_service_classes().keys()])


app.layout = dbc.Container([
    dhc.Div([
        dhc.Div(
            dcc.Dropdown(
                id='broker-selection',
                options=[{'label': clazz, 'value': clazz} for clazz in get_service_classes().keys()]
            )
        ),
        dhc.Div(  # Filters go here
            dcc.Input(
                id='name-search',
                type='text',
                placeholder='Alert name search',
                debounce=True
            ),
            id='alerts-table-filters-container'
        ),
        dhc.Div(  # Alerts datatable goes here
            DataTable(
                id='alerts-table',
                columns=broker_client.get_columns(),
                data=broker_client.get_alerts(),
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
     Input('name-search', 'value')]
)
def alerts_table_filter(broker_selection, name_search):
    if broker_selection:
        print(broker_selection)
        broker_client.set_broker(broker_selection)

    return broker_client.get_columns(), broker_client.get_alerts()
