[![pypi](https://img.shields.io/pypi/v/tom-alerts-dash.svg)](https://pypi.python.org/pypi/tom-alerts-dash)
[![run-tests](https://github.com/TOMToolkit/tom_alerts_dash/actions/workflows/run-tests.yml/badge.svg)](https://github.com/TOMToolkit/tom_alerts_dash/actions/workflows/run-tests.yml)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/e003f03e2820481e9206d6b18eef3d92)](https://www.codacy.com/gh/TOMToolkit/tom_alerts_dash/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=TOMToolkit/tom_alerts_dash&amp;utm_campaign=Badge_Grade)
[![Coverage Status](https://coveralls.io/repos/github/TOMToolkit/tom_alerts_dash/badge.svg?branch=main)](https://coveralls.io/github/TOMToolkit/tom_alerts_dash?branch=main)

# tom_alerts_dash
This module supplements the `tom_alerts` module with [Plotly Dash](https://plotly.com/dash/) support for more responsive broker views.

## Installation

Install the module into your TOM environment:

    pip install tom-alerts-dash

Add `tom_alerts_dash` and `django_plotly_dash.apps.DjangoPlotlyDashConfig` to the `INSTALLED_APPS` in your TOM's `settings.py`:

```python
    INSTALLED_APPS = [
        'django.contrib.admin',
        ...
        'tom_dataproducts',
        'tom_alerts_dash',
        'django_plotly_dash.apps.DjangoPlotlyDashConfig'
    ]
```

Add `STATIC_ROOT = os.path.join(BASE_DIR, '_static')` and the following `STATICFILES_FINDERS` configuration to your `settings.py`, ideally in the `Static files (CSS, JavaScript, Images)` section:

```python
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(BASE_DIR, '_static')
    MEDIA_ROOT = os.path.join(BASE_DIR, 'data')
    MEDIA_URL = '/data/'

    STATICFILES_FINDERS = [

        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',

        'django_plotly_dash.finders.DashAssetFinder',
        'django_plotly_dash.finders.DashComponentFinder',
        'django_plotly_dash.finders.DashAppDirectoryFinder',
    ]
```

Add `django_plotly_dash.middleware.BaseMiddleware` to `MIDDLEWARE` in your `settings.py`:

```python
    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        ...
        'django_plotly_dash.middleware.BaseMiddleware',
        'tom_common.middleware.Raise403Middleware',
        ...
    ]
```

Add the following Django Plotly Dash configuration to your `settings.py`:

```python
# django-plotly-dash configuration

X_FRAME_OPTIONS = 'SAMEORIGIN'

PLOTLY_COMPONENTS = [
    # Common components
    'dash_core_components',
    'dash_html_components',
    'dash_renderer',

    # django-plotly-dash components
    'dpd_components',
    # static support if serving local assets
    # 'dpd_static_support',

    # Other components, as needed
    'dash_bootstrap_components',
    'dash_table'
]
```

Add the following two new paths to your base `urls.py`:

```python
    url_patterns = [
        path('alerts/', include('tom_alerts_dash.urls', namespace='tom_alerts_dash')),
        path('', include('tom_common.urls')),
        path('django_plotly_dash/', include('django_plotly_dash.urls')),
    ]
```

Please note that the path with the namespace `tom_alerts_dash` MUST be placed above the `tom_common.urls` in order to properly override the default `tom_alerts` paths.

Finally, run the following to run the `django-plotly-dash` migrations:

```
    ./manage.py migrate
```

## Using SCIMMA with tom_alerts_dash

The `tom_scimma` [repo](https://github.com/TOMToolkit/tom_scimma) also includes `tom_alerts_dash` support. To install it into a TOM with `tom_alerts_dash` configured, the following steps are required.

Install `tom_alerts_dash` with the `tom_scimma` dependency, in either of the following fashions:

```
    pip install tom_alerts_dash tom_scimma
```
or:
```
    pip install tom_alerts_dash[scimma]
```

Add the `TOM_ALERT_DASH_CLASSES` setting to your `settings.py`, along with the brokers that you want to include in your TOM:

```python
    TOM_ALERT_DASH_CLASSES = [
        'tom_alerts_dash.brokers.mars.MARSDashBroker',
        'tom_alerts_dash.brokers.alerce.ALeRCEDashBroker',
        'tom_alerts_dash.brokers.scimma.SCIMMADashBroker'
    ]
```

Add the SCIMMA settings specified in the `tom_scimma` README:

```python
    TOM_ALERT_CLASSES = [
        ...
        'tom_scimma.scimma.SCIMMABroker'
    ]
```

```python
    BROKERS = {
        ...
        'SCIMMA': {
            'url': 'http://skip.dev.hop.scimma.org',
            'api_key': os.getenv('SKIP_API_KEY', ''),
            'hopskotch_url': 'dev.hop.scimma.org',
            'hopskotch_username': os.getenv('HOPSKOTCH_USERNAME', ''),
            'hopskotch_password': os.getenv('HOPSKOTCH_PASSWORD', ''),
            'default_hopskotch_topic': ''
        }
    }
```

## Creating a custom Dash broker module

For information on writing your own Dash broker module, please see the [TOM Toolkit documentation](https://tom-toolkit.readthedocs.io/en/stable/brokers/create_dash_broker.html) on Dash broker modules.
