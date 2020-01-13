# Copyright 2006 VMware, Inc.  All rights reserved. -- VMware Confidential

"""vR Ops self-monitoring object metric collector using suite REST API."""

__author__ = 'VMware, Inc.'

import logging
import argparse
import time
import os
from metric_collector import acquire_bearer_token, release_bearer_token, \
    json_decode, setup_status, metric_collector, save_as_csv, RequestCred


def run():
    """Import and execute self-monitoring metric collection."""
    run_status = "FAILURE"
    logging.basicConfig(format='%(asctime)s [%(levelname)s] - %(message)s',
                        level=logging.INFO)

    (credentials, object_list, report_directory) = arg_parser()
    logging.info('Parsed command line arguments successfully.')

    try:
        request_cred = json_decode(credentials)
        object_list = json_decode(object_list)

        request_cred = RequestCred(request_cred)
        request_cred.service_payloads = object_list

        if not os.path.exists(report_directory):
            os.makedirs(report_directory)

    except Exception as exception_caught:
        logging.error('%s, Unable to load resources.',
                      type(exception_caught).__name__)
        return run_status

    bearer_token = acquire_bearer_token(request_cred)
    if bearer_token['httpStatusCode'] != 200:
        logging.error(
            "%s, %s", bearer_token['httpStatusCode'], bearer_token["message"])
        return run_status

    request_cred.bearer_token = bearer_token['token']
    logging.info(
        "Retrieved bearer token: HTTP %s", bearer_token['httpStatusCode'])

    cluster_state = setup_status(request_cred)
    if cluster_state['httpStatusCode'] != 200:
        logging.error("%s, %s", cluster_state['httpStatusCode'],
                      cluster_state["message"])
        return run_status

    cluster_status = cluster_state["data"]["cluster_online_state_snapshot"]
    if cluster_status != "ONLINE":
        status_code, message = 503, "vROps cluster: %s." % cluster_status
        logging.error("%s, %s", status_code, message)
        return run_status

    logging.info("vR Ops Cluster Status: %s", cluster_status)
    logging.info("Starting to collect self-monitoring object metrics.")

    data, names = metric_collector(request_cred)

    for node_name, _ in data.items():
        metric_filename = '%s/%s_metrics.csv' % (
            report_directory, node_name)
        metric_saved_status = save_as_csv(
            metric_filename, data[node_name], "metrics")

        names_filename = '%s/%s_metric_names.csv' % (
            report_directory, node_name)
        names_saved_status = save_as_csv(
            names_filename, names[node_name], "names")

        if metric_saved_status and names_saved_status:
            logging.info("Saved %s metric data, SUCCESS", node_name)
        else:
            logging.error(
                "Unable to save %s metric data, FAILURE", node_name)
            return run_status

    released_token = release_bearer_token(request_cred)

    if released_token != 200:
        logging.error("Error while releasing token: HTTP %s", released_token)
    else:
        logging.info("Released bearer token: HTTP %s", released_token)

    run_status = "SUCCESS"
    logging.info("Metric Collection status: %s", run_status)
    return run_status


def arg_parser():
    """Return list of command line parsed arguments."""
    parser = argparse.ArgumentParser(
        description='Arguments for vR Ops self-monitoring metrics collector.')
    parser.add_argument('-CRED', '--credentials', type=str,
                        help='vR Ops credentials file path')
    parser.add_argument('-OBJ-LIST', '--object_list', type=str,
                        help='vR Ops self-monitoring object list')
    parser.add_argument('-REP-DIR', '--report_directory', type=str,
                        help='Directory path in which reports would be saved')
    arg_list = parser.parse_args()

    return (arg_list.credentials, arg_list.object_list,
            arg_list.report_directory)


if __name__ == '__main__':
    START_TIME = time.time()
    RUN_STATUS = run()

    print("=" * 100)
    logging.info("RUNNING Time: %s seconds", (time.time() - START_TIME))
    logging.info('Code Execution Status: %s', RUN_STATUS)
    print("=" * 100)
