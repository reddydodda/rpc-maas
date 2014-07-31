#!/usr/bin/env python

import collections
import sys
import time

from heatclient.client import Client
from maas_common import (get_heat_client, get_auth_ref, get_keystone_client,
                         metric, status_err, status_ok)

HEAT_STATUS = ['COMPLETE', 'FAILED', 'IN_PROGRESS']


def check_availability(auth_ref):
    """Check the availability of the Heat Orchestration API.

    :param auth_ref: A Keystone auth token reference for use in querying Heat

    Metrics include stacks built from either heat or cfn templates.
    Outputs metrics on current status of Heat and time elapsed during query.
    Outputs an error status if any error occurs querying Heat.
    Exits with 0 if Heat is available and responds with 200, otherwise 1.
    """
    keystone = get_keystone_client(auth_ref)
    if keystone is None:
        status_err('Unable to obtain valid keystone client, cannot proceed')

    heat_endpoint = keystone.service_catalog.url_for(
        service_type='orchestration', endpoint_type='publicURL')
    auth_token_id = keystone.auth_ref['token']['id']
    heat = get_heat_client(heat_endpoint, auth_token_id)

    counters = collections.Counter(zip(HEAT_STATUS, [0] * len(HEAT_STATUS)))
    start_at = time.time()
    try:
        for stack in heat.stacks.list():
            counters[stack.status] += 1
    except Exception as e:
        status_err(str(e))
    elapsed_ms = (time.time() - start_at) * 1000

    status_ok('heat api success')
    for key in HEAT_STATUS:
        metric('heat_{0}_stacks'.format(key.lower()), 'uint32', counters[key])
    metric('heat_response_ms', 'double', elapsed_ms)


def main():
    check_availability(get_auth_ref())

if __name__ == "__main__":
    main()