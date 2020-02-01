"""Module introducing vR Ops REST API request definitions."""

from urllib.error import HTTPError

import requests
import urllib3


def acquire_bearer_token(request_cred):
    """Generate vR Ops authorization token."""
    urllib3.disable_warnings()

    url = 'https://%s/suite-api/api/auth/token/acquire' % \
          request_cred.ip_addr

    headers = {'Accept': "application/json",
               'Content-Type': "application/json"}

    payload = """{{"username": "{0}", "password": "{1}"}}""". \
        format(request_cred.username, request_cred.password)

    try:
        response = requests.request(
            "POST", url, data=payload, headers=headers, verify=False)

    except HTTPError as error:
        response = error.response

    response_content = {}

    try:
        response_content['httpStatusCode'] = response.status_code
        response = response.json()
        response_content['data'] = response

    except Exception as exception_caught:
        response_content['httpStatusCode'] = response.status_code
        response_content['message'] = \
            "HTTP: %s, Unable to acquire bearer token." % \
            type(exception_caught).__name__

    return response_content


def release_bearer_token(request_cred):
    """Revoke vR Ops authorization token."""
    urllib3.disable_warnings()

    url = 'https://%s/suite-api/api/auth/token/release' % \
          request_cred.ip_addr

    headers = {'Accept': "application/json",
               'Content-Type': "application/json",
               'Authorization': 'vRealizeOpsToken %s' %
                                request_cred.bearer_token}
    try:
        response = requests.request(
            "POST", url, headers=headers, verify=False)

    except HTTPError as error:
        response = error.response
        response.status_code = 455

    return response.status_code


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
                (request_cred.username, request_cred.password)),
            verify=False)

    except HTTPError as error:
        response = error.response

    response_content = {}

    try:
        response = response.json()
        response_content['httpStatusCode'] = 200
        response_content['data'] = response

    except Exception as exception_caught:
        response_content['httpStatusCode'] = 503
        response_content['message'] = \
            "vR Ops CASA is unavailable. %s", \
            type(exception_caught).__name__

    return response_content


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
            "POST", url, data=payload, headers=headers, verify=False)

    except HTTPError as error:
        response = error.response

    response_content = {}

    try:
        response_content = response.json()
        if 'httpStatusCode' not in response_content.keys():
            response_content['httpStatusCode'] = response.status_code

    except Exception as exception_caught:
        response_content['httpStatusCode'] = response.status_code
        response_content['message'] = \
            "HTTP: %s, Unable to acquire bearer token." % \
            type(exception_caught).__name__

    return response_content


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
            request_url, headers=headers, params=None, verify=False)

    except HTTPError as error:
        response = error.response

    response_content = {}

    try:
        response_content = response.json()
        if 'httpStatusCode' not in response_content.keys():
            response_content['httpStatusCode'] = response.status_code

    except Exception as exception_caught:
        response_content['httpStatusCode'] = response.status_code
        response_content['message'] = \
            "HTTP: %s, Unable to acquire bearer token." % \
            type(exception_caught).__name__

    return response_content
