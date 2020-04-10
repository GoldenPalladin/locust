import time
from framework.generator.listener import Listener
from typing import List
from locust import Locust, TaskSet
from requests import Response

import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DebugRunner(object):
    """
    Class to implement locustfile execution in core Python, not in gevent greenlets
    """

    def __init__(self, locust_classes: List[Locust]):
        """
        :param locust_classes: Locust class is subclass of Locust with non-empty task_set.
        parsed from settings with locust.main.load_locust_file
        """
        self.locust_classes = locust_classes

    def start_test(self):
        for locust in self.locust_classes:
            new_locust: Locust = locust()
            taskset_instance: TaskSet = new_locust.task_set(new_locust)
            for task_no, task in enumerate(taskset_instance.tasks, start=1):
                logger.info(' ')
                logger.info(f'-----------------TASK #{task_no} - {task.__name__}-----------------------')
                logger.info(' ')
                task(taskset_instance)


class DebugListener(Listener):
    """
    Debug listener to print Sfx stats to console
    """
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(DebugListener, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        """
        :param config: config section with Sfx endpoint, access token and timeout
        """
        config = dict({'stats_interval': 5})
        super(DebugListener, self).__init__(config=config)

    def on_stop(self):
        logger.info(f'DEB listener stopped')

    def on_start(self):
        logger.info(f'DEB listener started')

    def emit(self):
        user_count = self.runner.user_count
        stats = self.runner.stats
        logger.info(f'DEB user count: {user_count}, sleep: {self.interval}')
        self.now = time.time()
        requests_stats = self.prepare_locust_stats(stats, user_count)
        if requests_stats:
            for request in requests_stats:
                request_name, request_timestamp, stats_values = request
                for name, value in stats_values.items():
                    logger.info(f'DEB: {request_timestamp}: {request_name}, metric: {name} - {value}')


def get_healthcheck_info(locust_classes: List[Locust]) -> dict:
    """
    function to get api healthcheck info: api version, name
    :param locust_classes: Locust users from locustfile.py
    :return:
    """
    result = dict()
    for locust in locust_classes:
        new_locust: Locust = locust()
        healthcheck_response: Response = new_locust.client.healthcheck()
        if not healthcheck_response.ok:
            raise EnvironmentError(f'{healthcheck_response} for {locust}')
        api_properties = healthcheck_response.json().get('properties')
        result.update({api_properties.get('systemName'): api_properties.get('buildInfo', {}).get('appVersion')})
    return result

