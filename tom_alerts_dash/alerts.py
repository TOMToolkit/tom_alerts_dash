from abc import abstractmethod
from importlib import import_module

from dash.dependencies import Input
from dash.exceptions import PreventUpdate
from django.conf import settings

from tom_alerts.alerts import GenericBroker


DEFAULT_ALERT_CLASSES = [
    'tom_alerts_dash.brokers.mars.MARSDashBroker',
    'tom_alerts_dash.brokers.alerce.ALeRCEDashBroker',
]


def get_service_classes():
    """
    Gets the dash broker classes available to this TOM as specified by ``TOM_ALERT_DASH_CLASSES`` in ``settings.py``.
    If none are specified, returns the default set.

    :returns: dict of broker classes, with keys being the name of the broker and values being the broker class
    :rtype: dict
    """
    try:
        TOM_ALERT_DASH_CLASSES = settings.TOM_ALERT_DASH_CLASSES
    except AttributeError:
        TOM_ALERT_DASH_CLASSES = DEFAULT_ALERT_CLASSES

    service_choices = {}
    for service in TOM_ALERT_DASH_CLASSES:
        mod_name, class_name = service.rsplit('.', 1)
        try:
            mod = import_module(mod_name)
            clazz = getattr(mod, class_name)
        except (ImportError, AttributeError):
            raise ImportError(f'Could not import {service}. Did you provide the correct path?')
        service_choices[clazz.name] = clazz
    return service_choices


def get_service_class(name):
    """
    Gets the specific dash broker class for a given broker name.

    :returns: Broker class
    :rtype: class
    """
    available_classes = get_service_classes()
    try:
        return available_classes[name]
    except KeyError:
        raise ImportError(
            '''Could not a find a broker with that name.
            Did you add it to TOM_ALERTS_DASH_CLASSES?'''
        )


class GenericDashBroker(GenericBroker):
    """
    Interface class for implementation of a Dash-compatible broker module. Please refer to the built-in ALeRCE, MARS,
    and SCIMMA Dash broker modules for implementation examples.
    """
    name = 'Generic Broker'

    def callback(self, page_current, page_size):
        """
        Broker-specific callback function triggered on broker-specific filter inputs. Accepts filter inputs and queries
        the corresponding service to return a list of flattened (single-level depth) alert dictionaries. The
        dictionaries in the return list must have keys corresponding to the ``id`` values returned by this broker's
        ``get_dash_columns()``. Method signature must correspond to the filter inputs returned by this broker's
        ``get_callback_inputs()``.

        :param page_current: The page number for the paginated alerts to display
        :type page_current: int

        :param page_size: The page size used for the pagination
        :type page_size: int

        All other args need to be specified in the concrete implementation.

        :returns: list of 1-level depth alert dicts, with keys corresponding to return value of ``get_dash_columns()``
        :rtype: list of dicts
        """
        raise PreventUpdate

    def get_callback_inputs(self):
        """
        Method that provides broker-specific inputs intended to trigger this broker's callback function. Input names
        must correspond with ``id`` properties specified in this broker's ``get_dash_filters()``.

        Default implementation provides inputs for page number and page size. This method is technically not required
        for concrete implementation, but omission would prevent an end user from filtering alerts.

        :returns: list of inputs corresponding to dash filters for this broker
        :rtype: list
        """
        return [
            Input(f'alerts-table-{self.name}', 'page_current'),
            Input(f'alerts-table-{self.name}', 'page_size')
        ]

    @abstractmethod
    def get_dash_filters(self):
        """
        Method that provides the layout and input types for the filter inputs that are available for this broker. Please
        consult the Plotly Dash documentation for specific properties of Dash components:
        https://dash.plotly.com/dash-core-components

        :returns: layout of Dash input components
        :rtype: dash_html_components.Div
        """
        pass

    @abstractmethod
    def get_dash_columns(self):
        """
        Provides the columns that will be displayed in the broker-specific Dash DataTable. Columns must follow the
        format specified in the Dash DataTable documentation: https://dash.plotly.com/datatable/reference

        :returns: columns for display in DataTable
        :rtype: list of dicts
        """
        pass

    def flatten_dash_alerts(self, alerts):
        """
        Transforms a list of alerts returned by a broker query into a list of single-level depth dictionaries for
        display in a Dash DataTable. Also handles any further transformation of the data returned by a broker query.

        Each flattened alert should also include a key/value pair of {'alert': original_alert}, to be used when
        creating a target from the alert.

        :param alerts: list of alerts from a broker query
        :type alerts: list

        :returns: list of single-level depth dicts
        :rtype: list of dicts
        """
        return alerts

    def validate_filters(self, page_current, page_size, errors_state):
        """
        Validates the input filters for a broker module. The concrete implementation of this method must accept all
        inputs returned from ``get_callback_inputs()``, as well as an ``errors_state`` as the last argument.

        :param page_current: The page number for the paginated alerts to display
        :type page_current: int

        :param page_size: The page size used for the pagination
        :type page_size: int

        All broker-specific args need to be specified in the concrete implementation.

        :param errors_state: The currently displayed errors relating to filters
        :type errors_state: list of dbc.Alert objects

        :returns: errors from validation of filters
        :rtype: list of dbc.Alert objects

        :raises: PreventUpdate
        """
        raise PreventUpdate
