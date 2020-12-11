from abc import abstractmethod
from importlib import import_module

from dash.dependencies import Input, Output
from django.conf import settings

from tom_alerts.alerts import GenericBroker


DEFAULT_ALERT_CLASSES = [
    'tom_alerts_dash.brokers.mars.MARSDashBroker',
    'tom_alerts_dash.brokers.alerce.ALeRCEDashBroker',
    # 'tom_alerts_dash.brokers.scimma.SCIMMADashBroker',
]


def get_service_classes():
    """
    Gets the dash broker classes available to this TOM as specified by ``TOM_ALERTS_DASH_CLASSES`` in ``settings.py``.
    If none are specified, returns the default set.

    :returns: dict of broker classes, with keys being the name of the broker and values being the broker class
    :rtype: dict
    """
    try:
        TOM_ALERTS_DASH_CLASSES = settings.TOM_ALERTS_DASH_CLASSES
    except AttributeError:
        TOM_ALERTS_DASH_CLASSES = DEFAULT_ALERT_CLASSES

    service_choices = {}
    for service in TOM_ALERTS_DASH_CLASSES:
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


# TODO: Finalize interface and document
class GenericDashBroker(GenericBroker):
    name = 'Generic Broker'

    def callback(self):
        return

    def get_callback_inputs(self):
        return []

    @abstractmethod
    def get_dash_filters(self):
        pass

    @abstractmethod
    def get_dash_columns(self):
        pass

    def flatten_dash_alerts(self, alerts):
        pass
