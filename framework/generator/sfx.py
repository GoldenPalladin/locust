import time
import logging
from config.test_config_reader import sfx_config

from gevent import monkey
# The monkey patching must run before requests is imported, or else
# we'll get an infinite recursion when doing SSL/HTTPS requests.
# See: https://github.com/requests/requests/issues/3752#issuecomment-294608002
monkey.patch_ssl()

import signalfx
from framework.generator.listener import Listener


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SfxListener(Listener):
    """
    Class for sending stats into SignalFX
    On init emits 'locust test started' event
    On delete emits 'locust test stopped' event
    """
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(SfxListener, cls).__new__(cls)
        return cls.instance

    def __init__(self, config=sfx_config):
        """
        :param config: config section with Sfx endpoint, access token and timeout
        :param additional_dimensions: dict with additional dimensions to add to gauges and events
        """
        super(SfxListener, self).__init__(config=config)
        self.sfx = signalfx.SignalFx().ingest(token=config['access_token'],
                                              endpoint=config['endpoint'],
                                              timeout=int(config['timeout'])*1000)

    def on_stop(self):
        self.sfx.send_event(event_type='locust test stop', dimensions=self.stats_dimensions)
        logger.info(f'Sfx listener stopped')

    def on_start(self):
        self.sfx.send_event(event_type='locust test start',
                            dimensions=self.stats_dimensions)
        logger.info(f'Sfx listener started')

    def emit(self):
        user_count = self.runner.user_count
        stats = self.runner.stats
        logger.debug(f'SFX user count: {user_count}, sleep: {self.interval}')
        self.now = time.time()
        gauges = list()
        requests_stats = self.prepare_locust_stats(stats, user_count)
        if requests_stats:
            for request in requests_stats:
                request_name, request_timestamp, stats_values = request
                for name, value in stats_values.items():
                    gauge = self.make_metric(request_name, name, value, request_timestamp)
                    gauges.append(gauge)
            logger.debug(f'SFX gauges: {gauges}')
            self.sfx.send(gauges=gauges)

    def make_metric(self, request_name: str, name: str, value, timestamp) -> dict:
        """Prepare Sfx metric dict"""
        self.stats_dimensions.update({'request_name': request_name})
        return {'dimensions': self.stats_dimensions,
                'metric': f'locust.{str(name).replace(" ", "_")}',
                'value': value,
                'timestamp': int(timestamp * 1000)}
