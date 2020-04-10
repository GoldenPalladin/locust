import sys
import gevent
import signal
import logging
from typing import List
from gevent.pool import Group
from locust import events
from locust.runners import LocalLocustRunner
from locust.stats import print_stats, CONSOLE_STATS_INTERVAL_SEC
from framework.generator.debug import DebugRunner, get_healthcheck_info
from framework.settings import Settings
from framework.generator.listener import Listener

Listeners = List[Listener]
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def set_console_log_level(loglevel=logging.INFO):
    for name in ['launcher', 'debug', 'asserter', 'sfx', 'splunk']:
        lg = logging.getLogger(f'framework.{name}')
        lg.setLevel(loglevel)


class LoadTestLauncher(object):
    """
    Locust load test class maintaining the following functionality:
    - prepared settings to launch the test
    - listeners to emit stats
    - stats printer from Locust
    - debug mode to debug test scripts
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        gevent.signal(signal.SIGTERM, sig_term_handler)
        self.listeners: Listeners = settings.logging.listeners
        self.stats_printer, self.test_result_stats, self.api_versions = None, None, None
        self.listeners_group = Group()
        set_console_log_level(loglevel=settings.logging.loglevel)
        hyper_logger = logging.getLogger('hyperclient')
        hyper_logger.setLevel(settings.logging.hyper_log_level)

    def start_test(self):
        """
        method to start test as usual or execute every test file in main thread,
        not locust to make it possible to debug
        :return:
        """
        if self.settings.test.debug:
            test = DebugRunner(locust_classes=self.settings.test.classes)
            test.start_test()
        else:
            self.run()
            return self.test_result_stats

    def run(self):
        """
        main function to run the test
        :return:
        """
        global locust_runner
        self.set_test_stopper()
        try:
            logger.info(f'Instantiating test runner with settings {self.settings}')
            locust_runner = LocalLocustRunner(locust_classes=self.settings.test.classes,
                                              options=self.settings.runner)
            logger.info(f'Checking API versions...')
            self.api_versions = get_healthcheck_info(locust_classes=self.settings.test.classes)
            logger.info(f'API versions:\n{self.api_versions}')
            if self.listeners:
                logger.info(f'Spawning listeners...')
                self.spawn_listeners()
            self.stats_printer = gevent.spawn(stats_printer, locust_runner.stats)
            logger.info(f'Spawning clients...')
            self.spawn_clients()
            locust_runner.greenlet.join()
            logger.info(f'Locust completed {locust_runner.stats.num_requests} requests '
                        f'with {len(locust_runner.errors)} errors')
        except Exception as e:
            logger.exception(f'Test launch exception {repr(e)}')
        finally:
            events.quitting.fire()
            if self.stats_printer:
                self.stats_printer.kill(block=False)
            self.listeners_group.kill()
            self.test_result_stats = locust_runner.stats

    def spawn_clients(self):
        if self.settings.runner.step_load:
            logger.info(f'Starting step load: {self.settings.runner}')
            locust_runner.start_stepload(locust_count=self.settings.runner.num_clients,
                                         step_duration=self.settings.runner.step_duration,
                                         step_locust_count=self.settings.runner.step_clients,
                                         hatch_rate=self.settings.runner.hatch_rate)
        else:
            locust_runner.start_hatching(wait=True)

    def spawn_listeners(self):
        for listener in self.listeners:
            if hasattr(listener, 'start'):
                self.listeners_group.spawn(listener.start,
                                           locust_runner_reference=locust_runner,
                                           final_stats=self.settings.logging.final_stats,
                                           additional_dimensions=self.api_versions)
            else:
                logger.error(f'Start method not implemented in {listener} listener')

    def set_test_stopper(self):
        """
        Method to parse run-time option and spawn gevent test stopper
        :return:
        """
        test_time_limit = self.settings.runner.stop_timeout
        logger.info(f'Run time limit set to {test_time_limit} seconds')

        def stop_test():
            logger.info(f'Run time limit reached: {test_time_limit} seconds')
            if locust_runner.stepload_greenlet:
                locust_runner.stepload_greenlet.kill(block=True)
            locust_runner.quit()
# TODO: test stopper is failing with step-load turned on, test don't stop.
        #  need to investigate
        gevent.spawn_later(test_time_limit, stop_test)


def sig_term_handler(signum, frame):
    logger.info("Received sigterm, exiting")
    sys.exit(0)


def stats_printer(stats):
    """
    gevent Locust console stats printer
    :param stats:
    :return:
    """
    while True:
        print_stats(stats)
        gevent.sleep(CONSOLE_STATS_INTERVAL_SEC)

