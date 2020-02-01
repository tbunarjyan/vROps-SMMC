"""Module organizing metric collection workflow."""

import json
import logging
import re
import pandas as pd

from requests_definitions import get_object_id, get_metric_list


class RequestCred:
    """Initialize request credential attributes."""

    def __init__(self, request_cred):
        """Initialize data and credentials attributes."""
        self.ip_addr = request_cred['vrops_ip'].strip()
        self.username = request_cred['auth'][0].strip()
        self.password = request_cred['auth'][1].strip()
        self.payloads = request_cred['payloads']
        self.service_payloads = ''
        self.bearer_token = ''


def json_decode(name):
    """Decode json using the file path as an input."""
    return json.load(open(name, encoding='utf-8'))


def save_as_csv(filename, data, data_type):
    """Save metric data as filename in csv format."""
    try:
        if data_type == 'metrics':
            data_frame = pd.DataFrame(data)
            data_frame.to_csv(filename, header=data.keys(), index=True)
        elif data_type == 'names':
            data_frame = pd.DataFrame(data, columns=(
                'kpi', 'name', 'object', 'metric'))
            data_frame.to_csv(filename)
        return True
    except Exception as exception_caught:
        logging.error('%s, Unable to dump %s csv.',
                      type(exception_caught).__name__, data_type)
        return False


def metric_collector(request_cred):
    """Collect and store self-monitoring object metrics via suite REST API."""
    metric_df_obj, metric_name_def = {}, {}

    local_start_index = 0
    output_data = {}

    for service_name in request_cred.service_payloads:
        setup_service_info = get_object_id(request_cred, service_name)

        if setup_service_info['httpStatusCode'] != 200:
            logging.error('%s, %s ', setup_service_info['httpStatusCode'],
                          setup_service_info['message'])
            output_data['status_code'] = \
                setup_service_info['httpStatusCode']
            output_data['message'] = \
                setup_service_info['message']
            return output_data

        num_service_instance = setup_service_info['pageInfo']['totalCount']

        for i in range(num_service_instance):
            obj_uuid = setup_service_info[
                'resourceList'][i]['identifier']
            obj_uuid_name = setup_service_info['resourceList'][i][
                'resourceKey']['name']
            node_name = setup_service_info['resourceList'][i][
                'resourceKey']['resourceIdentifiers'][0]['value']

            node_name = re.sub('[^.,A-Za-z0-9]+', '', node_name)

            if node_name.strip() == "":
                node_name = "UNDEFINED_NODE"

            if node_name not in metric_name_def.keys():
                metric_name_def[node_name], metric_df_obj[node_name] = [], {}

            requested_metric = get_metric_list(
                request_cred, obj_uuid)

            if requested_metric['httpStatusCode'] != 200:
                logging.error('%s, %s ', requested_metric['httpStatusCode'],
                              requested_metric['message'])
                output_data['status_code'] = \
                    requested_metric['httpStatusCode']
                output_data['message'] = \
                    requested_metric['message']
                return output_data

            try:
                requested_metric = requested_metric[
                    'values'][0]['stat-list']['stat']

            except Exception as exception_caught:
                logging.warning(
                    "%s/%s %s, NODE NAME: %s, -- NO DATA COLLECTED, %s",
                    i + 1, num_service_instance, obj_uuid_name, node_name,
                    type(exception_caught).__name__)
                continue

            for j, metric in enumerate(requested_metric):
                given_metric_name = metric['statKey']['key']
                given_metric_short_name = 'm%s' % int(j + local_start_index)
                is_kpi = ''

                if given_metric_name in \
                        request_cred.service_payloads[service_name].keys():
                    is_kpi = 'kpi'

                metric_name_def[node_name].append(
                    [is_kpi, given_metric_short_name,
                     service_name, given_metric_name])

                metric_df_obj[node_name][given_metric_short_name] = \
                    pd.Series(requested_metric[j]['data'])

            local_start_index += len(requested_metric)

            logging.info("%s/%s %s, NODE NAME: %s", i + 1,
                         num_service_instance, obj_uuid_name, node_name)

    output_data['metric_data'], output_data['metric_names'] = (
        metric_df_obj, metric_name_def)
    output_data['status_code'] = 200

    return output_data
