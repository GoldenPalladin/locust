import time
from json import dumps
import logging
from config.test_config_reader import splunk_config

from gevent import monkey
# The monkey patching must run before requests is imported, or else
# we'll get an infinite recursion when doing SSL/HTTPS requests.
# See: https://github.com/requests/requests/issues/3752#issuecomment-294608002
monkey.patch_all()

from socket import gethostname
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from framework.generator.listener import Listener


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SplunkErrorListener(Listener):
    """
    Class for sending error logs into Splunk
    """
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(SplunkErrorListener, cls).__new__(cls)
        return cls.instance

    def __init__(self, config=splunk_config):
        """
        :param config: config section with Sfx endpoint, access token and timeout
        """
        super(SplunkErrorListener, self).__init__(config=config)
        self.url = f'https://{config["splunkHost"]}:{config["splunkPort"]}/services/collector'
        self.headers = {'Authorization': f'Splunk {config["splunkToken"]}'}
        self.timeout = config['timeout']
        self.session = requests.Session()
        retry = Retry(total=5,
                      backoff_factor=2.0,
                      method_whitelist=False,  # Retry for any HTTP verb
                      status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retry))
        self.params = {'time': None,
                       'host': gethostname(),
                       'index': config['splunkIndex'],
                       'source': 'locust',
                       'sourcetype': 'json',
                       'event': None}
        self.posted_error_keys = list()

    def on_stop(self):
        logger.info(f'Splunk listener stopped')

    def on_start(self):
        logger.info(f'Splunk listener started')

    def emit(self):
        logger.debug(f'Splunk user count: {self.runner.user_count}, sleep: {self.interval}')
        self.now = time.time()
        requests_errors = self.prepare_locust_errors(stats=self.runner.stats,
                                                     user_count=self.runner.user_count,
                                                     posted_errors=self.posted_error_keys)
        if requests_errors:
            keys, errors = zip(*requests_errors)
            keys, errors = list(keys), list(errors)
            logger.debug(f'Emitting Splunk errors: {errors}')
            for error in errors:
                error.update(self.stats_dimensions)
                self.send_splunk_event(error)
            self.posted_error_keys.extend(keys)

    def send_splunk_event(self, event: dict):
        def jsn(x):
            return str(x).replace('"', '\"')
        event.update({'error': jsn(event.get('error', ''))})
        payload = self.params.copy()
        payload.update({'time': time.time(), 'event': event})
        logger.debug(f'Splunk sending! {payload}')
        try:
            r = self.session.post(
                self.url,
                data=dumps(payload),
                headers=self.headers,
                timeout=self.timeout
            )
            r.raise_for_status()
        except Exception as e:
            logger.exception(f'Exception in Splunk logging: {str(e)}')


