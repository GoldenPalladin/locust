import logging
import threading
import json

from gevent import monkey
# The monkey patching must run before requests is imported, or else
# we'll get an infinite recursion when doing SSL/HTTPS requests.
# See: https://github.com/requests/requests/issues/3752#issuecomment-294608002
monkey.patch_all()

from botocore import response
from config.test_config_reader import runner_config, test_header
from framework.test.stats import extend_stats, get_stats_from_response, print_stats
from framework.test.timings import Timings
from aws.prepare_lambda import get_aws_client, lambda_exists
from locust.stats import RequestStats


#TODO: monitor lambda RAM (Lambda listener?)
#TODO: separate framework from tests and configs
#TODO: separate configs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('load_test')


class LoadTest(object):
    """
    Class to trigger load test in multiple parallel threads
    thread = lambda execution
    """
    def __init__(self, config=None):
        self.aws_client = get_aws_client()
        t = Timings(runner_config=config)
        self.timings = t.get_test_timings()
        self.lambda_function_name = test_header['name']
        self.threads = list()
        self.lock = threading.Lock()
        self.test_stats = RequestStats()

    def start_generator(self, payload):
        """
        Function to start lambda load generator and append resulting stats
        :param payload: lambda invocation config
        :return:
        """
        logger.info(f'Starting generator with parameters:\n{payload}')
        lambda_response = self.start_lambda(payload)
        logger.info(f'Generator completed. Getting stats...')
        with self.lock:
            self.test_stats = extend_stats(stats_log=self.test_stats,
                                           stats_chunk=get_stats_from_response(lambda_response))
        logger.info(f'Stats appended. Quitting thread...')

    def start_lambda(self, payload, max_retries=3) -> response:
        """
        Function to invoke lambda with recursive retries
        :param payload: lambda invocation config
        :param max_retries:
        :return: botocore.response
        """
        if max_retries == 0:
            raise RuntimeError(f'Lambda invocation error. Max retries exceeded!')
        lambda_response = self.aws_client.invoke(FunctionName=self.lambda_function_name,
                                                 Payload=json.dumps(payload))
        if 'FunctionError' in lambda_response:
            logger.error(f'Error executing lambda: {lambda_response}')
            lambda_response = self.start_lambda(payload=payload,
                                                max_retries=max_retries-1)
        else:
            logger.info(f'Lambda execution finished: {lambda_response}.')
        return lambda_response

    def run_test(self):
        """
        Function to start threaded load test
        :return:
        """
        if not lambda_exists(client=self.aws_client,
                             name=self.lambda_function_name):
            raise ValueError(f'Cannot find {self.lambda_function_name} lambda. '
                             f'Check region settings or run \"aws\\prepare_lambda.py\" '
                             f'to create function first.')
        logger.info(f'Load test timings (start time, generator params):\n {self.timings}\n')
        for lambda_instance in self.timings:
            delay, payload = lambda_instance
            t = threading.Timer(interval=delay,
                                function=self.start_generator,
                                kwargs={'payload': payload})
            self.threads.append(t)
        for t in self.threads:
            t.start()
        for t in self.threads:
            t.join()
        logger.info(f'\nTest completed!\n')
        print_stats(self.test_stats)


if __name__ == '__main__':
    test = LoadTest(config=runner_config)
    test.run_test()


