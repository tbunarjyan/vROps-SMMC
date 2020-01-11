"""Module organizing metric collection workflow."""

import json
import logging
from urllib.error import HTTPError
import pandas as pd
import requests
import urllib3


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


def acquire_bearer_token(request_cred):
    """Generate vR Ops authorization token."""
    urllib3.disable_warnings()

    url = 'https://%s/suite-api/api/auth/token/acquire' % request_cred.ip_addr

    headers = {'Accept': "application/json",
               'Content-Type': "application/json"}

    payload = """{{"username": "{0}", "password": "{1}"}}""". \
        format(request_cred.username, request_cred.password)

    try:
        response = requests.request(
            "POST", url, data=payload, auth=tuple(
                (request_cred.username, request_cred.password)),
            headers=headers, verify=False)

    except HTTPError as error:
        response = error.response
    response = response.json()

    if 'httpStatusCode' not in response.keys():
        response['httpStatusCode'] = 200
    return response


def release_bearer_token(request_cred):
    """Revoke vR Ops authorization token."""
    urllib3.disable_warnings()

    url = 'https://%s/suite-api/api/auth/token/release' % request_cred.ip_addr

    headers = {'Accept': "application/json",
               'Content-Type': "application/json",
               'Authorization': 'vRealizeOpsToken %s' %
                                request_cred.bearer_token}
    try:
        response = requests.request(
            "POST", url, headers=headers, verify=False)
        return response.status_code
    except HTTPError as error:
        response = error.response
        response.status_code = 455
    return response.status_code


def get_object_id(request_cred, service_name):
    """Get object id from a given object name using vROps suite REST API."""
    urllib3.disable_warnings()

    url = "https://%s/suite-api/api/resources/query" % request_cred.ip_addr

    payload = "{\n    \"resourceKind\" : [\"" + service_name + '\"]\n}"'

    headers = {'Accept': "application/json",
               'Content-Type': "application/json",
               'Authorization': 'vRealizeOpsToken %s' %
                                request_cred.bearer_token}
    try:
        response = requests.request(
            "POST", url, auth=tuple(
                (request_cred.username, request_cred.password)),
            data=payload, headers=headers, verify=False)

    except HTTPError as error:
        response = error.response
    response = response.json()

    if 'httpStatusCode' not in response.keys():
        response['httpStatusCode'] = 200
    return response


def get_metric_list(request_cred, obj_uuid):
    """Get metric data from a given self-monitoring object."""
    urllib3.disable_warnings()

    request_url = 'https://%s/suite-api/api/resources/%s/stats?' % \
                  (request_cred.ip_addr, obj_uuid)

    headers = {'Accept': "application/json",
               'Content-Type': "application/json",
               'Authorization': 'vRealizeOpsToken %s' %
                                request_cred.bearer_token}
    try:
        response = requests.get(
            request_url, headers=headers, params=None, auth=tuple(
                (request_cred.username, request_cred.password)), verify=False)

    except HTTPError as error:
        response = error.response
    response = response.json()

    if 'httpStatusCode' not in response.keys():
        response['httpStatusCode'] = 200
    return response


def setup_status(request_cred):
    """Get vR Ops up status information."""
    urllib3.disable_warnings()

    request_url = 'https://%s/casa/sysadmin/cluster/online_state' % \
                  request_cred.ip_addr

    headers = {'Accept': "application/json",
               'Content-Type': "application/json"}

    try:
        response = requests.get(
            request_url, headers=headers, auth=tuple(
                (request_cred.username, request_cred.password)), verify=False)

    except HTTPError as error:
        response = error.response

    response_content = {}
    try:
        response = response.json()
        response_content['httpStatusCode'] = 200
        response_content['data'] = response
        return response_content

    except Exception as exception_caught:
        response_content['httpStatusCode'] = 503
        response_content['message'] = \
            "vR Ops CASA is unavailable. %s", \
            type(exception_caught).__name__
        return response_content


def metric_collector(request_cred):
    """Collect and store self-monitoring object metrics via suite REST API."""
    metric_df_obj, metric_name_def = {}, {}

    for service_name in request_cred.service_payloads:
        setup_service_info = get_object_id(request_cred, service_name)

        num_service_instance = setup_service_info['pageInfo']['totalCount']

        for i in range(num_service_instance):
            obj_uuid = setup_service_info[
                'resourceList'][i]['identifier']
            obj_uuid_name = setup_service_info['resourceList'][i][
                'resourceKey']['name']
            node_name = setup_service_info['resourceList'][i][
                'resourceKey']['resourceIdentifiers'][0]['value']

            metric_name_def[node_name], metric_df_obj[node_name] = [], {}

            logging.info("%s/%s %s",
                         i + 1, num_service_instance, obj_uuid_name)

            requested_metric = get_metric_list(
                request_cred, obj_uuid)['values'][0]['stat-list']['stat']

            for j, metric in enumerate(requested_metric):
                given_metric_name = metric['statKey']['key']
                given_metric_short_name = 'm%s' % j
                is_kpi = ''

                if given_metric_name in \
                        request_cred.service_payloads[service_name].keys():
                    is_kpi = 'kpi'

                metric_name_def[node_name].append(
                    [is_kpi, given_metric_short_name,
                     service_name, given_metric_name])

                metric_df_obj[node_name][given_metric_short_name] = \
                    pd.Series(requested_metric[j]['data'])

    return metric_df_obj, metric_name_def
