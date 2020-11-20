from tom_alerts_dash.alerts import GenericDashBroker
from tom_common.templatetags.tom_common_extras import truncate_number
from tom_scimma.scimma import SCIMMABroker
from tom_targets.templatetags.targets_extras import deg_to_sexigesimal


# TODO: how will this jive with tom_scimma as a non-default?
# TODO: should external apps have pip "extras" such as `pip install tom_alerts_dash[scimma]`?
# TODO: or should tom_scimma be a dependency of tom_alerts_dash?
class SCIMMADashBroker(SCIMMABroker, GenericDashBroker):
    def flatten_dash_alerts(self, alerts):
        flattened_alerts = []
        for alert in alerts:
            # url = f'{GRACE_DB_URL}/superevents/{alert["message"]["event_trig_num"]}/view/'
            url = ''
            flattened_alerts.append({
                'alert_identifier': f'[{alert["alert_identifier"]}]({url})',
                'counterpart_identifier': alert['extracted_fields']['counterpart_identifier'],
                'ra': alert['right_ascension_sexagesimal'],
                'dec': alert['declination_sexagesimal'],
                'rank': alert['message']['rank'],
                'comments': alert['extracted_fields']['comment_warnings'],
                'alert': alert
            })
        return flattened_alerts

    def filter_alerts(self, filters):
        parameters = {'topic': 3}  # LVC counterpart topic
        parameters['page'] = filters.get('page_num', 0) + 1  # Dash pages are 0-indexed, SCIMMA is 1-indexed

        parameters['event_trigger_number'] = filters['alert_identifier']['value'] if 'alert_identifier' in filters else ''
        parameters['keyword'] = filters['comments']['value'] if 'comments' in filters else ''
        if all(k in filters for k in ['ra', 'dec']):
            parameters['cone_search'] = f'{filters["ra"]["value"]},{filters["dec"]["value"]},1'
        # TODO: implement searching by rank and counterpart identifier

        return self.fetch_alerts(parameters)

    def get_dash_columns(self):
        return [
            {'id': 'alert_identifier', 'name': 'Alert Identifier', 'type': 'text', 'presentation': 'markdown'},
            {'id': 'counterpart_identifier', 'name': 'Counterpart Identifier', 'type': 'text'},
            {'id': 'ra', 'name': 'Right Ascension', 'type': 'text'},
            {'id': 'dec', 'name': 'Declination', 'type': 'text'},
            {'id': 'rank', 'name': 'Rank', 'type': 'text'},
            {'id': 'comments', 'name': 'Comments', 'type': 'text'}
        ]

    def get_dash_data(self, parameters):
        alerts = self.filter_alerts(parameters)
        return self.flatten_dash_alerts(alerts)
