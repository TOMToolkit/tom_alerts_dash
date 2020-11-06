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


operators = [['ge ', '>='], ['le ', '<='], ['lt ', '<'], ['gt ', '>'], ['ne ', '!='], ['eq ', '=']]


def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3


class BrokerClient:
    _broker = None

    def __init__(self, broker_name, *args, **kwargs):
        self._broker = get_service_class(broker_name)()

    def get_columns(self):
        return self._broker.get_dash_columns()

    def get_alerts(self):
        return self._broker.get_dash_data({})

    def set_broker(self, new_broker_name):
        self._broker = get_service_class(new_broker_name)()


broker_client = BrokerClient('MARS')
print(get_service_classes())
print([{'label': clazz, 'value': clazz} for clazz in get_service_classes().keys()])


app.layout = dbc.Container([
    dhc.Div([
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
                dbc.Button('Create targets from selected')
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
     Input('name-search', 'value'),
     Input('alerts-table', 'filter_query')]
)
def alerts_table_filter(broker_selection, name_search, filter_query):
    print(filter_query)
    if broker_selection:
        print(broker_selection)
        broker_client.set_broker(broker_selection)

    for filter_part in filter_query.split(' && '):
        if operator in operators:
            pass

    return broker_client.get_columns(), broker_client.get_alerts()
